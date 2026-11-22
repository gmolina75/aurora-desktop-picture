# Aurora Desktop Picture

Fondo de pantalla que muestra las **especificaciones reales del equipo**, leídas directamente del sistema cada vez que inicias sesión.

Genera una imagen PNG con los datos del equipo y la aplica como fondo en Windows, GNOME o Cinnamon.

## Versión

La tarjeta muestra la versión del script en letra pequeña junto a «Actualizado». Consulta la versión instalada y su fecha con `python3 generate_wallpaper.py --version`.

## Qué hace

1. Recoge los datos del hardware (`/proc`, `/sys`, `lspci`, `lscpu`, `/etc/os-release`), incluidos el **nombre del equipo** (hostname) y su **dirección IP** local.
2. Dibuja una imagen PNG con la resolución real de la pantalla, usando Pillow.
3. Guarda `hardware_wallpaper.png` en la carpeta Documentos del usuario en Windows y en `~/Pictures` en Linux. Usa `--output` para elegir otra ruta.
4. Aplica la imagen como fondo en Windows, GNOME o Cinnamon.
5. Escribe un registro en `~/.local/share/aurora-desktop-picture/last-run.log`.

Los datos se muestran en un panel compacto y semitransparente en el cuarto inferior derecho, sin título, para dejar libre el resto del escritorio. La imagen incluye una línea **«Actualizado: fecha y hora»** para que puedas comprobar que se refresca sola.

> **Privacidad:** el fondo muestra el hostname y la IP local, y el registro guarda las rutas y errores. No compartas el PNG ni el log sin revisarlos antes.

En Linux, la fila **Red** muestra la interfaz que el sistema elige para salir a la red.

En Linux, **Memoria RAM** añade el tipo y la velocidad cuando los datos SMBIOS están disponibles. Si `dmidecode` requiere permisos de administrador, captura estos datos una vez desde tu sesión de usuario:

```bash
mkdir -p "$HOME/.local/share/aurora-desktop-picture"
datos=$(sudo dmidecode --type 17) && printf '%s\n' "$datos" | grep -E '^Memory Device$|^[[:space:]]+(Size|Type|Speed|Configured Memory Speed|Configured Clock Speed):' > "$HOME/.local/share/aurora-desktop-picture/ram.txt"
bash actualizar.sh
```

En Ubuntu o Mint, si falta el comando, instálalo con `sudo apt install dmidecode`. Repite la captura si cambias la RAM. El archivo guarda los campos de capacidad, tipo y velocidad. Las actualizaciones del fondo se ejecutan con tu usuario habitual.

En Linux, **Almacenamiento** indica HDD, SSD, SSD SATA o SSD NVMe cuando el sistema permite identificar el dispositivo que respalda la raíz `/`. Si no se identifica, se conservan las cifras de espacio.

## Requisitos

- Linux con Cinnamon (Linux Mint) o GNOME (probado en Ubuntu 26.04, sesión Wayland con XWayland).
- Python 3.10 o superior.
- Pillow 9 o superior.
- Herramientas opcionales que mejoran los datos mostrados: `lspci` (paquete `pciutils`) y `lscpu` (paquete `util-linux`). Si faltan, el script degrada aisladamente esas filas.
- `xdpyinfo` (paquete `x11-utils`), `xrandr` o `wlr-randr` para detectar la resolución. Si ninguno devuelve un valor válido se usa la resolución segura de reserva 1920x1080.
- `gsettings` para aplicar el fondo.

## Instalación desde GitHub

### Windows (PowerShell)

Abre PowerShell en tu sesión de escritorio y ejecuta:

```powershell
$instalador = Join-Path $env:TEMP 'aurora-instalar-windows.ps1'
Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/gmolina75/aurora-desktop-picture/master/instalar-windows.ps1' -OutFile $instalador
powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File $instalador
```

El instalador descarga el proyecto desde GitHub, reutiliza Python compatible si está disponible o lo instala desde python.org, instala Pillow y aplica el fondo. Los archivos quedan en `%LOCALAPPDATA%\AuroraDesktopPicture\proyecto`. Ejecuta el mismo bloque para actualizar la instalación. Para generar la imagen sin cambiar el fondo, añade `-NoAplicar` a la última línea.

