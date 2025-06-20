import os
import fnmatch
import hashlib
import re # Pour le filtrage de contenu

class FileScanner:
    """
    Recherche récursivement des fichiers en fonction de critères spécifiés
    et applique des filtres (extension, taille, contenu).
    """

    def __init__(self,
                 scan_path: str,
                 include_types: list = None,
                 exclude_types: list = None,
                 min_size: int = 0,
                 max_size: int = float('inf'), # Infini par défaut
                 keywords: list = None,
                 regex_patterns: list = None,
                 logger=None): # Un objet logger sera passé ici
        """
        Initialise le scanner de fichiers avec les critères de recherche.

        :param scan_path: Chemin du répertoire à scanner.
        :param include_types: Liste des extensions de fichiers à inclure (ex: ['.doc', '.txt']).
                              Si vide ou None, tous les types sont inclus (sauf ceux exclus).
        :param exclude_types: Liste des extensions de fichiers à exclure (ex: ['.exe', '.dll']).
        :param min_size: Taille minimale du fichier en bytes.
        :param max_size: Taille maximale du fichier en bytes.
        :param keywords: Liste de mots-clés à rechercher dans le contenu des fichiers.
        :param regex_patterns: Liste de motifs regex à rechercher dans le contenu des fichiers.
        :param logger: Instance du logger pour la journalisation.
        """
        self.scan_path = scan_path
        self.include_types = [t.lower() for t in include_types] if include_types else []
        self.exclude_types = [t.lower() for t in exclude_types] if exclude_types else []
        self.min_size = min_size
        self.max_size = max_size
        self.keywords = [k.lower() for k in keywords] if keywords else []
        self.regex_patterns = regex_patterns if regex_patterns else []
        self.logger = logger
        self.found_files = []

        if self.logger:
            self.logger.log_debug(f"FileScanner initialisé: scan_path='{self.scan_path}', "
                                  f"include_types={self.include_types}, exclude_types={self.exclude_types}, "
                                  f"min_size={self.min_size}, max_size={self.max_size}, "
                                  f"keywords={self.keywords}, regex_patterns={self.regex_patterns}")

    def _log(self, level, message):
        """Helper pour logguer si un logger est disponible."""
        if self.logger:
            getattr(self.logger, f"log_{level}")(f"[FileScanner] {message}")
        else:
            print(f"[{level.upper()}] [FileScanner] {message}")

    def _is_file_whitelisted(self, filename: str) -> bool:
        """
        Vérifie si l'extension du fichier est dans la liste des types à inclure.
        Si la liste d'inclusion est vide, tous les types sont considérés comme autorisés
        (avant de vérifier la liste d'exclusion).
        """
        if not self.include_types: # Si aucune inclusion spécifiée, tout est whitelisté par défaut
            return True
        
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in self.include_types

    def _is_file_blacklisted(self, filename: str) -> bool:
        """
        Vérifie si l'extension du fichier est dans la liste des types à exclure.
        """
        file_extension = os.path.splitext(filename)[1].lower()
        return file_extension in self.exclude_types

    def _is_size_valid(self, filepath: str) -> bool:
        """
        Vérifie si la taille du fichier est dans les limites spécifiées.
        """
        try:
            file_size = os.path.getsize(filepath)
            return self.min_size <= file_size <= self.max_size
        except OSError as e:
            self._log("warning", f"Impossible d'obtenir la taille de '{filepath}': {e}")
            return False

    def _filter_content(self, filepath: str) -> bool:
        """
        Filtrage avancé par contenu (mots-clés et expressions régulières).
        Retourne True si le fichier correspond aux critères de contenu, False sinon.
        """
        if not self.keywords and not self.regex_patterns:
            return True # Pas de filtrage de contenu si aucun critère n'est donné

        try:
            # Lire les premiers 2MB du fichier pour un scan rapide de contenu
            # Ne pas charger des fichiers entiers très volumineux en mémoire
            with open(filepath, 'r', errors='ignore') as f: 
                content = f.read(2 * 1024 * 1024) # Lire les premiers 2MB
                
                # Filtrage par mots-clés
                if self.keywords:
                    for keyword in self.keywords:
                        if keyword in content.lower(): # Recherche insensible à la casse
                            self._log("debug", f"Contenu de '{filepath}' correspond au mot-clé '{keyword}'.")
                            return True

                # Filtrage par expressions régulières
                if self.regex_patterns:
                    for pattern_str in self.regex_patterns:
                        try:
                            pattern = re.compile(pattern_str, re.IGNORECASE)
                            if pattern.search(content):
                                self._log("debug", f"Contenu de '{filepath}' correspond au motif regex '{pattern_str}'.")
                                return True
                        except re.error as re_e:
                            self._log("error", f"Regex invalide '{pattern_str}': {re_e}")
                            continue # Continuer avec les autres motifs
            return False # Aucun critère de contenu correspondant
        except Exception as e:
            self._log("warning", f"Erreur lors du filtrage de contenu de '{filepath}': {e}")
            return False

    def scan(self) -> list:
        """
        Lance le scan récursif du répertoire spécifié et retourne la liste des chemins de fichiers.
        """
        self.found_files = [] # Réinitialiser la liste pour un nouveau scan
        self._log("info", f"Début du scan de fichiers dans '{self.scan_path}'...")
        
        # Vérifier si le chemin de scan existe
        if not os.path.exists(self.scan_path):
            self._log("error", f"Le chemin de scan spécifié n'existe pas: '{self.scan_path}'")
            return []
        if not os.path.isdir(self.scan_path):
            self._log("error", f"Le chemin de scan spécifié n'est pas un répertoire: '{self.scan_path}'")
            return []

        for root, _, files in os.walk(self.scan_path):
            for filename in files:
                filepath = os.path.join(root, filename)
                
                # Vérifier les permissions d'accès au fichier
                if not os.access(filepath, os.R_OK):
                    self._log("debug", f"Accès non autorisé au fichier '{filepath}', ignoré.")
                    continue

                if self._is_file_blacklisted(filename):
                    self._log("debug", f"Fichier '{filename}' exclu par type (blacklist).")
                    continue
                
                if not self._is_file_whitelisted(filename):
                    self._log("debug", f"Fichier '{filename}' non inclus par type (whitelist).")
                    continue

                if not self._is_size_valid(filepath):
                    self._log("debug", f"Fichier '{filename}' exclu par taille.")
                    continue
                
                # Filtrage de contenu, seulement si des critères sont définis
                if (self.keywords or self.regex_patterns) and not self._filter_content(filepath):
                    self._log("debug", f"Fichier '{filename}' exclu par contenu.")
                    continue

                self.found_files.append(filepath)
                self._log("debug", f"Fichier trouvé et inclus: '{filepath}'")
        
        self._log("info", f"Scan terminé. {len(self.found_files)} fichiers trouvés.")
        return self.found_files

