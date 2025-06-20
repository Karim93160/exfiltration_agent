# Exfiltration-Agent : *L'outil furtif d'exfiltration de données pour la Red Team*

## 🚨 Avertissement - Usage Éthique Uniquement 🚨

**Cet outil est développé et mis à disposition à des fins strictement pédagogiques, de recherche en sécurité offensive, et de tests d'intrusion autorisés (Red Team).**

Toute utilisation de Exfiltration-Agent sur des systèmes non autorisés est strictement illégale et contraire à l'éthique de la cybersécurité. Les créateurs et contributeurs de ce projet déclinent toute responsabilité en cas d'utilisation abusive ou malveillante.

**Utilisez-le de manière responsable et uniquement dans le cadre légal et éthique.**

## ✨ Vue d'Ensemble du Projet

Exfiltration-Agent est une solution d'ingénierie de sécurité offensive conçue pour simuler avec précision les tactiques avancées d'exfiltration de données. Pensé pour la furtivité, la robustesse et la modularité, cet agent permet aux équipes de Red Team et aux analystes de sécurité de mettre à l'épreuve de manière proactive la résilience de leurs infrastructures.

Que votre objectif soit d'évaluer la détection des fuites de données, l'efficacité des pare-feux, ou la capacité de vos systèmes à résister à des agents discrets, Exfiltration-Agent vous offre un contrôle granulaire sur ses opérations via une interface web intuitive.

## Pourquoi Exfiltration-Agent ?

- **Simulation Réaliste** : Reproduisez des scénarios complexes d'exfiltration pour évaluer la capacité de votre organisation à détecter et à prévenir les fuites de données.
- **Furtivité Intégrée** : Des techniques avancées de masquage de processus, de nettoyage des traces, et d'anti-évasion pour des tests discrets et difficiles à attribuer.
- **Multi-Canal** : Utilisez diverses méthodes d'exfiltration, y compris HTTP/HTTPS et le tunneling DNS, pour tester les défenses multicouches et les angles morts.
- **Robustesse Opérationnelle** : Ne perdez jamais de données. L'agent gère les échecs de transmission avec des mécanismes de ré-essais intelligents et une persistance locale chiffrée.
- **Convivialité** : Une interface web moderne et intuitive simplifie la configuration et le contrôle, rendant l'outil accessible même sur des environnements contraints comme Termux.
- **Modularité** : Son architecture basée sur des modules séparés facilite l'audit du code, sa modification et l'ajout de nouvelles fonctionnalités.

## 🚀 Fonctionnalités Clés en Détail

Exfiltration-Agent est une suite complète de capacités d'exfiltration, chacune conçue pour maximiser l'efficacité et la discrétion.

### 🔐 Chiffrement AES256

- **Confidentialité Assurée** : Toutes les données collectées sont chiffrées avec l'algorithme AES-256 en mode GCM (Galois/Counter Mode) avant d'être transmises.
- **Intégrité et Authentification** : Le mode GCM garantit non seulement la confidentialité, mais aussi l'intégrité et l'authenticité des données, protégeant contre toute altération.
- **Clé Dédiée** : Une clé AES unique est utilisée, configurable via l'interface, assurant la sécurité de vos exfiltrations.

### 🗜️ Compression Zlib/Gzip

- **Optimisation de la Bande Passante** : Les données sont compressées avec Zlib ou Gzip avant le chiffrement et l'envoi, réduisant ainsi la taille des charges utiles et la consommation de réseau.
- **Rapidité d'Exfiltration** : Des transferts plus petits se traduisent par des exfiltrations plus rapides et moins de temps passé sur le réseau, augmentant la furtivité.

### 📁 Scan et Filtrage Avancé de Fichiers

- **Recherche Récursive** : Scanne en profondeur les répertoires spécifiés pour découvrir les fichiers ciblés.
- **Filtrage Granulaire** :
  - **Par Extension** : Inclusion (.doc, .txt, .db) et exclusion (.exe, .dll) de types de fichiers spécifiques.
  - **Par Taille** : Définition de tailles minimales et maximales pour cibler les fichiers pertinents.
  - **Par Contenu** : Recherche de mots-clés ou de motifs d'expressions régulières (regex) spécifiques à l'intérieur des fichiers pour identifier les données sensibles.

