# Aurora Desktop Picture

Fondo de pantalla que muestra las **especificaciones reales del equipo**, leídas directamente del sistema cada vez que inicias sesión.

## Qué hace

1. Recoge los datos del hardware (`/proc`, `/sys`, `lspci`, `lscpu`, `/etc/os-release`), incluidos el **nombre del equipo** (hostname) y su **dirección IP** local.
2. Dibuja una imagen PNG con la resolución real de la pantalla, usando Pillow.
3. La guarda en `~/Pictures/hardware_wallpaper.png`.
4. La aplica como fondo de GNOME (tema claro y oscuro, modo `zoom`).
5. Escribe un registro en `~/.local/share/aurora-desktop-picture/last-run.log`.

La imagen incluye una línea **«Actualizado: fecha y hora»** para que puedas comprobar que se refresca sola.

## Estructura

```
aurora-desktop-picture/
├── generate_wallpaper.py   # script principal
├── install.sh              # instala el arranque automático
├── actualizar.sh           # refresco manual
├── desinstalar.sh          # quita el arranque automático
└── README.md
```

## Instalación

Necesitas Python 3 y Pillow:

```bash
sudo apt install python3-pil
cd ~/aurora-desktop-picture
chmod +x install.sh actualizar.sh desinstalar.sh
./install.sh
```

`install.sh` crea este archivo:

```
~/.config/autostart/aurora-desktop-picture.desktop
```

Gracias a él, GNOME ejecuta el script **automáticamente al iniciar sesión**. Para que el cambio surta efecto, cierra sesión y vuelve a entrar una vez.

## Uso manual

```bash
./actualizar.sh                                  # regenera y aplica el fondo
python3 generate_wallpaper.py --print             # solo muestra los datos detectados
python3 generate_wallpaper.py --no-set            # crea la imagen sin cambiar el fondo
python3 generate_wallpaper.py --output /tmp/prueba.png
```

## Comprobar que funciona

```bash
cat ~/.local/share/aurora-desktop-picture/last-run.log
gsettings get org.gnome.desktop.background picture-uri
```

La fecha de la última línea debería coincidir con el último inicio de sesión.

## Desinstalar

```bash
./desinstalar.sh
```

Esto elimina solo el arranque automático; la imagen se conserva. Para volver al fondo por defecto de Ubuntu:

```bash
gsettings reset org.gnome.desktop.background picture-uri
gsettings reset org.gnome.desktop.background picture-uri-dark
```

## Personalización

Edita `generate_wallpaper.py`:

- Colores: constantes `c0` / `c1` (fondo) y los valores RGBA de `d.text(...)`.
- Tamaños: `header_h`, `row_h`, `footer_h`.
- Fuentes: variables `F_MONO`, `F_MONO_B`, `F_SANS_B`.
- Texto/cabecera: cadenas dentro de `render()` y `collect_hardware()`.
