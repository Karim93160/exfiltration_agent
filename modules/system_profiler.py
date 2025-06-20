import platform
import os
import socket
import json
import time
import subprocess # Nouveau: pour exécuter des commandes système
import re # Pour le parsing de sortie de commandes

class SystemProfiler:
    """
    Collecte des informations détaillées sur le système d'exploitation, le réseau,
    le matériel et les utilisateurs actifs, en utilisant des modules Python standards
    et des commandes système.
    """

    def __init__(self, logger=None):
        self.logger = logger
        if self.logger:
            self.logger.log_debug("[SystemProfiler] Initialisé (sans psutil).")

    def _log(self, level, message):
        if self.logger:
            getattr(self.logger, f"log_{level}")(f"[SystemProfiler] {message}")
        else:
            print(f"[{level.upper()}] [SystemProfiler] {message}")

    def _run_command(self, command: list, timeout: int = 5) -> str:
        """Exécute une commande shell et retourne sa sortie standard."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            self._log("warning", f"Commande '{' '.join(command)}' a retourné une erreur: {e.stderr.strip()}")
            return ""
        except subprocess.TimeoutExpired:
            self._log("warning", f"Commande '{' '.join(command)}' a dépassé le délai.")
            return ""
        except FileNotFoundError:
            self._log("warning", f"Commande '{command[0]}' non trouvée.")
            return ""
        except Exception as e:
            self._log("error", f"Erreur inattendue lors de l'exécution de commande '{' '.join(command)}': {e}")
            return ""

    def _get_hostname(self) -> str:
        try:
            hostname = socket.gethostname()
            self._log("debug", f"Hostname: {hostname}")
            return hostname
        except Exception as e:
            self._log("error", f"Erreur lors de la récupération du hostname: {e}")
            return "N/A"

    def _get_os_info(self) -> dict:
        os_info = {
            "system": platform.system(),
            "node_name": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "platform": platform.platform(),
        }
        if os_info["system"] == "Linux":
            try:
                # Sur Termux, /etc/os-release peut exister.
                # Alternative: lsb_release -a si le paquet est installé (pkg install lsb-release)
                os_release_content = self._run_command(["cat", "/etc/os-release"])
                if os_release_content:
                    for line in os_release_content.splitlines():
                        if line.startswith("PRETTY_NAME="):
                            os_info["pretty_name"] = line.strip().split('=')[1].strip('"')
                            break
            except Exception:
                pass # Ignorer si le fichier n'existe pas ou ne peut pas être lu
        self._log("debug", f"OS Info: {os_info}")
        return os_info

    def _get_cpu_info(self) -> dict:
        cpu_info = {}
        try:
            # Sur Linux/Termux, lire /proc/cpuinfo
            cpuinfo_content = self._run_command(["cat", "/proc/cpuinfo"])
            if cpuinfo_content:
                cores = 0
                model_name = ""
                for line in cpuinfo_content.splitlines():
                    if "processor" in line:
                        cores += 1
                    if "model name" in line:
                        if not model_name: # Prendre le premier modèle name
                            model_name = line.split(":", 1)[1].strip()
                cpu_info["logical_cores"] = cores
                cpu_info["model_name"] = model_name
            
            # psutil.cpu_percent n'est pas facilement remplaçable par une commande simple sans période d'échantillonnage.
            # On laisse cette info vide ou à N/A pour l'instant.
            cpu_info["total_cpu_percent"] = "N/A" # Plus difficile sans psutil ou des outils comme 'top' avec parsing.

        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des infos CPU: {e}")
        self._log("debug", f"CPU Info: {cpu_info}")
        return cpu_info

    def _get_memory_info(self) -> dict:
        mem_info = {}
        try:
            # Sur Linux/Termux, lire /proc/meminfo
            meminfo_content = self._run_command(["cat", "/proc/meminfo"])
            if meminfo_content:
                total_mem_kb = 0
                free_mem_kb = 0
                for line in meminfo_content.splitlines():
                    if "MemTotal:" in line:
                        total_mem_kb = int(line.split(":")[1].strip().split(" ")[0])
                    elif "MemAvailable:" in line: # Ou MemFree si MemAvailable n'est pas dispo
                        free_mem_kb = int(line.split(":")[1].strip().split(" ")[0])
                
                if total_mem_kb > 0:
                    mem_info["total_gb"] = round(total_mem_kb / (1024**2), 2)
                    mem_info["free_gb"] = round(free_mem_kb / (1024**2), 2)
                    mem_info["percent_used"] = round(((total_mem_kb - free_mem_kb) / total_mem_kb) * 100, 2)
                else:
                     mem_info = {"total_gb": "N/A", "free_gb": "N/A", "percent_used": "N/A"}

        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des infos mémoire: {e}")
        self._log("debug", f"Memory Info: {mem_info}")
        return mem_info

    def _get_disk_info(self) -> list:
        partitions_info = []
        try:
            # Utiliser la commande 'df -h' pour une sortie lisible par humain, puis parser
            # Ou 'df -kP' pour une sortie en kilobytes, plus facile à parser numériquement
            df_output = self._run_command(["df", "-kP"]) # -k pour KB, -P pour format POSIX (facilite le parsing)
            
            lines = df_output.splitlines()
            if len(lines) > 1: # Skip header
                for line in lines[1:]:
                    parts = line.split()
                    if len(parts) >= 6:
                        try:
                            device = parts[0]
                            total_kb = int(parts[1])
                            used_kb = int(parts[2])
                            available_kb = int(parts[3])
                            percent_used = parts[4].replace('%', '')
                            mountpoint = parts[5]

                            partitions_info.append({
                                "device": device,
                                "mountpoint": mountpoint,
                                "total_gb": round(total_kb / (1024**2), 2),
                                "used_gb": round(used_kb / (1024**2), 2),
                                "free_gb": round(available_kb / (1024**2), 2),
                                "percent_used": float(percent_used),
                            })
                        except ValueError as ve:
                            self._log("warning", f"Impossible de parser la ligne df: {line} - {ve}")
                        except IndexError as ie:
                            self._log("warning", f"Format de ligne df inattendu: {line} - {ie}")

        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des infos disque: {e}")
        self._log("debug", f"Disk Info: {partitions_info}")
        return partitions_info

    def _get_network_info(self) -> dict:
        net_info = {
            "interfaces": {},
            "default_gateway": "N/A", # Plus complexe sans parsing avancé de la table de routage
            "dns_servers": []
        }
        try:
            # Utiliser 'ip addr show' ou 'ifconfig' (ifconfig est plus simple mais moins standard)
            # Sur Termux, 'ip' est généralement disponible.
            ip_output = self._run_command(["ip", "addr", "show"])
            
            current_interface = None
            for line in ip_output.splitlines():
                if re.match(r'^\d+:', line): # Ligne d'interface (ex: 1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000)
                    match = re.match(r'^\d+: ([^:]+):.*', line)
                    if match:
                        current_interface = match.group(1)
                        net_info["interfaces"][current_interface] = []
                elif "inet " in line and current_interface: # Ligne IPv4 (ex:    inet 127.0.0.1/8 scope host lo)
                    match = re.search(r'inet (\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2})', line)
                    if match:
                        addr, mask_bits = match.group(1).split('/')
                        net_info["interfaces"][current_interface].append({
                            "address": addr,
                            "netmask_bits": int(mask_bits),
                            "family": "IPv4"
                        })
                elif "inet6 " in line and current_interface: # Ligne IPv6 (ex:    inet6 ::1/128 scope host )
                     match = re.search(r'inet6 ([0-9a-fA-F:]+/\d{1,3})', line)
                     if match:
                         addr, mask_bits = match.group(1).split('/')
                         net_info["interfaces"][current_interface].append({
                             "address": addr,
                             "netmask_bits": int(mask_bits),
                             "family": "IPv6"
                         })
            
            # Récupération des serveurs DNS (souvent dans /etc/resolv.conf)
            resolv_conf = self._run_command(["cat", "/etc/resolv.conf"])
            for line in resolv_conf.splitlines():
                if line.startswith("nameserver"):
                    dns_ip = line.split()[1]
                    if dns_ip not in net_info["dns_servers"]:
                        net_info["dns_servers"].append(dns_ip)

        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des infos réseau: {e}")
        self._log("debug", f"Network Info: {net_info}")
        return net_info

    def _get_users_info(self) -> list:
        users_info = []
        try:
            # Utiliser la commande 'who' ou 'w'
            who_output = self._run_command(["who"])
            for line in who_output.splitlines():
                parts = line.split()
                if len(parts) >= 5: # user terminal date time
                    name = parts[0]
                    terminal = parts[1]
                    host = parts[2]
                    # La date et l'heure peuvent être combinées ou séparées
                    started_time = " ".join(parts[3:5]) # ex: "2024-06-20 01:23"
                    users_info.append({
                        "name": name,
                        "terminal": terminal,
                        "host": host,
                        "started": started_time
                    })
        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des infos utilisateurs: {e}")
        self._log("debug", f"Users Info: {users_info}")
        return users_info
    
    def _get_running_processes(self) -> list:
        processes_list = []
        try:
            # Utiliser la commande 'ps -eo pid,ppid,comm,user,args'
            # 'comm' est le nom de la commande, 'args' est la ligne de commande complète
            # Sur Termux, 'ps' est généralement 'toybox ps', qui peut avoir des options différentes
            # Essayer des options communes ou plus basiques.
            # 'ps -aux' est une option commune mais la sortie est plus difficile à parser.
            # 'ps -e -o pid,comm,user,args' est plus ciblé.
            
            ps_output = self._run_command(["ps", "-e", "-o", "pid,comm,user,args"])
            lines = ps_output.splitlines()
            if len(lines) > 1: # Skip header
                for line in lines[1:]:
                    try:
                        # La sortie de ps peut varier, utiliser regex pour plus de robustesse
                        # PID COMM USER COMMAND
                        match = re.match(r'^\s*(\d+)\s+([^ ]+)\s+([^ ]+)\s+(.*)', line)
                        if match:
                            pid = int(match.group(1))
                            comm = match.group(2) # Nom de la commande
                            user = match.group(3)
                            args = match.group(4) # Arguments complets
                            
                            processes_list.append({
                                "pid": pid,
                                "name": comm,
                                "username": user,
                                "cmdline": args
                            })
                        else:
                            self._log("warning", f"Impossible de parser la ligne de processus: {line}")
                    except ValueError as ve:
                        self._log("warning", f"Erreur de conversion dans le parsing ps: {line} - {ve}")

        except Exception as e:
            self._log("error", f"Erreur lors de la récupération des processus: {e}")
        self._log("debug", f"Collected {len(processes_list)} running processes.")
        return processes_list


    def collect_system_info(self) -> dict:
        """
        Collecte toutes les informations système et les retourne dans un dictionnaire.
        """
        self._log("info", "Début de la collecte des informations système (sans psutil)...")
        system_info = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),
            "hostname": self._get_hostname(),
            "os_info": self._get_os_info(),
            "cpu_info": self._get_cpu_info(),
            "memory_info": self._get_memory_info(),
            "disk_info": self._get_disk_info(),
            "network_info": self._get_network_info(),
            "users_info": self._get_users_info(),
            "running_processes": self._get_running_processes()
        }
        self._log("info", "Collecte des informations système terminée.")
        return system_info

# --- Partie de test (à exécuter si le fichier est lancé directement) ---
if __name__ == "__main__":
    print("[+] Test du module SystemProfiler (sans psutil)...")

    class MockLogger:
        def log_info(self, msg): print(f"[INFO] {msg}")
        def log_warning(self, msg): print(f"[WARN] {msg}")
        def log_error(self, msg): print(f"[ERROR] {msg}")
        def log_debug(self, msg): print(f"[DEBUG] {msg}")

    logger = MockLogger()
    profiler = SystemProfiler(logger=logger)

    system_data = profiler.collect_system_info()

    # Afficher les informations collectées de manière lisible
    print("\n--- Informations Système Collectées ---")
    print(json.dumps(system_data, indent=4)) # Utilisation de json.dumps pour une sortie formatée

    # Quelques assertions basiques pour vérifier que des données ont été collectées
    assert system_data["hostname"] != "N/A", "Le hostname n'a pas été collecté."
    assert "system" in system_data["os_info"], "Les informations OS sont manquantes."
    assert "logical_cores" in system_data["cpu_info"] or system_data["cpu_info"].get("logical_cores") != "N/A", "Les informations CPU sont manquantes ou N/A."
    assert "total_gb" in system_data["memory_info"] or system_data["memory_info"].get("total_gb") != "N/A", "Les informations mémoire sont manquantes ou N/A."
    assert isinstance(system_data["disk_info"], list), "Les informations disque ne sont pas une liste."
    assert isinstance(system_data["network_info"]["interfaces"], dict), "Les informations réseau sont manquantes ou mal formatées."
    assert isinstance(system_data["users_info"], list), "Les informations utilisateurs sont manquantes."
    assert isinstance(system_data["running_processes"], list), "Les informations processus sont manquantes."

    print("\n[+] Tests du module SystemProfiler terminés.")
    print("[!] Note: Les détails des informations collectées peuvent varier considérablement "
          "selon le système d'exploitation, les outils installés et les permissions de l'utilisateur.")