### Ubuntu o Debian con GNOME y Linux Mint con Cinnamon

```bash
sudo apt update
sudo apt install git python3 python3-pil fonts-dejavu-core libglib2.0-bin x11-utils pciutils
git clone --branch master https://github.com/gmolina75/aurora-desktop-picture.git
cd aurora-desktop-picture
bash install.sh
```

`install.sh` crea este archivo:

```
~/.config/autostart/aurora-desktop-picture.desktop
```

Gracias a él, el escritorio ejecuta el script **automáticamente al iniciar sesión**. Para que el cambio surta efecto, cierra sesión y vuelve a entrar una vez.

## Actualizar desde GitHub

En Windows, desde la carpeta del proyecto:

```powershell
.\actualizar-github.bat
```

El BAT actualiza el clon en la rama `master` si se instaló con Git. Si se instaló con PowerShell, descarga la versión nueva en `%LOCALAPPDATA%\AuroraDesktopPicture\proyecto`.

En Linux, desde el clon y dentro de tu sesión de escritorio:

```bash
bash actualizar-github.sh
```

Ambos actualizadores regeneran el fondo y conservan `.env`. Los scripts `actualizar.bat` y `actualizar.sh` siguen sirviendo para regenerar el fondo con la versión instalada.

## Usar una imagen propia como fondo

Copia `.env.example` como `.env` junto a `generate_wallpaper.py` y guarda allí tu imagen predeterminada:

```dotenv
AURORA_FONDO="C:\Fotos\mi-fondo.jpg"
```

Las rutas relativas se resuelven desde la carpeta del script. Si el valor está vacío o la imagen no existe, el fondo será negro. Usa `--fondo` para elegir otra imagen en una ejecución puntual.

En Windows, desde la carpeta del proyecto:

```powershell
.\actualizar.bat --fondo "C:\Fotos\mi-fondo.jpg"
```

En Linux con GNOME o Cinnamon:

```bash
python3 generate_wallpaper.py --fondo "$HOME/Pictures/mi-fondo.jpg"
```

Aurora adapta la foto al tamaño del escritorio con un recorte centrado y dibuja la tarjeta encima. La foto original se conserva. Usa `--no-set` para generar una vista previa sin aplicar el fondo.

## Estructura

```
aurora-desktop-picture/
├── generate_wallpaper.py   # script principal: recolección, dibujo y aplicación
├── install.sh              # instala el arranque automático
├── actualizar.sh           # refresco manual
├── desinstalar.sh          # quita el arranque automático
├── requirements.txt        # dependencia Python (Pillow)
├── tests/                  # pruebas unitarias (unittest)
├── AGENTS.md               # instrucciones para agentes de IA que trabajen aquí
├── CHANGELOG.md            # historial de cambios
├── README.md               # esta documentación
└── .gitignore
```

## Uso manual

```bash
./actualizar.sh                                   # regenera y aplica el fondo
python3 generate_wallpaper.py --print             # solo muestra los datos detectados y termina
python3 generate_wallpaper.py --no-set            # crea la imagen sin cambiar el fondo
python3 generate_wallpaper.py --output /tmp/prueba.png
python3 generate_wallpaper.py --log /tmp/prueba.log
python3 generate_wallpaper.py --wait-display 20   # espera a que X11 esté listo (lo usa install.sh)
```

Opciones disponibles:

| Opción | Descripción |
| --- | --- |
| `--fondo RUTA` | Imagen base para dibujar la tarjeta. |
| `--output RUTA` | Ruta del PNG generado (por defecto `~/Pictures/hardware_wallpaper.png`). |
| `--no-set` | No modifica `gsettings`; útil para probar sin tocar el fondo actual. |
| `--log RUTA` | Añade los mensajes a un archivo de registro. |
| `--print` | Imprime las filas de datos detectados por stdout y termina sin generar imagen ni tocar el fondo. |
| `--wait-display SEGUNDOS` | Reintenta la detección de resolución durante ese tiempo; útil en el arranque, antes de que X11 esté disponible. |

El programa devuelve `0` si todo salió bien y `1` si hubo un error; el error también se escribe en el registro si se indicó `--log`.

## Pruebas