### 💻 Profilage Système (sans psutil)

- **Reconnaissance Approfondie** : Collecte des informations vitales sur l'environnement compromis sans dépendances externes complexes.
- **Informations Collectées** :
  - Nom d'hôte et détails du système d'exploitation.
  - Informations CPU et mémoire.
  - Informations sur les partitions de disque.
  - Détails des interfaces réseau (adresses IP, serveurs DNS).
  - Utilisateurs connectés et processus en cours d'exécution.
- **Robustesse** : Utilise des commandes shell natives (df, ip, ps, who, cat /proc/...) pour assurer la compatibilité maximale sur des systèmes hétérogènes (y compris Termux).

### 🧬 Anti-Debug / Sandbox & Évasion

- **Détection d'Environnements Hostiles** : L'agent tente d'identifier s'il est exécuté dans un environnement d'analyse, comme un débogueur, une machine virtuelle ou un conteneur.
- **Stratégies d'Évasion** :
  - Vérification des processus parents suspects.
  - Analyse de l'uptime système (temps de fonctionnement court = sandbox).
  - Vérification des ratios d'espace disque.
  - Recherche d'artefacts spécifiques aux VM/conteneurs.
  - Vérification de ptrace (détection de débogueur sur Linux).
  - Analyse des flags CPU pour les indicateurs de virtualisation.
- **Comportement Adaptatif** : Si un environnement suspect est détecté, l'agent peut s'arrêter discrètement ou modifier son comportement pour éviter d'être analysé.

### 🌐 Exfiltration HTTP/HTTPS

- **Canal Principal** : Le moyen le plus courant et souvent le plus efficace pour transférer des données.
- **Furtivité Réseau** : Utilise la bibliothèque requests avec des User-Agents aléatoires et des en-têtes HTTP réalistes pour masquer le trafic d'exfiltration parmi le trafic web normal.
- **Gestion Robuste** : Inclut la gestion des timeouts, des erreurs de connexion et des réponses HTTP.

### 📡 Exfiltration DNS

- **Canal Furtif Avancé** : Une méthode d'exfiltration souvent sous-estimée, car le trafic DNS est rarement inspecté en profondeur.
- **Tunneling Intelligent** : Les données binaires (chiffrées et compressées) sont encodées en Base32 ou Hexadécimal, puis divisées en petits "chunks" envoyés comme sous-domaines dans des requêtes DNS (Type A).
- **Fiabilité** : Inclut des identifiants de transaction et des index de chunk pour permettre au serveur de contrôle de réassembler les données correctement.

### 🔄 Rotation/Retry Manager

- **Persistance des Données** : Si une tentative d'exfiltration échoue (problème réseau, serveur inaccessible), les données ne sont pas perdues.
- **Ré-essais Intelligents** : Les données sont mises en file d'attente et des tentatives de ré-envoi sont effectuées avec un backoff exponentiel (délai croissant entre les essais) pour ne pas saturer le réseau ou le C2.
- **Journalisation Chiffrée Locale** : Les données qui persistent en file d'attente sont sauvegardées dans un fichier local chiffré, assurant leur sécurité même sur la machine compromise.

### 🕵️ Stealth Mode

- **Masquage de Processus** : Tente de modifier le nom du processus visible pour se fondre dans les processus système légitimes.
- **Répertoire de Travail Temporaire** : Utilise des chemins éphémères (/tmp ou équivalent Termux) pour stocker les fichiers temporaires, évitant ainsi de laisser des traces persistantes.
- **Auto-Suppression des Logs et Fichiers** : À la fin de l'opération (sauf si désactivé en mode debug), l'agent nettoie activement tous les logs chiffrés et les fichiers temporaires qu'il a créés.
- **Timestomping** : Alterne les horodatages des fichiers créés ou modifiés pour masquer l'activité récente de l'agent.

### 🔁 Threads/Async Tasks

