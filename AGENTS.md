# AGENTS.md

Instrucciones para agentes de IA (y personas) que trabajen en este repositorio.

## Propósito del proyecto

Generar un fondo de pantalla GNOME con datos reales del hardware del equipo, regenerándolo al iniciar sesión. Todo el código y la documentación están en español.

## Estructura

- `generate_wallpaper.py`: único módulo Python. Bloques principales: recolección (`collect_hardware()`), resolución y layout (`detect_screen_size()`, `compute_layout()`), dibujo (`make_gradient()`, `render()`) y aplicación vía `gsettings` (`set_background()`).
- `install.sh` / `actualizar.sh` / `desinstalar.sh`: scripts Bash que gestionan el arranque automático y el refresco manual.
- `tests/test_wallpaper.py`: pruebas `unittest` de resolución, layout y dibujo.
- `README.md`: documentación de usuario.
- `CHANGELOG.md`: historial de cambios, formato *Keep a Changelog*.
- `requirements.txt`: dependencia Python (Pillow).

## Comandos útiles

```bash
# Pruebas (no tocan el fondo ni ~/Pictures):
python3 -m unittest discover -s tests -v

# Ver los datos que se recogerían, sin dibujar ni aplicar nada:
python3 generate_wallpaper.py --print

# Generar una imagen de prueba sin cambiar el fondo:
python3 generate_wallpaper.py --no-set --output /tmp/prueba.png

# Regenerar y aplicar el fondo:
./actualizar.sh

# Comprobar la configuración de GNOME:
gsettings get org.gnome.desktop.background picture-uri
```

La verificación manual **debe usar `--no-set`** para no cambiar el fondo del equipo de desarrollo. Para simular una resolución ajena, usa un `xdpyinfo` falso en `PATH` que imprima `dimensions: ANCHOxALTO`.

## Versionado

- Cada cambio del proyecto debe incrementar la versión en `generate_wallpaper.py` y actualizar su fecha, incluso si el cambio es pequeño.
- Usa `PATCH` para correcciones, `MINOR` para funcionalidades compatibles y `MAJOR` para cambios incompatibles. Registra cada versión y su fecha en `CHANGELOG.md`.
- Comprueba que `python3 generate_wallpaper.py --version` devuelve la versión y la fecha registradas.

## Convenciones

- Idioma: español en código, comentarios, mensajes de log, documentación y commits.
- Estilo Python: identificadores ASCII, type hints, manejo explícito de errores de sistema (los comandos externos pueden no existir).
- Los comandos externos se ejecutan con `subprocess` y timeout; si fallan, la fila correspondiente debe degradarse sin romper el programa.
- Scripts Bash: `set -euo pipefail` y rutas derivadas de `BASH_SOURCE`.
- Toda resolución devuelta por una herramienta externa debe pasar por `valid_size()` antes de dibujar. Nunca dibujes con anchos o altos sin validar.
- `compute_layout()` debe seguir garantizando que cabecera, filas y pie quedan dentro del panel; cualquier cambio de fuentes o márgenes requiere ejecutar las pruebas.
- No añadir dependencias nuevas sin actualizar `requirements.txt` y la sección «Requisitos» del README.
- Todo cambio visible para el usuario debe reflejarse en `CHANGELOG.md`; todo cambio en el uso o la configuración debe reflejarse en `README.md`.

## Restricciones

- **Nunca** commitear imágenes generadas, registros ni cachés: `.gitignore` excluye `*.png`, `*.log` y `__pycache__/`. El PNG y el log contienen hostname e IP local.
- **Nunca** ejecutar el script sin `--no-set` desde un entorno sin sesión gráfica: `gsettings` falla o aplica el fondo en la sesión equivocada.
- No eliminar ni sobrescribir `~/Pictures/hardware_wallpaper.png` ni el registro del usuario durante pruebas; usa `--output /tmp/...`.
- El archivo `.desktop` se instala con permisos `644`: no le añadas el bit ejecutable.
- No cambiar la URL, el usuario ni la visibilidad del repositorio remoto sin confirmación explícita.

## Estado de los problemas históricos (ya corregidos)

1. **Resolución inválida en el arranque:** `detect_screen_size()` valida valores (640x480 a 16384x16384), prueba `xdpyinfo`, `xrandr` y `wlr-randr`, reintenta con `--wait-display` y cae a 1920x1080. Ya no se producen los `ValueError: x1/y1 ...`.
2. **Contenido que no cabía en 1080p:** `compute_layout()` escala cabecera, alto de fila, pie y fuentes al alto real; el texto se recorta con `…` si no cabe. Las pruebas comprueban 800x600, 1366x768, 1920x1080, 2560x1440 y 3072x1728.
3. **Aviso de `systemd`:** `install.sh` usa `chmod 644` en el `.desktop`.
4. **Dibujo lento:** el degradado se genera con `ImageChops` en lugar de un bucle por píxel (de varios segundos a ~0,3 s).

Antes de dar por terminado un cambio en estas zonas, ejecuta las pruebas y comprueba al menos 1920x1080 y una resolución inválida simulada (`0x0`), confirmando que se usa el fallback y que no queda texto fuera del panel.
