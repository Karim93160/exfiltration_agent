[🇫🇷 Français](https://github.com/karim93160/exfiltration_agent/blob/main/README.md) | [🇬🇧 English](https://github.com/karim93160/exfiltration_agent/blob/main/README_EN.md) | [🇪🇸 Español](https://github.com/karim93160/exfiltration_agent/blob/main/README_ES.md)
Exfiltration-Agent:
La herramienta sigilosa de exfiltración de datos para Red Team
🚨 Advertencia - Solo para Uso Ético 🚨
Esta herramienta está desarrollada y disponible estrictamente con fines educativos, de investigación en seguridad ofensiva y de pruebas de penetración autorizadas (Red Team).
Cualquier uso de Exfiltration-Agent en sistemas no autorizados es estrictamente ilegal y contrario a la ética de la ciberseguridad. Los creadores y colaboradores de este proyecto declinan toda responsabilidad en caso de uso indebido o malintencionado.
Úselo de manera responsable y únicamente dentro del marco legal y ético.
✨ Descripción General del Proyecto
Exfiltration-Agent es una solución de ingeniería de seguridad ofensiva diseñada para simular con precisión tácticas avanzadas de exfiltración de datos. Diseñado para la sigilo, la robustez y la modularidad, este agente permite a los equipos de Red Team y a los analistas de seguridad probar proactivamente la resiliencia de sus infraestructuras.
Ya sea que su objetivo sea evaluar la detección de fugas de datos, la efectividad de los firewalls o la capacidad de sus sistemas para resistir agentes discretos, Exfiltration-Agent le ofrece un control granular sobre sus operaciones a través de una interfaz web intuitiva.
¿Por qué Exfiltration-Agent?
 * Simulación Realista: Reproduzca escenarios complejos de exfiltración para evaluar la capacidad de su organización para detectar y prevenir fugas de datos.
 * Sigilo Integrado: Técnicas avanzadas de ocultamiento de procesos, limpieza de rastros y anti-evasión para pruebas discretas y difíciles de atribuir.
 * Multi-Canal: Utilice diversos métodos de exfiltración, incluyendo HTTP/HTTPS y tunelización DNS, para probar defensas multicapa y puntos ciegos.
 * Robustez Operacional: Nunca pierda datos. El agente maneja los fallos de transmisión con mecanismos de reintento inteligentes y persistencia local cifrada.
 * Fácil de Usar: Una interfaz web moderna e intuitiva simplifica la configuración y el control, haciendo que la herramienta sea accesible incluso en entornos restringidos como Termux.
 * Modularidad: Su arquitectura basada en módulos separados facilita la auditoría del código, su modificación y la adición de nuevas funcionalidades.
🚀 Características Clave en Detalle
Exfiltration-Agent es una suite completa de capacidades de exfiltración, cada una diseñada para maximizar la eficiencia y la discreción.
🔐 Cifrado AES256
 * Confidencialidad Asegurada: Todos los datos recopilados se cifran con el algoritmo AES-256 en modo GCM (Galois/Counter Mode) antes de ser transmitidos.
 * Integridad y Autenticación: El modo GCM garantiza no solo la confidencialidad, sino también la integridad y autenticidad de los datos, protegiendo contra cualquier alteración.
 * Clave Dedicada: Se utiliza una clave AES única, configurable a través de la interfaz, asegurando la seguridad de sus exfiltraciones.
🗜️ Compresión Zlib/Gzip
 * Optimización del Ancho de Banda: Los datos se comprimen con Zlib o Gzip antes del cifrado y el envío, reduciendo así el tamaño de las cargas útiles y el consumo de red.
 * Velocidad de Exfiltración: Transferencias más pequeñas se traducen en exfiltraciones más rápidas y menos tiempo en la red, aumentando el sigilo.
📁 Escaneo y Filtrado Avanzado de Archivos
 * Búsqueda Recursiva: Escanea en profundidad los directorios especificados para descubrir los archivos objetivo.
 * Filtrado Granular:
   * Por Extensión: Inclusión (.doc, .txt, .db) y exclusión (.exe, .dll) de tipos de archivos específicos.
   * Por Tamaño: Definición de tamaños mínimos y máximos para apuntar a los archivos relevantes.
   * Por Contenido: Búsqueda de palabras clave o patrones de expresiones regulares (regex) específicas dentro de los archivos para identificar datos sensibles.
💻 Perfilado del Sistema (sin psutil)
 * Reconocimiento Profundo: Recopila información vital sobre el entorno comprometido sin dependencias externas complejas.
 * Información Recopilada:
   * Nombre de host y detalles del sistema operativo.
   * Información de CPU y memoria.
   * Información sobre las particiones de disco.
   * Detalles de las interfaces de red (direcciones IP, servidores DNS).
   * Usuarios conectados y procesos en ejecución.
 * Robustez: Utiliza comandos de shell nativos (df, ip, ps, who, cat /proc/...) para garantizar la máxima compatibilidad en sistemas heterogéneos (incluido Termux).
🧬 Anti-Debug / Sandbox y Evasión
 * Detección de Entornos Hostiles: El agente intenta identificar si se está ejecutando en un entorno de análisis, como un depurador, una máquina virtual o un contenedor.
 * Estrategias de Evasión:
   * Verificación de procesos padres sospechosos.
   * Análisis del tiempo de actividad del sistema (tiempo de ejecución corto = sandbox).
   * Verificación de proporciones de espacio en disco.
   * Búsqueda de artefactos específicos de VM/contenedores.
   * Verificación de ptrace (detección de depurador en Linux).
   * Análisis de los flags de CPU para indicadores de virtualización.
 * Comportamiento Adaptativo: Si se detecta un entorno sospechoso, el agente puede detenerse discretamente o modificar su comportamiento para evitar ser analizado.
🌐 Exfiltración HTTP/HTTPS
 * Canal Principal: La forma más común y a menudo más efectiva de transferir datos.
 * Sigilo de Red: Utiliza la biblioteca requests con User-Agents aleatorios y encabezados HTTP realistas para enmascarar el tráfico de exfiltración entre el tráfico web normal.
 * Manejo Robusto: Incluye manejo de tiempos de espera, errores de conexión y respuestas HTTP.
📡 Exfiltración DNS
 * Canal Sigiloso Avanzado: Un método de exfiltración a menudo subestimado, ya que el tráfico DNS rara vez se inspecciona en profundidad.
 * Tunelización Inteligente: Los datos binarios (cifrados y comprimidos) se codifican en Base32 o Hexadecimal, luego se dividen en pequeños "chunks" enviados como subdominios en consultas DNS (Tipo A).
 * Fiabilidad: Incluye identificadores de transacción e índices de chunk para permitir que el servidor de control reensamble los datos correctamente.
🔄 Administrador de Rotación/Reintento
 * Persistencia de Datos: Si un intento de exfiltración falla (problema de red, servidor inaccesible), los datos no se pierden.
 * Reintentos Inteligentes: Los datos se ponen en cola y se realizan intentos de reenvío con una retroceso exponencial (demora creciente entre intentos) para no saturar la red o el C2.
 * Registro Local Cifrado: Los datos que persisten en la cola se guardan en un archivo local cifrado, asegurando su seguridad incluso en la máquina comprometida.
🕵️ Modo Sigiloso
 * Ocultamiento de Procesos: Intenta modificar el nombre del proceso visible para mezclarse con los procesos legítimos del sistema.
 * Directorio de Trabajo Temporal: Utiliza rutas efímeras (/tmp o equivalente en Termux) para almacenar archivos temporales, evitando dejar rastros persistentes.
 * Autoeliminación de Registros y Archivos: Al finalizar la operación (a menos que se desactive en modo de depuración), el agente limpia activamente todos los registros cifrados y los archivos temporales que ha creado.
 * Timestomping: Altera las marcas de tiempo de los archivos creados o modificados para ocultar la actividad reciente del agente.
🔁 Hilos/Tareas Asíncronas
 * Rendimiento Óptimo: El agente está diseñado con una arquitectura multihilo.
 * Operaciones Simultáneas: El escaneo de archivos y el proceso de exfiltración/reintento se ejecutan en paralelo, maximizando la eficiencia y la velocidad sin bloquear el agente.
 * Comunicación Segura: Utiliza colas (queues) seguras para hilos para una comunicación confiable entre los diferentes hilos.
🧊 Dropper de Carga Útil
 * Despliegue Post-Exfiltración: Permite que el agente descargue y coloque un ejecutable secundario (RAT, shell, otro malware simulado) en la máquina objetivo después de una exfiltración exitosa o según un criterio.
 * Flexibilidad: Facilita la extensión de las operaciones en el objetivo.
 * Renderizado Ejecutable: Opción para establecer permisos de ejecución en el archivo colocado.
📊 Registrador/Telemetría
 * Auditoría Sigilosa: Todas las actividades del agente se registran localmente en un archivo dedicado.
 * Cifrado de Registros: El archivo de registro en sí está cifrado con AES256 para mantener la discreción.
 * Análisis Post-Operacional: El panel de control web permite leer, descifrar y mostrar estos registros, ofreciendo una visibilidad completa del progreso de la operación.
🛠️ Instalación y Uso (Guía Completa)
Esta guía está optimizada para entornos Termux (Android).
Prerrequisitos
 * Un dispositivo Android con Termux instalado.
 * Una conexión a internet activa.
 * (Opcional pero muy recomendable) Una cuenta en webhook.site para probar fácilmente la exfiltración HTTP/HTTPS, o un servidor C2 que usted controle.
Pasos de Instalación Automatizados
 * Abra Termux en su dispositivo Android.
 * Clone el repositorio de GitHub:
   git clone https://github.com/Karim93160/exfiltration_agent

 * Ejecute el script de instalación todo en uno:
   cd exfiltration_agent
chmod +x setuptermux.sh exfagent.py control_panel.py # Asegura los permisos de ejecución
./setup_termux.sh

   * El script instalará todos los paquetes Termux necesarios (Python, clang, build-essential, iproute2, procps, coreutils, etc.) y todas las dependencias de Python requeridas (pycryptodome, requests, dnspython).
   * Lanzará automáticamente el panel de control web en segundo plano (nohup python -u control_panel.py ... &). Verá un mensaje nohup: ignoring input y el PID del proceso.
Acceso y Configuración Inicial a través del Panel de Control Web
El panel de control es su interfaz gráfica completa para administrar el agente.
 * Acceda al Panel de Control:
   Abra el navegador web de su dispositivo Android e ingrese la dirección:
   http://127.0.0.1:8050

   (Si el puerto 8050 ya está en uso, aparecerá un mensaje de error en la terminal de Termux. Deberá modificar la línea port=8050 en el archivo control_panel.py a otro puerto, como 8051, y luego reiniciar el script).
 * Primera Configuración:
   * Al abrirlo por primera vez (después de la generación por setup_termux.sh), la interfaz mostrará una clave AES generada automáticamente en el campo "Clave AES".
   * Acción Crucial: En el campo "Objetivo de Exfiltración (URL o IP:Puerto)", reemplace la URL predeterminada con la URL única de su webhook.site o la dirección de su propio servidor de control C2. Aquí es donde el agente enviará los datos.
   * Todos los demás campos (ruta de escaneo, tipos de archivo, etc.) se precargarán con valores predeterminados inteligentes (/data/data/com.termux/files/home/storage/shared es un buen punto de partida para el almacenamiento interno de Android).
 * Guarde su Configuración:
   Una vez que haya personalizado las opciones, haga clic en el botón "Guardar Configuración". Esto guardará todas las configuraciones que haya definido en el archivo ~/exfiltrationagent/sharedconfig.json. De esta manera, la próxima vez que abra el panel, sus preferencias se cargarán automáticamente.
Uso Diario del Agente a través de la Interfaz Web
Después de la configuración inicial, el uso es muy sencillo:
 * Inicie el Panel de Control (si no está ya en ejecución):
   Si ha cerrado Termux o detenido el panel, reinícielo desde el directorio del agente:
   cd ~/exfiltration_agent
nohup python -u controlpanel.py > controlpanel.log 2>&1 &

   Luego acceda de nuevo a http://127.0.0.1:8050 en su navegador.
 * Configure y Lance el Agente:
   * Los campos se precargarán con su última configuración guardada.
   * Ajuste los parámetros según el escenario de prueba deseado (nueva ubicación de escaneo, nuevas palabras clave, cambio de método de exfiltración, etc.).
   * Haga clic en el botón "Lanzar Agente". El agente se ejecutará en segundo plano, discretamente, y comenzará sus operaciones.
 * Supervise la Actividad y Gestione el Agente:
   * Haga clic en "Actualizar Registros (cifrados localmente)" para ver la actividad del agente en tiempo real en la interfaz (descifrada por el panel de control usando la clave AES del campo).
   * Si utiliza la exfiltración HTTPS, consulte su página de webhook.site (o su C2) para verificar la recepción de los datos exfiltrados.
   * Utilice el botón "Detener Agente" para detenerlo de forma segura. Esto activará su mecanismo de limpieza (si no está desactivado en modo de depuración).
 * Descargue los Registros para Análisis:
   * El botón "Descargar Registros Crudos (cifrados)" le permite recuperar el archivo agent_logs.enc. Este archivo contiene todas las actividades del agente, cifradas. Puede descifrarlo con la clave AES de su panel de control para un análisis profundo sin conexión.
📜 Estructura del Proyecto (Repositorio de GitHub)
exfiltration_agent/
├── README.md                 # Este archivo: Documentación completa del proyecto
├── exf_agent.py              # El script principal del agente de exfiltración
├── control_panel.py          # El script de la interfaz web Dash para el control
├── modules/                  # Directorio que contiene todos los módulos internos del agente
│   ├── aes256.py             # Cifrado AES-256 GCM
│   ├── anti_evasion.py       # Técnicas anti-depuración / sandbox
│   ├── compression.py        # Compresión Zlib/Gzip
│   ├── config.py             # Gestión de argumentos de configuración
│   ├── exfiltration_dns.py   # Exfiltración a través de tunelización DNS
│   ├── exfiltration_http.py  # Exfiltración a través de HTTP/HTTPS
│   ├── file_scanner.py       # Escaneo y filtrado de archivos
│   ├── logger.py             # Registro cifrado de actividades
│   ├── payload_dropper.py    # Lanzamiento de cargas útiles secundarias
│   ├── retry_manager.py      # Gestión de reintentos y persistencia
│   ├── stealth_mode.py       # Técnicas de sigilo y limpieza
│   └── system_profiler.py    # Perfilado del sistema (sin psutil)
├── requirements.txt          # Dependencias externas de Python
├── setup_termux.sh           # Script de instalación automatizada para Termux

🤝 Contribuciones
¡Las contribuciones son bienvenidas! Si desea mejorar ip-nose, corregir errores o agregar nuevas funcionalidades, consulte nuestra Guía de Contribución.





Licencia 📜
hashish se distribuye bajo la licencia MIT License
Contacto 📧
Para cualquier pregunta o sugerencia, no dude en abrir una issue en GitHub o contactarnos por correo electrónico:
<div align="center">
<h2>🌿 exfiltration_agent - Código de Conducta 🌿</h2>
<p>
Nos comprometemos a crear un entorno acogedor y respetuoso para todos los colaboradores.
Por favor, tómese un momento para leer nuestro <a href="CODE_OF_CONDUCT.md">Código de Conducta</a>.
Al participar en este proyecto, usted acepta cumplir con sus términos.
</p>
<p>
<a href="CODE_OF_CONDUCT.md">
<img src="https://img.shields.io/badge/Code%20of%20Conduct-Por%20Favor%20Lea-blueviolet?style=for-the-badge&logo=github" alt="Código de Conducta">
</a>
</p>
</div>
<div align="center">
<h2>🐞 Informar de un Bug en exfiltration_agent 🐞</h2>
<p>
¿Encuentra un problema con exfiltration_agent? ¡Ayúdenos a mejorar el proyecto informando de los errores!
Haga clic en el botón de abajo para abrir directamente un nuevo informe de error precargado.
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=">
<img src="https://img.shields.io/badge/Informar%20un%20Bug-Abrir%20una%20Issue-red?style=for-the-badge&logo=bugsnag" alt="Informar un Bug">
</a>
</p>
</div>
<div align="center">
<h2>💬 Comunidad ip-nose - ¡Únete a la Discusión! 💬</h2>
<p>
¿Preguntas, sugerencias o ganas de discutir el proyecto ip-nose?
¡Únete a la comunidad en GitHub Discussions!
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/discussions">
<img src="https://img.shields.io/badge/Unirse%20a%20la%20Comunidad-Discusiones-blue?style=for-the-badge&logo=github" alt="Unirse a la Comunidad">
</a>
</p>
</div>
