import os
import json
import time
from datetime import datetime

# Importer le module de chiffrement AES256 que nous avons créé
try:
    from modules.aes256 import AES256Cipher
except ImportError:
    print("[CRITICAL] [Logger] Le module AES256Cipher n'a pas pu être importé. Les logs NE SERONT PAS CHIFFRÉS.")
    AES256Cipher = None # Désactiver le chiffrement si le module est absent
except ValueError as e:
    print(f"[CRITICAL] [Logger] Erreur lors de l'initialisation de AES256Cipher: {e}. Les logs NE SERONT PAS CHIFFRÉS.")
    AES256Cipher = None

class Logger:
    """
    Module de journalisation furtif qui écrit les logs dans un fichier chiffré localement.
    Prend en charge différents niveaux de journalisation.
    """

    # Niveaux de journalisation (compatibles avec le module logging standard)
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

    LEVEL_NAMES = {
        DEBUG: "DEBUG",
        INFO: "INFO",
        WARNING: "WARNING",
        ERROR: "ERROR",
        CRITICAL: "CRITICAL"
    }

    # Taille maximale du fichier de log avant rotation (en bytes)
    MAX_LOG_SIZE = 1 * 1024 * 1024 # 1 MB
    # Nombre de fichiers de log de rotation à conserver
    BACKUP_COUNT = 1

    def __init__(self, log_file_path: str, cipher_key: str, debug_mode: bool = False):
        """
        Initialise le logger.

        :param log_file_path: Chemin complet du fichier de journalisation.
        :param cipher_key: Clé AES pour le chiffrement/déchiffrement des logs.
        :param debug_mode: Si True, les logs DEBUG sont affichés.
        """
        self.log_file_path = log_file_path
        self.debug_mode = debug_mode
        self.cipher = None
        if AES256Cipher and cipher_key:
            try:
                self.cipher = AES256Cipher(cipher_key)
            except Exception as e:
                print(f"[CRITICAL] [Logger] Erreur à l'initialisation du chiffreur ({e}). Les logs NE SERONT PAS CHIFFRÉS.")
        
        if not self.cipher:
            print(f"[WARNING] [Logger] Chiffrement des logs désactivé. Le fichier '{log_file_path}' sera en clair.")
        
        self._ensure_log_directory_exists()
        self._log_initial_message()


    def _ensure_log_directory_exists(self):
        """S'assure que le répertoire du fichier de log existe."""
        log_dir = os.path.dirname(self.log_file_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except Exception as e:
                print(f"[CRITICAL] [Logger] Impossible de créer le répertoire de logs '{log_dir}': {e}. Les logs ne seront pas enregistrés sur le disque.")
                self.log_file_path = None # Désactiver l'écriture sur disque

    def _log_initial_message(self):
        """Écrit un message initial au démarrage du logger."""
        self._write_log(self.INFO, "Logger initialisé. Chiffrement des logs: " + ("Activé" if self.cipher else "Désactivé"))
        if self.debug_mode:
            self._write_log(self.DEBUG, "Mode DEBUG activé pour le logger.")

    def _format_message(self, level: int, message: str) -> bytes:
        """Formate le message de log avec timestamp, niveau et contenu."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        level_name = self.LEVEL_NAMES.get(level, "UNKNOWN")
        log_entry = {
            "timestamp": timestamp,
            "level": level_name,
            "message": message
        }
        # Retourne les bytes pour le chiffrement
        return (json.dumps(log_entry) + "\n").encode('utf-8')

    def _write_log(self, level: int, message: str):
        """
        Écrit le message de log au fichier, avec chiffrement si activé.
        Gère la rotation des logs.
        """
        if not self.log_file_path:
            return # Ne rien faire si le chemin de log n'est pas valide
            
        if not self.debug_mode and level == self.DEBUG:
            return # Ne pas logguer les DEBUG si le mode debug n'est pas actif

        # Vérifier la taille du fichier et effectuer la rotation si nécessaire
        try:
            if os.path.exists(self.log_file_path) and os.path.getsize(self.log_file_path) >= self.MAX_LOG_SIZE:
                self._rotate_logs()
        except Exception as e:
            print(f"[ERROR] [Logger] Erreur lors de la vérification/rotation des logs: {e}")

        # Formater et chiffrer le message
        formatted_message_bytes = self._format_message(level, message)
        
        data_to_write = formatted_message_bytes
        if self.cipher:
            try:
                data_to_write = self.cipher.encrypt(formatted_message_bytes) + b'\n' # Ajouter un saut de ligne après le bloc chiffré
                                                                                   # pour faciliter la lecture/découpage
            except Exception as e:
                print(f"[ERROR] [Logger] Échec du chiffrement du log: {e}. Écriture en clair.")
                data_to_write = formatted_message_bytes # Écrire en clair si le chiffrement échoue

        try:
            # Ouvrir en mode append binaire
            with open(self.log_file_path, 'ab') as f:
                f.write(data_to_write)
        except Exception as e:
            print(f"[CRITICAL] [Logger] Impossible d'écrire dans le fichier de logs '{self.log_file_path}': {e}")

    def _rotate_logs(self):
        """Gère la rotation des fichiers de log."""
        self._write_log(self.INFO, "Rotation du fichier de log...") # Log avant rotation
        
        # Supprimer le plus ancien fichier de backup
        if os.path.exists(f"{self.log_file_path}.{self.BACKUP_COUNT}"):
            try:
                os.remove(f"{self.log_file_path}.{self.BACKUP_COUNT}")
            except Exception as e:
                print(f"[ERROR] [Logger] Impossible de supprimer le fichier de log de backup: {e}")

        # Renommer les fichiers existants
        for i in range(self.BACKUP_COUNT - 1, -1, -1):
            src = f"{self.log_file_path}" if i == 0 else f"{self.log_file_path}.{i}"
            dst = f"{self.log_file_path}.{i+1}"
            if os.path.exists(src):
                try:
                    os.rename(src, dst)
                except Exception as e:
                    print(f"[ERROR] [Logger] Impossible de renommer '{src}' en '{dst}': {e}")
        
        # Le fichier actuel est maintenant vide (renommé en .1), il sera créé au prochain log.
        self._write_log(self.INFO, "Rotation des logs terminée.") # Log après rotation

    # Méthodes publiques pour chaque niveau de log
    def log_debug(self, message: str):
        self._write_log(self.DEBUG, message)

    def log_info(self, message: str):
        self._write_log(self.INFO, message)

    def log_warning(self, message: str):
        self._write_log(self.WARNING, message)

    def log_error(self, message: str):
        self._write_log(self.ERROR, message)

    def log_critical(self, message: str):
        self._write_log(self.CRITICAL, message)

    def read_and_decrypt_logs(self) -> list:
        """
        Lit le fichier de log (et ses backups), déchiffre le contenu et le retourne.
        Utile pour l'analyse post-mortem côté attaquant.
        """
        if not self.cipher:
            print("[WARNING] [Logger] Impossible de lire et déchiffrer les logs: Chiffreur non disponible. Lecture en clair si possible.")

        decrypted_entries = []
        log_files_to_read = [self.log_file_path]
        for i in range(1, self.BACKUP_COUNT + 1):
            if os.path.exists(f"{self.log_file_path}.{i}"):
                log_files_to_read.append(f"{self.log_file_path}.{i}")

        for f_path in log_files_to_read:
            if not os.path.exists(f_path):
                continue
            
            try:
                with open(f_path, 'rb') as f:
                    content = f.read()
                
                # Les logs sont des blocs chiffrés séparés par des '\n' si chiffrement activé.
                # Sinon, ce sont des lignes JSON.
                if self.cipher:
                    # Diviser le contenu en blocs chiffrés (chaque bloc se termine par '\n')
                    encrypted_blocks = content.split(b'\n')
                    for block in encrypted_blocks:
                        if not block.strip():
                            continue # Ignorer les lignes vides
                        try:
                            decrypted_block = self.cipher.decrypt(block)
                            entry = json.loads(decrypted_block.decode('utf-8'))
                            decrypted_entries.append(entry)
                        except (ValueError, json.JSONDecodeError, TypeError) as e:
                            print(f"[ERROR] [Logger] Erreur lors du déchiffrement ou parsing d'un bloc de log dans '{f_path}': {e}. Bloc: {block[:50]}...")
                else:
                    # Si pas de chiffreur, lire comme du texte JSON ligne par ligne
                    for line in content.decode('utf-8', errors='ignore').splitlines():
                        if not line.strip(): continue
                        try:
                            entry = json.loads(line)
                            decrypted_entries.append(entry)
                        except json.JSONDecodeError as e:
                            print(f"[ERROR] [Logger] Erreur lors du parsing d'une ligne de log en clair dans '{f_path}': {e}. Ligne: {line[:50]}...")

            except FileNotFoundError:
                pass # Déjà vérifié plus haut, mais au cas où
            except Exception as e:
                print(f"[ERROR] [Logger] Erreur inattendue lors de la lecture de '{f_path}': {e}")
        
        return decrypted_entries


# --- Partie de test (à exécuter si le fichier est lancé directement) ---
if __name__ == "__main__":
    print("[+] Test du module Logger...")

    # Mock de AES256Cipher pour les tests
    class MockAES256Cipher:
        def __init__(self, key): 
            self.key = key.encode('utf-8')
            if len(self.key) not in [16, 24, 32]:
                raise ValueError("Clé de test AES incorrecte.")
        def encrypt(self, data): 
            return b"ENC_" + base64.b64encode(data) + b"_END"
        def decrypt(self, data):
            if data.startswith(b"ENC_") and data.endswith(b"_END"):
                return base64.b64decode(data[len(b"ENC_"):-len(b"_END")])
            raise ValueError("Données chiffrées malformées de test.")

    # Créer un répertoire de test pour les logs
    test_log_dir = "./test_logs"
    os.makedirs(test_log_dir, exist_ok=True)
    test_log_file = os.path.join(test_log_dir, "test_agent_logs.enc")
    test_cipher_key = "test_key_for_log_aes" # 20 bytes, sera haché en 32 par MockAES256Cipher
    
    # Nettoyer les anciens fichiers de test
    if os.path.exists(test_log_file):
        os.remove(test_log_file)
    for i in range(1, Logger.BACKUP_COUNT + 2): # Nettoyer les backups possibles aussi
        if os.path.exists(f"{test_log_file}.{i}"):
            os.remove(f"{test_log_file}.{i}")

    # Test 1: Logger en mode debug
    print("\n--- Test 1: Logger en mode DEBUG ---")
    logger_debug = Logger(test_log_file, test_cipher_key, debug_mode=True)
    logger_debug.log_debug("Ceci est un message de debug.")
    logger_debug.log_info("Ceci est un message d'info.")
    logger_debug.log_warning("Ceci est un message d'avertissement.")
    logger_debug.log_error("Ceci est un message d'erreur critique.")
    logger_debug.log_critical("Ceci est un message critique.")
    
    time.sleep(0.1) # Laisser le temps d'écrire
    
    # Lire et déchiffrer les logs
    read_logs_debug = logger_debug.read_and_decrypt_logs()
    print(f"[*] Logs lus ({len(read_logs_debug)} entrées):")
    for entry in read_logs_debug:
        print(entry)
    assert len(read_logs_debug) == 5, "Le nombre de logs lus en mode debug est incorrect."
    assert any(e['level'] == 'DEBUG' for e in read_logs_debug), "Le log DEBUG n'a pas été enregistré en mode debug."


    # Test 2: Logger en mode non debug (pas de logs DEBUG)
    print("\n--- Test 2: Logger en mode normal (pas de DEBUG) ---")
    # Supprimer les anciens logs pour ce test
    if os.path.exists(test_log_file): os.remove(test_log_file)
    logger_normal = Logger(test_log_file, test_cipher_key, debug_mode=False)
    logger_normal.log_debug("Ceci est un message de debug qui ne devrait PAS apparaître.")
    logger_normal.log_info("Ceci est un message d'info en mode normal.")
    
    time.sleep(0.1)
    read_logs_normal = logger_normal.read_and_decrypt_logs()
    print(f"[*] Logs lus ({len(read_logs_normal)} entrées):")
    for entry in read_logs_normal:
        print(entry)
    assert len(read_logs_normal) == 2, "Le nombre de logs lus en mode normal est incorrect (devrait exclure DEBUG)."
    assert not any(e['level'] == 'DEBUG' for e in read_logs_normal), "Le log DEBUG a été enregistré en mode normal."


    # Test 3: Rotation des logs
    print("\n--- Test 3: Rotation des logs ---")
    if os.path.exists(test_log_file): os.remove(test_log_file)
    for i in range(1, Logger.BACKUP_COUNT + 2):
        if os.path.exists(f"{test_log_file}.{i}"):
            os.remove(f"{test_log_file}.{i}")

    logger_rotate = Logger(test_log_file, test_cipher_key, debug_mode=True)
    # Remplir le log jusqu'à la rotation
    num_entries_to_fill = int(Logger.MAX_LOG_SIZE / len(logger_rotate._format_message(Logger.INFO, "a")) * 1.5) # Écrire plus que la taille max
    print(f"[*] Écriture de ~{num_entries_to_fill} messages pour forcer la rotation (taille max: {Logger.MAX_LOG_SIZE / 1024 / 1024:.2f} MB)...")
    for i in range(num_entries_to_fill):
        logger_rotate.log_info(f"Message de test pour la rotation {i}")
    
    time.sleep(0.5) # Laisser le temps à la rotation
    
    print(f"[*] Vérification des fichiers de log après rotation:")
    assert not os.path.exists(f"{test_log_file}.{Logger.BACKUP_COUNT + 1}"), "Trop de fichiers de backup."
    assert os.path.exists(f"{test_log_file}.1"), "Le fichier de log n'a pas été renommé en .1"
    
    # Écrire un nouveau log après rotation
    logger_rotate.log_critical("Ceci est un log après la rotation.")
    time.sleep(0.1)

    read_logs_rotated = logger_rotate.read_and_decrypt_logs()
    print(f"[*] Nombre total de logs lus après rotation: {len(read_logs_rotated)}")
    assert "Ceci est un log après la rotation." in [e['message'] for e in read_logs_rotated], "Le log après rotation n'est pas présent."


    # Test 4: Chiffrement désactivé (pas de clé ou erreur chiffreur)
    print("\n--- Test 4: Chiffrement des logs désactivé ---")
    if os.path.exists(test_log_file): os.remove(test_log_file)
    # Passage d'une clé vide pour désactiver le chiffrement
    logger_no_cipher = Logger(test_log_file, "", debug_mode=True) 
    logger_no_cipher.log_info("Ceci est un log en clair.")
    time.sleep(0.1)
    
    with open(test_log_file, 'rb') as f:
        content_no_cipher = f.read().decode('utf-8', errors='ignore')
    print(f"[*] Contenu du fichier de log (en clair): \n{content_no_cipher}")
    assert "Ceci est un log en clair." in content_no_cipher, "Le log en clair n'est pas présent."
    assert not content_no_cipher.startswith("ENC_"), "Le log semble chiffré alors qu'il ne devrait pas l'être."

    # Nettoyage final
    if os.path.exists(test_log_dir):
        shutil.rmtree(test_log_dir)
        print(f"\n[+] Répertoire de test '{test_log_dir}' supprimé.")

    print("\n[+] Tests du module Logger terminés.")
