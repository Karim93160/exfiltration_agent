![GitHub Gif](https://github.com/Karim93160/Dark-Web/blob/917902a43bee10adf623f50e420d0444155de532/20250620_032834.gif)
[🇫🇷 Français](https://github.com/karim93160/exfiltration_agent/blob/main/README.md) | [🇬🇧 English](https://github.com/karim93160/exfiltration_agent/blob/main/README_EN.md) | [🇪🇸 Español](https://github.com/karim93160/exfiltration_agent/blob/main/README_ES.md)
# Exfiltration-Agent:
*La Herramienta Furtiva de Exfiltración de Datos para Equipos Red*

## 🚨 Advertencia - Uso Ético Únicamente 🚨

**Esta herramienta se desarrolla y proporciona estrictamente con fines educativos, investigación en seguridad ofensiva y pruebas de penetración autorizadas (Red Team).**

Cualquier uso de Exfiltration-Agent en sistemas no autorizados es estrictamente ilegal y contrario a la ética de la ciberseguridad. Los creadores y colaboradores de este proyecto declinan toda responsabilidad por cualquier uso abusivo o malintencionado.

**Úselo de manera responsable y solo dentro de marcos legales y éticos.**

## ✨ Visión General del Proyecto

Exfiltration-Agent es una solución de ingeniería de seguridad ofensiva diseñada para simular con precisión tácticas avanzadas de exfiltración de datos. Construido para el sigilo, la robustez y la modularidad, este agente permite a los miembros del Red Team y analistas de seguridad probar proactivamente la resiliencia de sus infraestructuras.

Ya sea que su objetivo sea evaluar la detección de fugas de datos, la efectividad de los firewalls o la capacidad de sus sistemas para resistir agentes discretos, Exfiltration-Agent ofrece control granular sobre sus operaciones a través de una interfaz web intuitiva.

## ¿Por qué Exfiltration-Agent?

- **Simulación Realista**: Reproduzca escenarios complejos de exfiltración para evaluar la capacidad de su organización para detectar y prevenir fugas de datos.
- **Sigilo Integrado**: Técnicas avanzadas de ocultación de procesos, limpieza de rastros y anti-evasión para pruebas discretas y difíciles de atribuir.
- **Multi-Canal**: Utilice varios métodos de exfiltración, incluidos HTTP/HTTPS y tunneling DNS, para probar defensas multicapa y puntos ciegos.
- **Robustez Operacional**: Nunca pierda datos. El agente maneja fallas de transmisión con mecanismos de reintento inteligentes y persistencia local cifrada.
- **Facilidad de Uso**: Una interfaz web moderna e intuitiva simplifica la configuración y el control, haciendo que la herramienta sea accesible incluso en entornos limitados como Termux.
- **Modularidad**: Su arquitectura basada en módulos separados facilita la auditoría del código, su modificación y la adición de nuevas funciones.

## 🚀 Características Clave en Detalle

Exfiltration-Agent es un conjunto completo de capacidades de exfiltración, cada una diseñada para maximizar la eficiencia y la discreción.

### 🔐 Cifrado AES256

- **Confidencialidad Garantizada**: Todos los datos recopilados se cifran con el algoritmo AES-256 en modo GCM (Galois/Counter Mode) antes de la transmisión.
- **Integridad y Autenticación**: El modo GCM garantiza no solo la confidencialidad sino también la integridad y autenticidad de los datos, protegiendo contra cualquier alteración.
- **Clave Dedicada**: Se utiliza una clave AES única, configurable a través de la interfaz, garantizando la seguridad de sus exfiltraciones.

### 🗜️ Compresión Zlib/Gzip

- **Optimización de Ancho de Banda**: Los datos se comprimen con Zlib o Gzip antes del cifrado y el envío, reduciendo así el tamaño de la carga útil y el consumo de red.
- **Velocidad de Exfiltración**: Transferencias más pequeñas resultan en exfiltraciones más rápidas y menos tiempo en la red, aumentando el sigilo.

### 📁 Escaneo y Filtrado Avanzado de Archivos

- **Búsqueda Recursiva**: Escanea en profundidad los directorios especificados para descubrir archivos objetivo.
- **Filtrado Granular**:
  - **Por Extensión**: Inclusión (.doc, .txt, .db) y exclusión (.exe, .dll) de tipos de archivos específicos.
  - **Por Tamaño**: Definición de tamaños mínimos y máximos para apuntar a archivos relevantes.
  - **Por Contenido**: Búsqueda de palabras clave específicas o patrones de expresiones regulares (regex) dentro de los archivos para identificar datos sensibles.

### 💻 Perfilado del Sistema (sin psutil)

- **Reconocimiento Profundo**: Recopila información vital sobre el entorno comprometido sin dependencias externas complejas.
- **Información Recopilada**:
  - Nombre de host y detalles del sistema operativo.
  - Información de CPU y memoria.
  - Información de particiones de disco.
  - Detalles de interfaces de red (direcciones IP, servidores DNS).
  - Usuarios conectados y procesos en ejecución.
- **Robustez**: Utiliza comandos nativos de shell (df, ip, ps, who, cat /proc/...) para garantizar la máxima compatibilidad en sistemas heterogéneos (incluido Termux).

### 🧬 Anti-Debug / Sandbox & Evasión

- **Detección de Entornos Hostiles**: El agente intenta identificar si se está ejecutando en un entorno de análisis, como un depurador, máquina virtual o contenedor.
- **Estrategias de Evasión**:
  - Verificación de procesos padres sospechosos.
  - Análisis del tiempo de actividad del sistema (tiempo de ejecución corto = sandbox).
  - Verificación de proporciones de espacio en disco.
  - Búsqueda de artefactos específicos de VM/contenedores.
  - Verificación de ptrace (detección de depurador en Linux).
  - Análisis de indicadores de virtualización en las banderas de la CPU.
- **Comportamiento Adaptativo**: Si se detecta un entorno sospechoso, el agente puede apagarse silenciosamente o alterar su comportamiento para evitar el análisis.

### 🌐 Exfiltración HTTP/HTTPS

- **Canal Principal**: La forma más común y a menudo más efectiva de transferir datos.
- **Sigilo de Red**: Utiliza la biblioteca requests con User-Agents aleatorios y encabezados HTTP realistas para enmascarar el tráfico de exfiltración entre el tráfico web normal.
- **Manejo Robusto**: Incluye manejo de timeouts, errores de conexión y respuestas HTTP.

### 📡 Exfiltración DNS

- **Canal Furtivo Avanzado**: Un método de exfiltración a menudo subestimado, ya que el tráfico DNS rara vez se inspecciona en profundidad.
- **Tunelamiento Inteligente**: Los datos binarios (cifrados y comprimidos) se codifican en Base32 o Hexadecimal, luego se dividen en pequeños "chunks" enviados como subdominios en consultas DNS (Tipo A).
- **Fiabilidad**: Incluye IDs de transacción e índices de chunk para permitir que el servidor de control reensamble los datos correctamente.

### 🔄 Gestor de Reintentos/Rotación

- **Persistencia de Datos**: Si un intento de exfiltración falla (problema de red, servidor inaccesible), los datos no se pierden.
- **Reintentos Inteligentes**: Los datos se ponen en cola y se realizan intentos de reenvío con retroceso exponencial (aumento del retraso entre intentos) para evitar saturar la red o el C2.
- **Registro Local Cifrado**: Los datos que persisten en la cola se guardan en un archivo local cifrado, garantizando su seguridad incluso en la máquina comprometida.

### 🕵️ Modo Sigilo

- **Ocultación de Procesos**: Intenta modificar el nombre del proceso visible para mezclarse con procesos legítimos del sistema.
- **Directorio de Trabajo Temporal**: Utiliza rutas efímeras (/tmp o equivalente de Termux) para almacenar archivos temporales, evitando rastros persistentes.
- **Auto-Eliminación de Registros y Archivos**: Al final de la operación (a menos que se desactive en modo debug), el agente limpia activamente todos los registros cifrados y archivos temporales que creó.
- **Timestomping**: Altera las marcas de tiempo de archivos creados o modificados para ocultar la actividad reciente del agente.

### 🔁 Hilos/Tareas Asíncronas

- **Rendimiento Óptimo**: El agente está diseñado con una arquitectura multi-hilo.
- **Operaciones Simultáneas**: El escaneo de archivos y el proceso de exfiltración/reintento se ejecutan en paralelo, maximizando la eficiencia y la velocidad sin bloquear el agente.
- **Comunicación Segura**: Utiliza colas seguras para hilos para una comunicación confiable entre los diferentes hilos.

### 🧊 Payload Dropper

- **Despliegue Post-Exfiltración**: Permite al agente descargar y colocar un ejecutable secundario (RAT, shell, otro malware simulado) en la máquina objetivo después de una exfiltración exitosa o según un criterio.
- **Flexibilidad**: Facilita la extensión de las operaciones en el objetivo.
- **Habilitación de Ejecución**: Opción para establecer permisos de ejecución en el archivo colocado.

### 📊 Registrador/Telemetría

- **Auditoría Furtiva**: Todas las actividades del agente se registran localmente en un archivo dedicado.
- **Cifrado de Registros**: El archivo de registro en sí está cifrado con AES256 para mantener la discreción.
- **Análisis Post-Operacional**: El panel de control web permite leer, descifrar y mostrar estos registros, ofreciendo visibilidad completa sobre el progreso de la operación.

## 🛠️ Instalación y Uso (Guía Completa)

Esta guía está optimizada para entornos Termux (Android).

### Requisitos Previos

- Un dispositivo Android con Termux instalado.
- Una conexión a Internet activa.
- (Opcional pero altamente recomendado) Una cuenta en webhook.site para probar fácilmente la exfiltración HTTP/HTTPS, o un servidor C2 que controle.

### Pasos de Instalación Automatizados

1. Abra Termux en su dispositivo Android.
2. Clone el repositorio de GitHub:
   ```bash
   git clone https://github.com/Karim93160/exfiltration_agent
   ```
3. Ejecute el script de instalación todo-en-uno:
   ```bash
   cd exfiltration_agent
chmod +x setup_termux.sh exf_agent.py control_panel.py
./setup_termux.sh

   ```
   - El script instalará todos los paquetes necesarios de Termux (Python, clang, build-essential, iproute2, procps, coreutils, etc.) y todas las dependencias de Python requeridas (pycryptodome, requests, dnspython).
   - Lanzará automáticamente el panel de control web en segundo plano (`nohup python -u control_panel.py ... &`). Verá un mensaje `nohup: ignoring input` y el PID del proceso.

### Acceso Inicial y Configuración a través del Panel de Control Web

El panel de control es su interfaz gráfica completa para gestionar el agente.

1. **Acceda al Panel de Control**:
   Abra el navegador web de su dispositivo Android e ingrese la dirección:
   ```
   http://127.0.0.1:8050
   ```
   *(Si el puerto 8050 ya está en uso, aparecerá un mensaje de error en la terminal de Termux. Deberá modificar la línea `port=8050` en el archivo `control_panel.py` a otro puerto, como 8051, y luego reiniciar el script.)*

2. **Primera Configuración**:
   - En la primera apertura (después de la generación por `setup_termux.sh`), la interfaz mostrará una clave AES generada automáticamente en el campo "Clave AES".
   - **Acción Crucial**: En el campo "Objetivo de Exfiltración (URL o IP:Puerto)", reemplace la URL predeterminada con su URL única de webhook.site o la dirección de su propio servidor de control C2. Aquí es donde el agente enviará los datos.
   - Todos los demás campos (ruta de escaneo, tipos de archivos, etc.) estarán pre-llenados con valores predeterminados inteligentes (`/data/data/com.termux/files/home/storage/shared` es un buen punto de partida para el almacenamiento interno de Android).

3. **Guarde su Configuración**:
   Una vez que haya personalizado las opciones, haga clic en el botón "Guardar Configuración". Esto guardará todas las configuraciones que haya definido en el archivo `~/exfiltrationagent/sharedconfig.json`. De esta manera, la próxima vez que abra el panel, sus preferencias se cargarán automáticamente.

### Uso Diario del Agente a través de la Interfaz Web

Después de la configuración inicial, el uso es muy simple:

1. **Inicie el Panel de Control (si no está ya en ejecución)**:
   Si ha cerrado Termux o detenido el panel, reinícielo desde el directorio del agente:
   ```bash
   cd ~/exfiltration_agent
   nohup python -u controlpanel.py > controlpanel.log 2>&1 &
   ```
   Luego acceda nuevamente a `http://127.0.0.1:8050` en su navegador.

2. **Configure y Lance el Agente**:
   - Los campos estarán pre-llenados con su última configuración guardada.
   - Ajuste la configuración según el escenario de prueba deseado (nueva ubicación de escaneo, nuevas palabras clave, cambio de método de exfiltración, etc.).
   - Haga clic en el botón "Iniciar Agente". El agente se ejecutará en segundo plano, discretamente, y comenzará sus operaciones.

3. **Monitoree la Actividad y Gestione el Agente**:
   - Haga clic en "Actualizar Registros (localmente cifrados)" para ver la actividad del agente en tiempo real en la interfaz (descifrada por el panel de control usando la clave AES del campo).
   - Si utiliza la exfiltración HTTPS, consulte su página de webhook.site (o su C2) para verificar la recepción de los datos exfiltrados.
   - Utilice el botón "Detener Agente" para detenerlo limpiamente. Esto activará su mecanismo de limpieza (a menos que se desactive en modo debug).

4. **Descargue Registros para Análisis**:
   - El botón "Descargar Registros Crudos (cifrados)" le permite recuperar el archivo `agent_logs.enc`. Este archivo contiene todas las actividades del agente, cifradas. Puede descifrarlo con la clave AES de su panel de control para un análisis en profundidad sin conexión.

## 📜 Estructura del Proyecto (Repositorio GitHub)

```
exfiltration_agent/
├── README.md                 # Este archivo: Documentación completa del proyecto
├── exf_agent.py              # El script principal del agente de exfiltración
├── control_panel.py          # El script de la interfaz web Dash para el control
├── modules/                  # Directorio que contiene todos los módulos internos del agente
│   ├── aes256.py             # Cifrado AES-256 GCM
│   ├── anti_evasion.py       # Técnicas anti-debugging / sandbox
│   ├── compression.py        # Compresión Zlib/Gzip
│   ├── config.py             # Gestión de argumentos de configuración
│   ├── exfiltration_dns.py   # Exfiltración mediante tunneling DNS
│   ├── exfiltration_http.py  # Exfiltración mediante HTTP/HTTPS
│   ├── file_scanner.py       # Escaneo y filtrado de archivos
│   ├── logger.py             # Registro cifrado de actividades
│   ├── payload_dropper.py    # Colocación de payloads secundarios
│   ├── retry_manager.py      # Gestión de reintentos y persistencia
│   ├── stealth_mode.py       # Técnicas de sigilo y limpieza
│   └── system_profiler.py    # Perfilado del sistema (sin psutil)
├── requirements.txt          # Dependencias externas de Python
├── setup_termux.sh           # Script de instalación automatizado para Termux
└── backup_agent.sh           # Script para crear copias de seguridad del proyecto
```

## 🤝 Contribuciones y Soporte

¡Las contribuciones son bienvenidas! Si tiene ideas de mejora, informes de errores o sugerencias, por favor:

- **Abra un Issue**: Para reportar un error o sugerir una nueva característica.
- **Envíe un Pull Request**: Para proponer cambios o adiciones de código.

¡Su ayuda es valiosa para hacer evolucionar Exfiltration-Agent!

## 🛡️ Licencia

Este proyecto se distribuye bajo la Licencia MIT. Esto significa que es libre de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del Software, sujeto a los términos establecidos en la licencia.

**Licencia MIT**

<div align="center">
<h2>🌿 Exfiltration-Agent - Código de Conducta 🌿</h2>
<p>
Estamos comprometidos a crear un ambiente acogedor y respetuoso para todos los contribuyentes.
Por favor, tómese un momento para leer nuestro <a href="CODIGO_DE_CONDUCTA.md">Código de Conducta</a>.
Al participar en este proyecto, usted acepta cumplir con sus términos.
</p>
<p>
<a href="CODIGO_DE_CONDUCTA.md">
<img src="https://img.shields.io/badge/C%C3%B3digo%20de%20Conducta-Lea%20Por%20Favor-blueviolet?style=for-the-badge&logo=github" alt="Código de Conducta">
</a>
</p>
</div>

<div align="center">
<h2>🐞 Reportar un Error en Exfiltration-Agent 🐞</h2>
<p>
¿Encontró un problema con Exfiltration-Agent? ¡Ayúdenos a mejorar el proyecto reportando errores!
Haga clic en el botón de abajo para abrir directamente un nuevo informe de error pre-llenado.
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=">
<img src="https://img.shields.io/badge/Reportar%20Error-Abrir%20un%20Issue-red?style=for-the-badge&logo=bugsnag" alt="Reportar un Error">
</a>
</p>
</div>

<div align="center">
<h2>💬 Comunidad de Exfiltration-Agent - ¡Únase a la Discusión! 💬</h2>
<p>
¿Preguntas, sugerencias o quiere discutir el proyecto Exfiltration-Agent?
¡Únase a la comunidad en GitHub Discussions!
</p>
<p>
<a href="https://github.com/karim93160/exfiltration_agent/discussions">
<img src="https://img.shields.io/badge/Unirse%20a%20la%20Comunidad-Discusiones-blue?style=for-the-badge&logo=github" alt="Unirse a la Comunidad">
</a>
</p>
</div>
```
