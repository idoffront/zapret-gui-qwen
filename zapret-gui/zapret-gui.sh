#!/bin/bash
# Zapret Manager - Launcher script
# Запускает приложение через Python

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="${SCRIPT_DIR}/main.py"

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed."
    exit 1
fi

# Проверяем наличие GTK4 и libadwaita
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: GTK4 and/or libadwaita are not installed."
    echo "Please install: sudo dnf install gtk4 libadwaita python3-gobject"
    exit 1
fi

# Запускаем приложение
exec python3 "$PYTHON_SCRIPT" "$@"