- **Performance Optimale** : L'agent est conçu avec une architecture multi-threadée.
- **Opérations Simultanées** : Le scan de fichiers et le processus d'exfiltration/ré-essai s'exécutent en parallèle, maximisant l'efficacité et la rapidité sans bloquer l'agent.
- **Communication Sécurisée** : Utilise des files d'attente (queues) thread-safe pour une communication fiable entre les différents threads.

### 🧊 Payload Dropper

- **Déploiement Post-Exfiltration** : Permet à l'agent de télécharger et de déposer un exécutable secondaire (RAT, shell, autre malware simulé) sur la machine cible après une exfiltration réussie ou en fonction d'un critère.
- **Flexibilité** : Facilite l'extension des opérations sur la cible.
- **Rendu Exécutable** : Option pour définir les permissions d'exécution sur le fichier déposé.

### 📊 Logger/Telemetry

- **Audit Furtif** : Toutes les activités de l'agent sont journalisées localement dans un fichier dédié.
- **Chiffrement des Logs** : Le fichier de logs est lui-même chiffré avec AES256 pour maintenir la discrétion.
- **Analyse Post-Opérationnelle** : Le panneau de contrôle web permet de lire, déchiffrer et afficher ces logs, offrant une visibilité complète sur le déroulement de l'opération.

## 🛠️ Installation et Utilisation (Guide Complet)

Ce guide est optimisé pour les environnements Termux (Android).

### Prérequis

- Un appareil Android avec Termux installé.
- Une connexion internet active.
- (Optionnel mais fortement recommandé) Un compte sur webhook.site pour tester l'exfiltration HTTP/HTTPS facilement, ou un serveur C2 que vous contrôlez.

### Étapes d'Installation Automatisées

1. Ouvrez Termux sur votre appareil Android.
2. Clonez le dépôt GitHub :
   ```bash
   git clone [VOTREURLDUDÉPÔTGITHUB] exfiltration_agent
   ```
   *(N'oubliez pas de remplacer [VOTREURLDUDÉPÔTGITHUB] par l'URL réelle de votre dépôt !)*
3. Lancez le script d'installation tout-en-un :
   ```bash
   cd exfiltration_agent
   chmod +x setuptermux.sh exfagent.py control_panel.py # Assure les permissions d'exécution
   ./setup_termux.sh
   ```
   - Le script installera tous les packages Termux nécessaires (Python, clang, build-essential, iproute2, procps, coreutils, etc.) et toutes les dépendances Python requises (pycryptodome, requests, dnspython).
   - Il lancera automatiquement le panneau de contrôle web en arrière-plan (`nohup python -u control_panel.py ... &`). Vous verrez un message `nohup: ignoring input` et le PID du processus.

### Accès et Configuration Initiale via le Panneau de Contrôle Web

Le panneau de contrôle est votre interface graphique complète pour gérer l'agent.

1. **Accédez au Panneau de Contrôle** :
   Ouvrez le navigateur web de votre appareil Android et saisissez l'adresse :
   ```
   http://127.0.0.1:8050
   ```
   *(Si le port 8050 est déjà utilisé, un message d'erreur s'affichera dans le terminal Termux. Vous devrez alors modifier la ligne `port=8050` dans le fichier `control_panel.py` vers un autre port, comme 8051, puis relancer le script.)*