# --- Partie de test (à exécuter si le fichier est lancé directement) ---
if __name__ == "__main__":
    print("[+] Test du module FileScanner...")

    class MockLogger:
        def log_info(self, msg): print(f"[INFO] {msg}")
        def log_warning(self, msg): print(f"[WARN] {msg}")
        def log_error(self, msg): print(f"[ERROR] {msg}")
        def log_debug(self, msg): print(f"[DEBUG] {msg}")

    # Création de quelques fichiers et répertoires de test
    test_dir = "./test_scan_dir"
    if os.path.exists(test_dir):
        import shutil
        shutil.rmtree(test_dir) # Nettoyer avant de commencer
    os.makedirs(f"{test_dir}/sub_dir1", exist_ok=True)
    os.makedirs(f"{test_dir}/sub_dir2", exist_ok=True)

    # Fichiers à inclure
    with open(f"{test_dir}/doc_important.docx", "w") as f: f.write("contenu confidentiel docx 12345")
    with open(f"{test_dir}/rapport.txt", "w") as f: f.write("Données sensibles à exfiltrer 12345")
    with open(f"{test_dir}/sub_dir1/credentials.db", "w") as f: f.write("user:pass db")
    with open(f"{test_dir}/sub_dir2/notes.txt", "w") as f: f.write("autres notes importantes")
    
    # Fichiers à exclure par type ou taille
    with open(f"{test_dir}/programme.exe", "w") as f: f.write("binary content")
    with open(f"{test_dir}/temp.tmp", "w") as f: f.write("temporary file")
    with open(f"{test_dir}/petit.txt", "w") as f: f.write("a") # Très petit fichier
    with open(f"{test_dir}/grand_fichier.log", "w") as f: f.write("a" * (2 * 1024 * 1024)) # 2MB

    logger = MockLogger()

    # Test 1: Scan de base avec inclusion et exclusion et taille
    print("\n--- Test 1: Scan de base avec inclusion, exclusion et taille ---")
    scanner1 = FileScanner(
        scan_path=test_dir,
        include_types=[".txt", ".docx", ".db"],
        exclude_types=[".tmp"],
        min_size=10, # Pour exclure "petit.txt"
        max_size=1 * 1024 * 1024, # Pour exclure "grand_fichier.log"
        logger=logger
    )
    files1 = scanner1.scan()
    print(f"[*] Fichiers trouvés (Test 1):")
    for f in files1:
        print(f"  - {f}")
    assert len(files1) == 4, f"Test 1 échoué: Attendu 4 fichiers, trouvé {len(files1)}" # .docx, .txt, .db, notes.txt

    print("\n--- Test 2: Scan avec filtrage de contenu (mots-clés) ---")
    scanner2 = FileScanner(
        scan_path=test_dir,
        include_types=[".txt", ".docx", ".db"], # Inclure .db aussi
        min_size=1,
        max_size=float('inf'),
        keywords=["confidentiel", "sensibles", "user:pass"], # Ajout de user:pass
        logger=logger
    )
    files2 = scanner2.scan()
    print(f"[*] Fichiers trouvés (Test 2 - mots-clés):")
    for f in files2:
        print(f"  - {f}")
    assert len(files2) == 3, f"Test 2 échoué: Attendu 3 fichiers, trouvé {len(files2)}" # doc_important.docx, rapport.txt, credentials.db


    print("\n--- Test 3: Scan avec filtrage de contenu (regex) ---")
    scanner3 = FileScanner(
        scan_path=test_dir,
        include_types=[".txt", ".db", ".docx"],
        min_size=1,
        max_size=float('inf'),
        regex_patterns=[r'\d{5}', r'user:pass'], # 5 chiffres, ou "user:pass"
        logger=logger
    )
    files3 = scanner3.scan()
    print(f"[*] Fichiers trouvés (Test 3 - regex):")
    for f in files3:
        print(f"  - {f}")
    assert len(files3) == 3, f"Test 3 échoué: Attendu 3 fichiers, trouvé {len(files3)}" # doc_important.docx, rapport.txt, credentials.db

    print("\n--- Test 4: Chemin inexistant ---")
    scanner4 = FileScanner(scan_path="./non_existent_dir", logger=logger)
    files4 = scanner4.scan()
    assert len(files4) == 0, f"Test 4 échoué: Attendu 0 fichiers, trouvé {len(files4)}"

    # Nettoyage des fichiers de test
    import shutil
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"\n[+] Répertoire de test '{test_dir}' supprimé.")

    print("\n[+] Tests du module FileScanner terminés.")
