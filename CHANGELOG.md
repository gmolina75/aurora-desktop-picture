# Changelog

Todos los cambios relevantes de este proyecto se documentan en este archivo.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y el proyecto usa versiones `MAJOR.MINOR.PATCH` aún no publicadas como etiquetas.

## [No publicado]

### Added

- `AGENTS.md` con instrucciones, convenciones y limitaciones conocidas para agentes de IA.
- `CHANGELOG.md` con el historial de cambios del proyecto.
- Documentación de requisitos, opciones de línea de comandos, solución de problemas y limitaciones conocidas en `README.md`.

### Fixed

- Sin correcciones de código en esta sección todavía.

### Known issues

- El arranque automático puede fallar con `ValueError: x1 must be greater than or equal to x0` si `xdpyinfo` devuelve dimensiones inválidas antes de que X11 esté listo (observado el 2026-11-22).
- En resoluciones 1920x1080 el contenido excede el alto disponible: las últimas filas quedan fuera del panel y el pie puede solaparlas.
- `install.sh` marca el archivo `.desktop` como ejecutable, lo que provoca un aviso no fatal de `systemd-xdg-autostart-generator`.

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