2. **Première Configuration** :
   - À la première ouverture (après la génération par `setup_termux.sh`), l'interface affichera une clé AES générée automatiquement dans le champ "Clé AES".
   - **Action Cruciale** : Dans le champ "Cible d'Exfiltration (URL ou IP:Port)", remplacez l'URL par défaut par l'URL unique de votre webhook.site ou l'adresse de votre propre serveur de contrôle C2. C'est là que l'agent enverra les données.
   - Tous les autres champs (chemin à scanner, types de fichiers, etc.) seront pré-remplis avec des valeurs par défaut intelligentes (`/data/data/com.termux/files/home/storage/shared` est un bon point de départ pour le stockage interne d'Android).

3. **Sauvegardez votre Configuration** :
   Une fois que vous avez personnalisé les options, cliquez sur le bouton "Sauvegarder la Configuration". Cela enregistrera tous les paramètres que vous avez définis dans le fichier `~/exfiltrationagent/sharedconfig.json`. Ainsi, la prochaine fois que vous ouvrirez le panneau, vos préférences seront automatiquement chargées.

### Utilisation Quotidienne de l'Agent via l'Interface Web

Après la configuration initiale, l'utilisation est très simple :

1. **Lancez le Panneau de Contrôle (si ce n'est pas déjà fait)** :
   Si vous avez fermé Termux ou arrêté le panneau, relancez-le depuis le répertoire de l'agent :
   ```bash
   cd ~/exfiltration_agent
   nohup python -u controlpanel.py > controlpanel.log 2>&1 &
   ```
   Puis accédez de nouveau à `http://127.0.0.1:8050` dans votre navigateur.

2. **Configurez et Lancez l'Agent** :
   - Les champs seront pré-remplis avec votre dernière configuration sauvegardée.
   - Ajustez les paramètres selon le scénario de test souhaité (nouvel emplacement de scan, nouveaux mots-clés, changement de méthode d'exfiltration, etc.).
   - Cliquez sur le bouton "Lancer l'Agent". L'agent s'exécutera en arrière-plan, discrètement, et commencera ses opérations.

3. **Surveillez l'Activité et Gérez l'Agent** :
   - Cliquez sur "Rafraîchir les Logs (chiffrés localement)" pour voir l'activité de l'agent en temps réel dans l'interface (déchiffrée par le panneau de contrôle en utilisant la clé AES du champ).
   - Si vous utilisez l'exfiltration HTTPS, consultez votre page webhook.site (ou votre C2) pour vérifier la réception des données exfiltrées.
   - Utilisez le bouton "Arrêter l'Agent" pour l'arrêter proprement. Cela déclenchera son mécanisme de nettoyage (si non désactivé en mode debug).

4. **Téléchargez les Logs pour Analyse** :
   - Le bouton "Télécharger les Logs Bruts (chiffrés)" vous permet de récupérer le fichier `agent_logs.enc`. Ce fichier contient toutes les activités de l'agent, chiffrées. Vous pouvez le déchiffrer avec la clé AES de votre panneau de contrôle pour une analyse approfondie hors ligne.

## 📜 Structure du Projet (Dépôt GitHub)

```
exfiltration_agent/
├── README.md                 # Ce fichier : Documentation complète du projet
├── exf_agent.py              # Le script principal de l'agent d'exfiltration
├── control_panel.py          # Le script de l'interface web Dash pour le contrôle
├── modules/                  # Répertoire contenant tous les modules internes de l'agent
│   ├── aes256.py             # Chiffrement AES-256 GCM
│   ├── anti_evasion.py       # Techniques anti-débogage / sandbox
│   ├── compression.py        # Compression Zlib/Gzip
│   ├── config.py             # Gestion des arguments de configuration
│   ├── exfiltration_dns.py   # Exfiltration via tunneling DNS
│   ├── exfiltration_http.py  # Exfiltration via HTTP/HTTPS
│   ├── file_scanner.py       # Scan et filtrage de fichiers
│   ├── logger.py             # Journalisation chiffrée des activités
│   ├── payload_dropper.py    # Dépôt de payloads secondaires
│   ├── retry_manager.py      # Gestion des ré-essais et persistance
│   ├── stealth_mode.py       # Techniques de furtivité et nettoyage
│   └── system_profiler.py    # Profilage système (sans psutil)
├── requirements.txt          # Dépendances Python externes
├── setup_termux.sh           # Script d'installation automatisée pour Termux
```

## 🤝 Contributions & Support

Les contributions sont les bienvenues ! Si vous avez des idées d'amélioration, des rapports de bugs, ou des suggestions, n'hésitez pas à :

- **Ouvrir une Issue** : Pour rapporter un bug ou suggérer une nouvelle fonctionnalité.
- **Soumettre une Pull Request** : Pour proposer des modifications ou des ajouts de code.

Votre aide est précieuse pour faire évoluer Exfiltration-Agent !

## 🛡️ Licence

Ce projet est distribué sous la licence MIT. Cela signifie que vous êtes libre d'utiliser, de copier, de modifier, de fusionner, de publier, de distribuer, de sous-licencier et/ou de vendre des copies du Logiciel, sous réserve des conditions stipulées dans la licence.

**MIT License**
```
