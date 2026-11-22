# AGENTS.md

Instrucciones para agentes de IA (y personas) que trabajen en este repositorio.

## Propósito del proyecto

Generar un fondo de pantalla GNOME con datos reales del hardware del equipo, regenerándolo al iniciar sesión. Todo el código y la documentación están en español.

## Estructura

- `generate_wallpaper.py`: único módulo Python. Contiene tres bloques: recolección de datos (`collect_hardware()`), dibujo (`render()`) y aplicación vía `gsettings` (`set_background()`).
- `install.sh` / `actualizar.sh` / `desinstalar.sh`: scripts Bash que gestionan el arranque automático y el refresco manual.
- `README.md`: documentación de usuario.
- `CHANGELOG.md`: historial de cambios, formato *Keep a Changelog*.
- `requirements.txt`: dependencia Python (Pillow).

## Comandos útiles

```bash
# Ver los datos que se recogerían, sin dibujar:
python3 generate_wallpaper.py --print --no-set --output /tmp/prueba.png

# Regenerar y aplicar el fondo:
./actualizar.sh

# Comprobar la configuración de GNOME:
gsettings get org.gnome.desktop.background picture-uri
```

No hay suite de pruebas automatizada. Toda verificación es manual y **debe usar `--no-set`** para no cambiar el fondo del equipo de desarrollo.

## Convenciones

- Idioma: español en código, comentarios, mensajes de log, documentación y commits.
- Estilo Python: identificadores ASCII, type hints, manejo explícito de errores de sistema (los comandos externos pueden no existir).
- Los comandos externos se ejecutan con `subprocess` y timeout; si fallan, la fila correspondiente debe degradarse sin romper el programa.
- Scripts Bash: `set -euo pipefail` y rutas derivadas de `BASH_SOURCE`.
- No añadir dependencias nuevas sin actualizar `requirements.txt` y la sección «Requisitos» del README.
- Todo cambio visible para el usuario debe reflejarse en `CHANGELOG.md`; todo cambio en el uso o la configuración debe reflejarse en `README.md`.

## Restricciones

- **Nunca** commitear imágenes generadas, registros ni cachés: `.gitignore` excluye `*.png`, `*.log` y `__pycache__/`. El PNG y el log contienen hostname e IP local.
- **Nunca** ejecutar el script sin `--no-set` desde un entorno sin sesión gráfica: `gsettings` falla o aplica el fondo en la sesión equivocada.
- No eliminar ni sobrescribir `~/Pictures/hardware_wallpaper.png` ni el registro del usuario durante pruebas; usa `--output /tmp/...`.
- No cambiar la URL, el usuario ni la visibilidad del repositorio remoto sin confirmación explícita.

## Limitaciones conocidas (no corregidas)

1. `render()` no valida las dimensiones devueltas por `xdpyinfo`. Si son muy pequeñas o inválidas (condición de carrera al iniciar sesión, antes de que X11 esté listo), Pillow lanza `ValueError: x1 must be greater than or equal to x0` o `y1 ...` y el arranque falla.
2. El contenido necesita ~1468 px de alto (300 de cabecera + 12x84 de filas + 160 de pie). En 1080p el panel se recorta a 900 px, las filas se dibujan hasta `y=1304` (fuera de pantalla) y el pie en `y=902` solapa las últimas filas. La resolución de reserva 3072x1728 enmascara el problema.
3. `install.sh` aplica `chmod +x` al archivo `.desktop`; los generadores de autostart de systemd avisan de que no debe ser ejecutable.

Antes de cerrar una tarea que afirme haber arreglado estos puntos, verifica el caso con resolución 1920x1080 **y** con una resolución transitoria simulada (por ejemplo, `xdpyinfo` falso que devuelva `0x0`), además de revisar que no queden filas fuera del panel.
