#!/usr/bin/env bash
# Instala el arranque automático de Aurora Desktop Picture.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AUTOSTART_DIR="$HOME/.config/autostart"
AUTOSTART_FILE="$AUTOSTART_DIR/aurora-desktop-picture.desktop"

echo "==> Comprobando dependencias..."
if ! python3 -c 'import PIL' 2>/dev/null; then
    echo "Falta Pillow. Instálalo con:"
    echo "  sudo apt install python3-pil"
    exit 1
fi

mkdir -p "$AUTOSTART_DIR" "$HOME/Pictures" "$HOME/.local/share/aurora-desktop-picture"

echo "==> Creando entrada de arranque automático..."
cat > "$AUTOSTART_FILE" <<EOF
[Desktop Entry]
Type=Application
Name=Aurora Desktop Picture
Comment=Actualiza el fondo de pantalla con los datos del hardware
Exec=/usr/bin/env python3 "$DIR/generate_wallpaper.py" --wait-display 20 --log "$HOME/.local/share/aurora-desktop-picture/last-run.log"
X-GNOME-Autostart-enabled=true
NoDisplay=true
EOF
chmod 644 "$AUTOSTART_FILE"

echo "==> Generando el fondo con los datos actuales..."
python3 "$DIR/generate_wallpaper.py" --log "$HOME/.local/share/aurora-desktop-picture/last-run.log"

echo
echo "Listo. El fondo se actualizará solo cada vez que inicies sesión."
echo "  Entrada de arranque: $AUTOSTART_FILE"
echo "  Imagen:              $HOME/Pictures/hardware_wallpaper.png"
echo "  Registro:            $HOME/.local/share/aurora-desktop-picture/last-run.log"
