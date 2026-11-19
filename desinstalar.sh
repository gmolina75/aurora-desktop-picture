#!/usr/bin/env bash
# Quita el arranque automático (la imagen NO se borra).
set -euo pipefail

AUTOSTART_FILE="$HOME/.config/autostart/aurora-desktop-picture.desktop"
if [ -f "$AUTOSTART_FILE" ]; then
    rm "$AUTOSTART_FILE"
    echo "Arranque automático eliminado: $AUTOSTART_FILE"
else
    echo "No había arranque automático instalado."
fi
echo "La imagen en ~/Pictures/hardware_wallpaper.png se ha conservado."