```bash
python3 -m unittest discover -s tests -v
```

Comprueban el parsing de resoluciones, el fallback, que el panel y las fuentes caben en varias resoluciones y el recorte de texto. No modifican el fondo ni escriben en `~/Pictures`.

## Comprobar que funciona

```bash
cat ~/.local/share/aurora-desktop-picture/last-run.log
gsettings get org.gnome.desktop.background picture-uri
gsettings get org.gnome.desktop.background picture-uri-dark
gsettings get org.gnome.desktop.background picture-options
```

La fecha de la última línea del registro debería coincidir con el último inicio de sesión, y la URI debería apuntar a `~/Pictures/hardware_wallpaper.png` con `picture-options` en `'zoom'`.

En Linux Mint con Cinnamon, consulta el fondo activo con:

```bash
gsettings get org.cinnamon.desktop.background picture-uri
```

## Desinstalar

```bash
./desinstalar.sh
```

Elimina solo el arranque automático; la imagen y el registro se conservan. Para volver al fondo por defecto de Ubuntu:

```bash
gsettings reset org.gnome.desktop.background picture-uri
gsettings reset org.gnome.desktop.background picture-uri-dark
gsettings reset org.gnome.desktop.background picture-options
```

## Personalización

Edita `generate_wallpaper.py`:

- Colores: constantes `c0` / `c1` (fondo) y los valores RGBA de `d.text(...)`.
- Tamaños: `header_h`, `row_h`, `footer_h` en `render()`.
- Fuentes: variables `F_MONO`, `F_MONO_B`, `F_SANS_B`.
- Texto/cabecera: cadenas dentro de `render()` y `collect_hardware()`.

Tras cualquier cambio, comprueba primero con `python3 -m unittest discover -s tests -v` y después con `python3 generate_wallpaper.py --no-set --output /tmp/prueba.png`.

## Solución de problemas

| Síntoma | Causa probable | Acción |
| --- | --- | --- |
| El fondo no se actualiza al iniciar sesión | El arranque automático se lanzó antes de que la pantalla estuviera disponible. | El instalador ya pasa `--wait-display 20`. Revisa el registro; ejecuta `./actualizar.sh` una vez iniciada la sesión. |
| `Aviso: no se pudo detectar una resolución válida` | Ninguna herramienta de resolución respondió; se usa 1920x1080. | Instala `x11-utils`. Si el fondo no se ve bien, indica tu resolución al reportar el caso. |
| `No se pudo aplicar … picture-uri` | `gsettings` sin acceso a la sesión gráfica (por ejemplo, desde SSH o cron). | Ejecuta el script dentro de la sesión de usuario. |
| Aparece un aviso de `systemd-xdg-autostart-generator` | El `.desktop` quedó ejecutable de una instalación anterior. | Vuelve a ejecutar `./install.sh`: ahora se instala con permisos `644`. |
| El texto se ve muy pequeño | La fuente se escala automáticamente para que quepan las 12 filas en pantallas bajas. | Ajusta los multiplicadores en `compute_layout()` si prefieres otro equilibrio. |

## Limitaciones conocidas

- La detección depende de XWayland/X11 o `wlr-randr`; en sesiones Wayland sin XWayland puede caerse al valor de reserva 1920x1080.
- El diseño escala fuentes y alturas para que todo quepa, pero en pantallas muy bajas (por debajo de 640x480) no se genera la imagen: se considera una resolución inválida.

## Integración continua

GitHub Actions ejecuta las pruebas en Windows y Ubuntu con Python 3.13 al subir cambios a `master` y al abrir o actualizar una solicitud de cambios hacia esa rama. También verifica los scripts y genera un PNG de prueba con `--no-set`. La comprobación del fondo en una sesión de escritorio, incluida una sesión RDP, se hace manualmente.

## Desarrollo

Consulta `AGENTS.md` para las convenciones del proyecto y `CHANGELOG.md` para el historial de cambios. Los archivos generados (`*.png`, `*.log`, `__pycache__`) están excluidos por `.gitignore` y no deben subirse al repositorio.

## Licencia

Sin licencia declarada actualmente. Añade un archivo `LICENSE` si deseas publicar el proyecto bajo términos concretos.
