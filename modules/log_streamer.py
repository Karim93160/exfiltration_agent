# modules/log_streamer.py
import sys
from datetime import datetime
import threading

class LogStreamer:
    """
    Redirige sys.stdout et sys.stderr vers un buffer en mémoire,
    permettant de capturer toutes les sorties du programme.
    """
    def __init__(self, max_buffer_lines: int = 1000):
        self._buffer = []
        self._lock = threading.Lock() # Pour la sécurité des threads
        self.max_buffer_lines = max_buffer_lines
        self.original_stdout = None
        self.original_stderr = None

    def write(self, message: str):
        """Méthode appelée quand quelque chose est écrit dans le flux."""
        if message.strip(): # Ignorer les lignes vides
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Ajoute un préfixe pour identifier l'origine (si besoin), ici on garde le message tel quel
            # ou on peut le formater si désiré, ex: f"[{timestamp}] {message.strip()}"
            formatted_message = message.strip()
            
            with self._lock:
                self._buffer.append(formatted_message)
                if len(self._buffer) > self.max_buffer_lines:
                    self._buffer.pop(0) # Supprime la plus ancienne ligne

    def flush(self):
        """Méthode de flush (requise pour les flux sys.stdout/stderr)."""
        pass # Nous ne faisons rien ici car le buffer est en mémoire

    def start_capturing(self):
        """Commence la redirection de sys.stdout et sys.stderr."""
        if self.original_stdout is None:
            self.original_stdout = sys.stdout
            sys.stdout = self
        if self.original_stderr is None:
            self.original_stderr = sys.stderr
            sys.stderr = self
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [LogStreamer] Capture des sorties standard activée.")


    def stop_capturing(self):
        """Arrête la redirection et restaure les flux originaux."""
        if self.original_stdout is not None:
            sys.stdout = self.original_stdout
            self.original_stdout = None
        if self.original_stderr is not None:
            sys.stderr = self.original_stderr
            self.original_stderr = None
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [LogStreamer] Capture des sorties standard désactivée.")

    def get_logs(self, last_index: int = 0) -> tuple[list[str], int]:
        """Retourne les nouveaux logs et l'index total actuel."""
        with self._lock:
            new_logs = self._buffer[last_index:]
            return new_logs, len(self._buffer)

    def clear_logs(self):
        """Vide le buffer de logs."""
        with self._lock:
            self._buffer.clear()
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [LogStreamer] Buffer de logs vidé.")

# Pour les tests autonomes du module log_streamer
if __name__ == "__main__":
    log_streamer = LogStreamer(max_buffer_lines=5)
    log_streamer.start_capturing()

    print("Ceci est un test de log normal.")
    sys.stderr.write("Ceci est un message d'erreur sur stderr.\n")
    print("Un autre message.")
    time.sleep(0.1) # Laisser un peu de temps pour que les écritures se fassent

    new_logs, current_total = log_streamer.get_logs(0)
    print("\n--- Logs capturés (premier appel) ---")
    for log in new_logs:
        print(f"Captured: {log}")
    print(f"Total lines: {current_total}")

    print("\nSimulating more logs...")
    print("Log 1")
    print("Log 2")
    print("Log 3") # Ceci devrait faire déborder le buffer de 5, supprimant le premier log

    time.sleep(0.1)
    more_logs, new_total = log_streamer.get_logs(current_total)
    print("\n--- Nouveaux logs capturés ---")
    for log in more_logs:
        print(f"New Captured: {log}")
    print(f"New Total lines: {new_total}")

    # Vérifier le contenu total après dépassement du buffer
    all_current_logs, _ = log_streamer.get_logs(0)
    print("\n--- Contenu complet du buffer après dépassement (devrait être les 5 derniers logs) ---")
    for log in all_current_logs:
        print(f"Final Buffer: {log}")
    assert len(all_current_logs) == 5, "Le buffer n'a pas géré la taille maximale correctement."

    log_streamer.clear_logs()
    cleared_logs, cleared_total = log_streamer.get_logs(0)
    print(f"\nBuffer après nettoyage : {len(cleared_logs)} lignes, total {cleared_total}")
    assert len(cleared_logs) == 0, "Le buffer n'a pas été vidé correctement."

    log_streamer.stop_capturing()
    print("\n--- Test terminé ---")
    print("Ce message ne devrait pas apparaître dans le buffer du LogStreamer.")


