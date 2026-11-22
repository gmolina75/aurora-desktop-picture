# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa versiones `MAJOR.MINOR.PATCH` aún no publicadas como etiquetas.

## [0.7.1] - 2026-11-22

### Fixed

- Linux puede reutilizar una captura de tipo y velocidad de RAM cuando la sesión gráfica no tiene acceso a SMBIOS.

## [0.7.0] - 2026-11-22

### Added

- Windows muestra el modelo comercial del procesador y la frecuencia disponible.
- La fila Almacenamiento se resalta en amarillo cuando queda menos del 10 % de espacio libre.

## [0.6.0] - 2026-11-22

### Added

- Linux muestra el tipo de disco que respalda el sistema de archivos raíz.

## [0.5.0] - 2026-11-22

### Added

- En Linux, la tarjeta muestra el tipo de RAM y su velocidad si los datos SMBIOS están disponibles.

## [0.4.5] - 2026-11-22

### Fixed

- En Linux, la fila Red muestra la interfaz de salida en lugar del modelo de un adaptador Wi-Fi que puede estar apagado.

## [0.4.4] - 2026-11-22

### Fixed

- Se aplica el fondo con el esquema de Cinnamon en Linux Mint y se conserva la selección de tema claro y oscuro en GNOME cuando está disponible.

## [0.4.3] - 2026-11-22

### Added

- GitHub Actions verifica las pruebas, los scripts y la generación del PNG en Windows y Ubuntu.

## [0.4.2] - 2026-11-22

### Added

- Actualizadores para Windows y Linux que descargan la versión de GitHub y regeneran el fondo.

## [0.4.1] - 2026-11-22

### Changed

- Se reducen un 20 % el ancho y el alto de la tarjeta, conservando su anclaje inferior derecho.

## [0.4.0] - 2026-11-22

### Added

- Configuración de la imagen predeterminada mediante `AURORA_FONDO` en `.env`.

### Changed

- Aurora usa un fondo negro cuando no hay una imagen disponible.

## [0.3.0] - 2026-11-22

### Added

- Opción `--fondo` para dibujar la tarjeta sobre una imagen elegida por el usuario.

## [0.2.15] - 2026-11-22

### Added

- Instalador de PowerShell que descarga el proyecto desde GitHub y prepara Python y Pillow en Windows.

## [0.2.14] - 2026-11-22

### Fixed

- La instalación en Windows usa `instalar.bat` y admite equipos con `python` sin el lanzador `py`.

## [0.2.13] - 2026-11-22

### Changed

- El README incluye los comandos para instalar desde GitHub en Windows y en Ubuntu o Debian con GNOME.

## [0.2.12] - 2026-11-22

### Changed

- Se añaden 20 px de separación entre la tarjeta y el borde inferior del fondo.

## [0.2.11] - 2026-11-22

### Changed

- Una franja adicional de 40 px separa la tarjeta del borde derecho de la imagen.

## [0.2.10] - 2026-11-22

### Changed

- La tarjeta muestra la versión del script en letra pequeña junto a «Actualizado».

## [0.2.9] - 2026-11-22

### Changed

- Se ensancha la tarjeta hacia la izquierda para dar más espacio al texto.

## [0.2.8] - 2026-11-22

### Changed

- El margen interior derecho de la tarjeta aumenta al 8 % de su ancho, con un mínimo de 20 px.

## [0.2.7] - 2026-11-22

### Changed

- Se amplía el margen interior derecho de la tarjeta.

## [0.2.6] - 2026-11-22

### Fixed

- Windows detecta el fabricante y el modelo del equipo a partir de la información del BIOS.

## [0.2.5] - 2026-11-22

### Added

- `actualizar.bat` para aplicar el fondo desde el Explorador de Windows.

## [0.2.4] - 2026-11-22

### Added

- Aplicación directa del fondo en Windows desde el script.

### Changed

- Tarjeta semitransparente con más margen interior y aproximadamente un 25 % menos de ancho y alto.

## [0.2.3] - 2026-11-22

### Changed

- Los datos se muestran sin título ni pie de página, dentro del cuarto inferior derecho del fondo.

## [0.2.2] - 2026-11-22

### Fixed

- Windows muestra la RAM física utilizable y la interfaz de red correspondiente a la IPv4 local.

## [0.2.1] - 2026-11-22

### Changed

- En Windows, el PNG se guarda por defecto en la carpeta Documentos configurada para el usuario.

### Fixed

- La generación de imágenes en Windows utiliza fuentes del sistema.

## [0.2.0] - 2026-11-22

### Added

- Opción `--version` para consultar la versión y su fecha sin generar una imagen ni aplicar el fondo.
- `AGENTS.md` con instrucciones, convenciones y estado de los problemas históricos para agentes de IA.
- `CHANGELOG.md` con el historial de cambios del proyecto.
- `tests/test_wallpaper.py`: 7 pruebas `unittest` de resolución, layout y dibujo (`python3 -m unittest discover -s tests -v`).
- Opción `--wait-display SEGUNDOS` para reintentar la detección de resolución durante el arranque.
- `README.md`: requisitos detallados, opciones de línea de comandos, sección de pruebas, solución de problemas y limitaciones actuales.

### Changed

- `--print` ahora muestra los datos y termina sin generar imagen ni modificar el fondo (antes también dibujaba y aplicaba el fondo).
- El degradado de fondo se genera con operaciones de `ImageChops` en lugar de un bucle por píxel: de varios segundos a ~0,3 s en 1920x1080.
- `install.sh` instala el arranque automático con `--wait-display 20` y permisos `644` en el archivo `.desktop`.
- El diseño del panel escala cabecera, alto de fila, pie y tamaños de fuente al alto real de la pantalla; el texto largo se recorta con `…` en lugar de desbordarse.
- La resolución de reserva pasa de 3072x1728 a 1920x1080.
- Se eliminó la etiqueta `(integrada)` añadida automáticamente a las GPU Intel, que podía ser incorrecta.

### Fixed

- Arranque automático fallido con `ValueError: x1 must be greater than or equal to x0` o `y1 ...`: las dimensiones externas ahora se validan (640x480 a 16384x16384), se prueban varias fuentes (`xdpyinfo`, `xrandr`, `wlr-randr`), se reintentan con `--wait-display` y se usa un fallback seguro.
- Contenido fuera de pantalla en 1080p: las 12 filas, la cabecera y el pie caben ahora en resoluciones desde 800x600 hasta 3072x1728, verificado por pruebas.
- Aviso no fatal de `systemd-xdg-autostart-generator` por el `.desktop` ejecutable.
- `gsettings` ausente: se registra un aviso en lugar de fallar.

## [0.1.0] - 2026-11-18

### Added

- `generate_wallpaper.py`: recolección de datos del hardware (equipo, hostname, CPU, RAM, GPU, disco, red, IP, SO y kernel) desde `/proc`, `/sys`, `lspci`, `lscpu` y `/etc/os-release`.
- Generación del fondo PNG con Pillow, gradiente, panel y texto adaptado a la resolución detectada.
- Aplicación del fondo en GNOME para los temas claro y oscuro en modo `zoom` mediante `gsettings`.
- Opciones `--output`, `--no-set`, `--log` y `--print`.
- Registro de ejecución en `~/.local/share/aurora-desktop-picture/last-run.log`.
- `install.sh`, `actualizar.sh` y `desinstalar.sh` para el arranque automático y el refresco manual.
- `requirements.txt` con la dependencia Pillow.
- `README.md` inicial y `.gitignore`.
