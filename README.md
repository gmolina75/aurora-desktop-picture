# Aurora Desktop Picture

Fondo de pantalla que muestra las **especificaciones reales del equipo**, leídas directamente del sistema cada vez que inicias sesión.

Pensado para equipos Ubuntu/GNOME: genera una imagen PNG con la resolución de la pantalla y la aplica como fondo en los temas claro y oscuro.

## Qué hace

1. Recoge los datos del hardware (`/proc`, `/sys`, `lspci`, `lscpu`, `/etc/os-release`), incluidos el **nombre del equipo** (hostname) y su **dirección IP** local.
2. Dibuja una imagen PNG con la resolución real de la pantalla, usando Pillow.
3. La guarda en `~/Pictures/hardware_wallpaper.png`.
4. La aplica como fondo de GNOME (tema claro y oscuro, modo `zoom`).
5. Escribe un registro en `~/.local/share/aurora-desktop-picture/last-run.log`.

La imagen incluye una línea **«Actualizado: fecha y hora»** para que puedas comprobar que se refresca sola.

> **Privacidad:** el fondo muestra el hostname y la IP local, y el registro guarda las rutas y errores. No compartas el PNG ni el log sin revisarlos antes.

## Requisitos

- Linux con GNOME (probado en Ubuntu 26.04, sesión Wayland con XWayland).
- Python 3.10 o superior.
- Pillow 9 o superior.
- Herramientas opcionales que mejoran los datos mostrados: `lspci` (paquete `pciutils`) y `lscpu` (paquete `util-linux`). Si faltan, el script degrada aisladamente esas filas.
- `xdpyinfo` (paquete `x11-utils`) para detectar la resolución; si no está disponible se usa una resolución de reserva de 3072x1728.
- `gsettings` para aplicar el fondo.

## Instalación

```bash
sudo apt install python3-pil x11-utils pciutils
cd ~/aurora-desktop-picture
chmod +x install.sh actualizar.sh desinstalar.sh
./install.sh
```

Alternativamente, con entorno virtual y `pip`:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
./install.sh
```

`install.sh` crea este archivo:

```
~/.config/autostart/aurora-desktop-picture.desktop
```

Gracias a él, GNOME ejecuta el script **automáticamente al iniciar sesión**. Para que el cambio surta efecto, cierra sesión y vuelve a entrar una vez.

## Estructura

```
aurora-desktop-picture/
├── generate_wallpaper.py   # script principal: recolección, dibujo y aplicación
├── install.sh              # instala el arranque automático
├── actualizar.sh           # refresco manual
├── desinstalar.sh          # quita el arranque automático
├── requirements.txt        # dependencia Python (Pillow)
├── AGENTS.md               # instrucciones para agentes de IA que trabajen aquí
├── CHANGELOG.md            # historial de cambios
├── README.md               # esta documentación
└── .gitignore
```

## Uso manual

```bash
./actualizar.sh                                  # regenera y aplica el fondo
python3 generate_wallpaper.py --print             # solo muestra los datos detectados
python3 generate_wallpaper.py --no-set            # crea la imagen sin cambiar el fondo
python3 generate_wallpaper.py --output /tmp/prueba.png
python3 generate_wallpaper.py --log /tmp/prueba.log
```

Opciones disponibles:

| Opción | Descripción |
| --- | --- |
| `--output RUTA` | Ruta del PNG generado (por defecto `~/Pictures/hardware_wallpaper.png`). |
| `--no-set` | No modifica `gsettings`; útil para probar sin tocar el fondo actual. |
| `--log RUTA` | Añade los mensajes a un archivo de registro. |
| `--print` | Imprime las filas de datos detectados por stdout. |

El programa devuelve `0` si todo salió bien y `1` si hubo un error; el error también se escribe en el registro si se indicó `--log`.

## Comprobar que funciona

```bash
cat ~/.local/share/aurora-desktop-picture/last-run.log
gsettings get org.gnome.desktop.background picture-uri
gsettings get org.gnome.desktop.background picture-uri-dark
gsettings get org.gnome.desktop.background picture-options
```

La fecha de la última línea del registro debería coincidir con el último inicio de sesión, y la URI debería apuntar a `~/Pictures/hardware_wallpaper.png` con `picture-options` en `'zoom'`.

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

Tras cualquier cambio, comprueba primero con `python3 generate_wallpaper.py --print --no-set --output /tmp/prueba.png`.

## Solución de problemas

| Síntoma | Causa probable | Acción |
| --- | --- | --- |
| El fondo no se actualiza al iniciar sesión | El arranque automático se lanzó antes de que X11 estuviera listo y `xdpyinfo` devolvió dimensiones inválidas. | Revisa el registro; ejecuta `./actualizar.sh` una vez iniciada la sesión. |
| `ERROR: ValueError: x1 must be greater than or equal to x0` | Resolución detectada demasiado pequeña o inválida en el arranque. | Igual que arriba; el bug está documentado en `CHANGELOG.md`. |
| `ERROR: ValueError: y1 must be greater than or equal to y0` | Altura insuficiente para el panel. | Igual que arriba. |
| `Aviso: no se pudo aplicar picture-uri` | `gsettings` sin acceso a la sesión gráfica (por ejemplo, desde SSH o cron). | Ejecuta el script dentro de la sesión de usuario. |
| La imagen se ve con texto cortado | La resolución es menor que el espacio necesario para las 12 filas. | Ver limitaciones conocidas. |

## Limitaciones conocidas

- En pantallas de 1080p el contenido diseñado necesita ~1468 px de alto: las últimas filas quedan fuera del panel/pantalla y el pie puede solaparlas. La resolución de reserva (3072x1728) sí cabe, por lo que el fallo no aparece en pruebas sin pantalla.
- La detección de resolución depende de XWayland; en el arranque puede devolver valores transitorios inválidos.
- El panel `.desktop` se instala con permiso de ejecución, lo que produce un aviso no fatal de `systemd-xdg-autostart-generator`.
- No hay suite de pruebas automatizada; la verificación es manual con `--print` y `--no-set`.

## Desarrollo

Consulta `AGENTS.md` para las convenciones del proyecto y `CHANGELOG.md` para el historial de cambios. Los archivos generados (`*.png`, `*.log`, `__pycache__`) están excluidos por `.gitignore` y no deben subirse al repositorio.

## Licencia

Sin licencia declarada actualmente. Añade un archivo `LICENSE` si deseas publicar el proyecto bajo términos concretos.
