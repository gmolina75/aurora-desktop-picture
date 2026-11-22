#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
if [[ ! -e .git ]] || [[ "$(git branch --show-current)" != master ]]; then
    printf '%s\n' 'Ejecuta este actualizador desde un clon del proyecto en la rama master.' >&2
    exit 1
fi

git pull --ff-only origin master
bash actualizar.sh
