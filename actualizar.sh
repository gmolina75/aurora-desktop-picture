#!/usr/bin/env bash
# Actualiza el fondo manualmente sin cerrar sesión.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
python3 "$DIR/generate_wallpaper.py" --log "$HOME/.local/share/aurora-desktop-picture/last-run.log"
