[🇫🇷 Français](https://github.com/karim93160/exfiltration_agent/blob/main/README.md) | [🇬🇧 English](https://github.com/karim93160/exfiltration_agent/blob/main/README_EN.md) | [🇪🇸 Español](https://github.com/karim93160/exfiltration_agent/blob/main/README_ES.md)
Exfiltration-Agent:
The Stealthy Data Exfiltration Tool for Red Teams
🚨 Warning - Ethical Use Only 🚨
This tool is developed and provided strictly for educational purposes, offensive security research, and authorized penetration testing (Red Team).
Any use of Exfiltration-Agent on unauthorized systems is strictly illegal and contrary to cybersecurity ethics. The creators and contributors of this project disclaim all responsibility for any abusive or malicious use.
Use it responsibly and only within legal and ethical frameworks.
✨ Project Overview
Exfiltration-Agent is an offensive security engineering solution designed to accurately simulate advanced data exfiltration tactics. Built for stealth, robustness, and modularity, this agent allows Red Team members and security analysts to proactively test the resilience of their infrastructures.
Whether your goal is to evaluate data leak detection, firewall effectiveness, or your systems' ability to withstand discrete agents, Exfiltration-Agent offers granular control over its operations via an intuitive web interface.
Why Exfiltration-Agent?
 * Realistic Simulation: Reproduce complex exfiltration scenarios to assess your organization's ability to detect and prevent data leaks.
 * Built-in Stealth: Advanced process hiding techniques, trace cleaning, and anti-evasion for discrete and difficult-to-attribute tests.
 * Multi-Channel: Use various exfiltration methods, including HTTP/HTTPS and DNS tunneling, to test multi-layered defenses and blind spots.
 * Operational Robustness: Never lose data. The agent handles transmission failures with intelligent retry mechanisms and encrypted local persistence.
 * User-Friendly: A modern and intuitive web interface simplifies configuration and control, making the tool accessible even on constrained environments like Termux.
 * Modularity: Its architecture based on separate modules facilitates code auditing, modification, and the addition of new features.
🚀 Key Features in Detail
Exfiltration-Agent is a comprehensive suite of exfiltration capabilities, each designed to maximize efficiency and discretion.
🔐 AES256 Encryption
 * Guaranteed Confidentiality: All collected data is encrypted with the AES-256 algorithm in GCM (Galois/Counter Mode) before transmission.
 * Integrity and Authentication: GCM mode ensures not only confidentiality but also data integrity and authenticity, protecting against any alteration.
 * Dedicated Key: A unique AES key is used, configurable via the interface, ensuring the security of your exfiltrations.
🗜️ Zlib/Gzip Compression
 * Bandwidth Optimization: Data is compressed with Zlib or Gzip before encryption and sending, thereby reducing payload size and network consumption.
 * Exfiltration Speed: Smaller transfers result in faster exfiltrations and less time spent on the network, increasing stealth.
📁 Advanced File Scanning and Filtering
 * Recursive Search: Deeply scans specified directories to discover targeted files.
 * Granular Filtering:
   * By Extension: Inclusion (.doc, .txt, .db) and exclusion (.exe, .dll) of specific file types.
   * By Size: Definition of minimum and maximum sizes to target relevant files.
   * By Content: Search for specific keywords or regular expression (regex) patterns inside files to identify sensitive data.
💻 System Profiling (without psutil)
 * In-Depth Reconnaissance: Collects vital information about the compromised environment without complex external dependencies.
 * Information Collected:
   * Hostname and operating system details.
   * CPU and memory information.
   * Disk partition information.
   * Network interface details (IP addresses, DNS servers).
   * Logged-in users and running processes.
 * Robustness: Uses native shell commands (df, ip, ps, who, cat /proc/...) to ensure maximum compatibility on heterogeneous systems (including Termux).
🧬 Anti-Debug / Sandbox & Evasion
 * Hostile Environment Detection: The agent attempts to identify if it is being run in an analysis environment, such as a debugger, virtual machine, or container.
 * Evasion Strategies:
   * Checking for suspicious parent processes.
   * Analyzing system uptime (short runtime = sandbox).
   * Checking disk space ratios.
   * Searching for VM/container specific artifacts.
   * Checking for ptrace (debugger detection on Linux).
   * Analyzing CPU flags for virtualization indicators.
 * Adaptive Behavior: If a suspicious environment is detected, the agent can quietly shut down or alter its behavior to avoid analysis.
🌐 HTTP/HTTPS Exfiltration
 * Primary Channel: The most common and often most effective way to transfer data.
 * Network Stealth: Uses the requests library with random User-Agents and realistic HTTP headers to mask exfiltration traffic among normal web traffic.
 * Robust Handling: Includes handling of timeouts, connection errors, and HTTP responses.
📡 DNS Exfiltration
 * Advanced Stealth Channel: An often underestimated exfiltration method, as DNS traffic is rarely deeply inspected.
 * Intelligent Tunneling: Binary data (encrypted and compressed) is encoded in Base32 or Hexadecimal, then divided into small "chunks" sent as subdomains in DNS queries (Type A).
 * Reliability: Includes transaction IDs and chunk indexes to allow the control server to reassemble data correctly.
🔄 Rotation/Retry Manager
 * Data Persistence: If an exfiltration attempt fails (network issue, inaccessible server), data is not lost.
 * Intelligent Retries: Data is queued, and re-send attempts are made with exponential backoff (increasing delay between attempts) to avoid saturating the network or the C2.
 * Encrypted Local Logging: Data persisting in the queue is saved to an encrypted local file, ensuring its security even on the compromised machine.
🕵️ Stealth Mode
 * Process Hiding: Attempts to modify the visible process name to blend in with legitimate system processes.
 * Temporary Working Directory: Uses ephemeral paths (/tmp or Termux equivalent) to store temporary files, avoiding persistent traces.
 * Self-Deletion of Logs and Files: At the end of the operation (unless disabled in debug mode), the agent actively cleans up all encrypted logs and temporary files it created.
 * Timestomping: Alters the timestamps of created or modified files to obscure recent agent activity.
🔁 Threads/Async Tasks
 * Optimal Performance: The agent is designed with a multi-threaded architecture.
 * Simultaneous Operations: File scanning and the exfiltration/retry process run in parallel, maximizing efficiency and speed without blocking the agent.
 * Secure Communication: Uses thread-safe queues for reliable communication between different threads.
🧊 Payload Dropper
 * Post-Exfiltration Deployment: Allows the agent to download and drop a secondary executable (RAT, shell, other simulated malware) on the target machine after a successful exfiltration or based on a criterion.
 * Flexibility: Facilitates extending operations on the target.
 * Executable Rendering: Option to set execution permissions on the dropped file.
📊 Logger/Telemetry
 * Stealthy Audit: All agent activities are logged locally in a dedicated file.
 * Log Encryption: The log file itself is encrypted with AES256 to maintain discretion.
 * Post-Operational Analysis: The web control panel allows reading, decrypting, and displaying these logs, offering complete visibility into the operation's progress.
🛠️ Installation and Usage (Complete Guide)
This guide is optimized for Termux environments (Android).
Prerequisites
 * An Android device with Termux installed.
 * An active internet connection.
 * (Optional but highly recommended) An account on webhook.site to easily test HTTP/HTTPS exfiltration, or a C2 server you control.
Automated Installation Steps
 * Open Termux on your Android device.
 * Clone the GitHub repository:
   git clone https://github.com/Karim93160/exfiltration_agent

 * Run the all-in-one installation script:
   cd exfiltration_agent
chmod +x setuptermux.sh exfagent.py control_panel.py # Ensure execution permissions
./setup_termux.sh

   * The script will install all necessary Termux packages (Python, clang, build-essential, iproute2, procps, coreutils, etc.) and all required Python dependencies (pycryptodome, requests, dnspython).
   * It will automatically launch the web control panel in the background (nohup python -u control_panel.py ... &). You will see a nohup: ignoring input message and the process PID.
Initial Access and Configuration via Web Control Panel
The control panel is your complete graphical interface for managing the agent.
 * Access the Control Panel:
   Open your Android device's web browser and enter the address:
   http://127.0.0.1:8050

   (If port 8050 is already in use, an error message will appear in the Termux terminal. You will then need to modify the port=8050 line in the control_panel.py file to another port, such as 8051, then restart the script.)
 * First Configuration:
   * On first opening (after generation by setup_termux.sh), the interface will display an automatically generated AES key in the "AES Key" field.
   * Crucial Action: In the "Exfiltration Target (URL or IP:Port)" field, replace the default URL with your unique webhook.site URL or the address of your own C2 control server. This is where the agent will send the data.
   * All other fields (scan path, file types, etc.) will be pre-filled with intelligent default values (/data/data/com.termux/files/home/storage/shared is a good starting point for Android's internal storage).
 * Save Your Configuration:
   Once you have customized the options, click the "Save Configuration" button. This will save all the settings you have defined in the ~/exfiltrationagent/sharedconfig.json file. This way, the next time you open the panel, your preferences will be automatically loaded.
Daily Use of the Agent via the Web Interface
After the initial configuration, usage is very simple:
 * Launch the Control Panel (if not already running):
   If you have closed Termux or stopped the panel, restart it from the agent's directory:
   cd ~/exfiltration_agent
nohup python -u controlpanel.py > controlpanel.log 2>&1 &

   Then access http://127.0.0.1:8050 again in your browser.
 * Configure and Launch the Agent:
   * Fields will be pre-filled with your last saved configuration.
   * Adjust settings according to the desired test scenario (new scan location, new keywords, change exfiltration method, etc.).
   * Click the "Launch Agent" button. The agent will run in the background, discreetly, and begin its operations.
 * Monitor Activity and Manage the Agent:
   * Click "Refresh Logs (locally encrypted)" to see agent activity in real-time in the interface (decrypted by the control panel using the AES key from the field).
   * If using HTTPS exfiltration, check your webhook.site page (or your C2) to verify receipt of exfiltrated data.
   * Use the "Stop Agent" button to stop it cleanly. This will trigger its cleanup mechanism (if not disabled in debug mode).
 * Download Logs for Analysis:
   * The "Download Raw Logs (encrypted)" button allows you to retrieve the agent_logs.enc file. This file contains all agent activities, encrypted. You can decrypt it with your control panel's AES key for in-depth offline analysis.
📜 Project Structure (GitHub Repository)
exfiltration_agent/
├── README.md                 # This file: Complete project documentation
├── exf_agent.py              # The main exfiltration agent script
├── control_panel.py          # The Dash web interface script for control
├── modules/                  # Directory containing all internal agent modules
│   ├── aes256.py             # AES-256 GCM encryption
│   ├── anti_evasion.py       # Anti-debugging / sandbox techniques
│   ├── compression.py        # Zlib/Gzip compression
│   ├── config.py             # Configuration argument management
│   ├── exfiltration_dns.py   # Exfiltration via DNS tunneling
│   ├── exfiltration_http.py  # Exfiltration via HTTP/HTTPS
│   ├── file_scanner.py       # File scanning and filtering
│   ├── logger.py             # Encrypted activity logging
│   ├── payload_dropper.py    # Dropping secondary payloads
│   ├── retry_manager.py      # Retry management and persistence
│   ├── stealth_mode.py       # Stealth techniques and cleanup
│   └── system_profiler.py    # System profiling (without psutil)
├── requirements.txt          # External Python dependencies
├── setup_termux.sh           # Automated installation script for Termux

🤝 Contributions
Contributions are welcome! If you'd like to improve ip-nose, fix bugs, or add new features, please consult our Contribution Guide.





License 📜
hashish is distributed under the MIT License
Contact 📧
For any questions or suggestions, feel free to open an issue on GitHub or contact us by email:
<div align="center">
<h2>🌿 exfiltration_agent - Code of Conduct 🌿</h2>
<p>
We are committed to creating a welcoming and respectful environment for all contributors.
Please take a moment to read our <a href="CODE_OF_CONDUCT.md">Code of Conduct</a>.
By participating in this project, you agree to abide by its terms.
</p>
<p>
<a href="CODE_OF_CONDUCT.md">
<img src="https://img.shields.io/badge/Code%20of%20Conduct-Please%20Read-blueviolet?style=for-the-badge&logo=github" alt="Code of Conduct">
</a>
</p>
</div>
<div align="center">
<h2>🐞 Report a Bug in exfiltration_agent 🐞</h2>
<p>
Encountering a problem with exfiltration_agent? Help us improve the project by reporting bugs!
Click the button below to directly open a new pre-filled bug report.
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=">
<img src="https://img.shields.io/badge/Report%20a%20Bug-Open%20an%20Issue-red?style=for-the-badge&logo=bugsnag" alt="Report a Bug">
</a>
</p>
</div>
<div align="center">
<h2>💬 ip-nose Community - Join the Discussion! 💬</h2>
<p>
Questions, suggestions, or want to discuss the ip-nose project?
Join the community on GitHub Discussions!
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/discussions">
<img src="https://img.shields.io/badge/Join%20the%20Community-Discussions-blue?style=for-the-badge&logo=github" alt="Join the Community">
</a>
</p>
</div>
