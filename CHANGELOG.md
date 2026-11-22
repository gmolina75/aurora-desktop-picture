# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa versiones `MAJOR.MINOR.PATCH` aún no publicadas como etiquetas.

## [No publicado]

### Added

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
