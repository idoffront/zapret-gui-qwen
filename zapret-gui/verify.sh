#!/bin/bash
#
# verify.sh - Скрипт проверки установки Zapret Manager
#
# Использование:
#   ./verify.sh              # Полная проверка
#   ./verify.sh --quick      # Быстрая проверка (только файлы)
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Пути установки
PREFIX="${PREFIX:-/usr}"
BINDIR="${PREFIX}/bin"
SHAREDIR="${PREFIX}/share"
ICONSDIR="${SHAREDIR}/icons/hicolor/scalable/apps"
APPSDIR="${SHAREDIR}/applications"
POLKITDIR="${SHAREDIR}/polkit-1/actions"
APP_ID="io.github.snowy-fluffy.zapret-gui"

# Счётчики
PASSED=0
FAILED=0
WARNINGS=0

log_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

log_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

log_warn() {
    echo -e "${YELLOW}!${NC} $1"
    ((WARNINGS++))
}

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

# Проверка Python файлов
check_python_files() {
    log_info "Проверка Python файлов..."
    
    if [[ -f "$SHAREDIR/zapret-gui/main.py" ]]; then
        log_pass "main.py установлен"
        
        # Проверка синтаксиса
        if python3 -m py_compile "$SHAREDIR/zapret-gui/main.py" 2>/dev/null; then
            log_pass "Синтаксис main.py корректен"
        else
            log_fail "Ошибка синтаксиса в main.py"
        fi
    else
        log_fail "main.py не найден"
    fi
    
    if [[ -f "$SHAREDIR/zapret-gui/zapret_backend.py" ]]; then
        log_pass "zapret_backend.py установлен"
        
        if python3 -m py_compile "$SHAREDIR/zapret-gui/zapret_backend.py" 2>/dev/null; then
            log_pass "Синтаксис zapret_backend.py корректен"
        else
            log_fail "Ошибка синтаксиса в zapret_backend.py"
        fi
    else
        log_fail "zapret_backend.py не найден"
    fi
    
    if [[ -f "$SHAREDIR/zapret-gui/zapret_commands.json" ]]; then
        log_pass "zapret_commands.json установлен"
        
        if python3 -c "import json; json.load(open('$SHAREDIR/zapret-gui/zapret_commands.json'))" 2>/dev/null; then
            log_pass "JSON конфигурация корректна"
        else
            log_fail "Ошибка в JSON конфигурации"
        fi
    else
        log_warn "zapret_commands.json не найден (будет использована встроенная конфигурация)"
    fi
}

# Проверка иконки
check_icon() {
    log_info "Проверка иконки..."
    
    if [[ -f "$ICONSDIR/${APP_ID}.svg" ]]; then
        log_pass "SVG иконка установлена"
        
        # Проверка что это валидный SVG
        if python3 -c "import xml.etree.ElementTree as ET; ET.parse('$ICONSDIR/${APP_ID}.svg')" 2>/dev/null; then
            log_pass "SVG файл корректен"
        else
            log_fail "Ошибка в SVG файле"
        fi
        
        # Проверка размера файла
        local size=$(stat -c%s "$ICONSDIR/${APP_ID}.svg" 2>/dev/null || echo 0)
        if [[ $size -gt 100 ]]; then
            log_pass "Размер иконки корректен ($size байт)"
        else
            log_warn "Иконка слишком маленькая ($size байт)"
        fi
    else
        log_fail "SVG иконка не найдена"
    fi
}

# Проверка desktop файла
check_desktop_file() {
    log_info "Проверка desktop файла..."
    
    if [[ -f "$APPSDIR/${APP_ID}.desktop" ]]; then
        log_pass "Desktop файл установлен"
        
        # Проверка обязательных полей
        local content=$(cat "$APPSDIR/${APP_ID}.desktop")
        
        if echo "$content" | grep -q "^Name="; then
            log_pass "Поле Name присутствует"
        else
            log_fail "Отсутствует поле Name"
        fi
        
        if echo "$content" | grep -q "^Exec="; then
            log_pass "Поле Exec присутствует"
        else
            log_fail "Отсутствует поле Exec"
        fi
        
        if echo "$content" | grep -q "^Icon="; then
            log_pass "Поле Icon присутствует"
        else
            log_fail "Отсутствует поле Icon"
        fi
        
        if echo "$content" | grep -q "^Type=Application"; then
            log_pass "Поле Type корректно"
        else
            log_fail "Отсутствует или некорректно поле Type"
        fi
        
        if echo "$content" | grep -q "^Categories="; then
            log_pass "Поле Categories присутствует"
        else
            log_fail "Отсутствует поле Categories"
        fi
        
        if echo "$content" | grep -q "^Terminal=false"; then
            log_pass "Terminal=false установлен"
        else
            log_warn "Terminal не установлен в false"
        fi
        
        # Проверка через desktop-file-validate если доступен
        if command -v desktop-file-validate &> /dev/null; then
            if desktop-file-validate "$APPSDIR/${APP_ID}.desktop" 2>/dev/null; then
                log_pass "desktop-file-validate прошёл успешно"
            else
                log_fail "desktop-file-validate обнаружил ошибки"
            fi
        else
            log_warn "desktop-file-validate не доступен"
        fi
    else
        log_fail "Desktop файл не найден"
    fi
}

# Проверка скрипта запуска
check_launcher() {
    log_info "Проверка скрипта запуска..."
    
    if [[ -x "$BINDIR/zapret-gui" ]]; then
        log_pass "Скрипт zapret-gui установлен и исполняемый"
        
        # Проверка содержимого
        if grep -q "python3" "$BINDIR/zapret-gui" && grep -q "main.py" "$BINDIR/zapret-gui"; then
            log_pass "Скрипт содержит корректный путь к main.py"
        else
            log_fail "Скрипт содержит некорректное содержимое"
        fi
    else
        log_fail "Скрипт zapret-gui не найден или не исполняемый"
    fi
    
    if [[ -L "$BINDIR/zapret-manager" ]]; then
        log_pass "Символическая ссылка zapret-manager существует"
    else
        log_warn "Символическая ссылка zapret-manager не найдена"
    fi
}

# Проверка PolicyKit
check_policykit() {
    log_info "Проверка PolicyKit..."
    
    if [[ -f "$POLKITDIR/${APP_ID}.policy" ]]; then
        log_pass "PolicyKit файл установлен"
        
        # Проверка XML
        if python3 -c "import xml.etree.ElementTree as ET; ET.parse('$POLKITDIR/${APP_ID}.policy')" 2>/dev/null; then
            log_pass "XML PolicyKit файла корректен"
        else
            log_fail "Ошибка в XML PolicyKit файла"
        fi
        
        # Проверка наличия action ID
        if grep -q "${APP_ID}" "$POLKITDIR/${APP_ID}.policy"; then
            log_pass "Action ID присутствует"
        else
            log_fail "Action ID не найден"
        fi
    else
        log_warn "PolicyKit файл не найден (привилегированные операции могут не работать)"
    fi
    
    # Проверка службы polkit
    if systemctl is-active polkit.service &>/dev/null; then
        log_pass "Служба polkit активна"
    else
        log_warn "Служба polkit не активна"
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    # Python3
    if command -v python3 &> /dev/null; then
        local pyver=$(python3 --version 2>&1 | cut -d' ' -f2)
        log_pass "Python3 установлен (версия $pyver)"
    else
        log_fail "Python3 не найден"
    fi
    
    # GTK4
    if pkg-config --exists gtk4 2>/dev/null; then
        local gtkver=$(pkg-config --modversion gtk4)
        log_pass "GTK4 установлен (версия $gtkver)"
    else
        log_fail "GTK4 не найден"
    fi
    
    # libadwaita
    if pkg-config --exists libadwaita-1 2>/dev/null; then
        local ladver=$(pkg-config --modversion libadwaita-1)
        log_pass "libadwaita установлен (версия $ladver)"
    else
        log_fail "libadwaita не найден"
    fi
    
    # PyGObject
    if python3 -c "import gi" 2>/dev/null; then
        log_pass "PyGObject установлен"
        
        # Проверка версий модулей
        if python3 -c "from gi.repository import Gtk, Adw" 2>/dev/null; then
            log_pass "Gtk и Adw доступны"
        else
            log_fail "Gtk или Adw не доступны"
        fi
    else
        log_fail "PyGObject не найден"
    fi
    
    # polkit
    if command -v pkexec &> /dev/null; then
        log_pass "pkexec доступен"
    else
        log_fail "pkexec не найден"
    fi
}

# Проверка конфигурации
check_config() {
    log_info "Проверка конфигурации..."
    
    if [[ -f "/etc/zapret-gui/config.json" ]]; then
        log_pass "Системная конфигурация найдена"
        
        if python3 -c "import json; json.load(open('/etc/zapret-gui/config.json'))" 2>/dev/null; then
            log_pass "Системная конфигурация корректна"
        else
            log_fail "Ошибка в системной конфигурации"
        fi
    else
        log_warn "Системная конфигурация не найдена"
    fi
    
    if [[ -f "$HOME/.config/zapret-gui/config.json" ]]; then
        log_pass "Пользовательская конфигурация найдена"
    else
        log_info "Пользовательская конфигурация не найдена (используется системная или встроенная)"
    fi
}

# Итоговый отчёт
print_summary() {
    echo ""
    echo "======================================"
    echo "         ИТОГОВЫЙ ОТЧЁТ"
    echo "======================================"
    echo -e "${GREEN}Успешно:${NC} $PASSED"
    echo -e "${YELLOW}Предупреждения:${NC} $WARNINGS"
    echo -e "${RED}Ошибки:${NC} $FAILED"
    echo "======================================"
    
    if [[ $FAILED -eq 0 ]]; then
        echo -e "${GREEN}Все проверки пройдены!${NC}"
        return 0
    else
        echo -e "${RED}Обнаружены ошибки!${NC}"
        return 1
    fi
}

# Быстрая проверка
do_quick_check() {
    log_info "Быстрая проверка файлов..."
    
    [[ -f "$SHAREDIR/zapret-gui/main.py" ]] && log_pass "main.py" || log_fail "main.py"
    [[ -f "$SHAREDIR/zapret-gui/zapret_backend.py" ]] && log_pass "zapret_backend.py" || log_fail "zapret_backend.py"
    [[ -f "$ICONSDIR/${APP_ID}.svg" ]] && log_pass "Иконка" || log_fail "Иконка"
    [[ -f "$APPSDIR/${APP_ID}.desktop" ]] && log_pass "Desktop файл" || log_fail "Desktop файл"
    [[ -x "$BINDIR/zapret-gui" ]] && log_pass "Скрипт запуска" || log_fail "Скрипт запуска"
    
    print_summary
}

# Полная проверка
do_full_check() {
    log_info "Полная проверка установки Zapret Manager..."
    echo ""
    
    check_dependencies
    echo ""
    check_python_files
    echo ""
    check_icon
    echo ""
    check_desktop_file
    echo ""
    check_launcher
    echo ""
    check_policykit
    echo ""
    check_config
    echo ""
    
    print_summary
}

# Показ справки
show_help() {
    echo "Zapret Manager - Проверка установки"
    echo ""
    echo "Использование:"
    echo "  $0 [COMMAND]"
    echo ""
    echo "Команды:"
    echo "  full        Полная проверка (по умолчанию)"
    echo "  quick       Быстрая проверка (только файлы)"
    echo "  help        Показать эту справку"
    echo ""
}

# Основная функция
main() {
    case "${1:-full}" in
        full|--full|-f)
            do_full_check
            ;;
        quick|--quick|-q)
            do_quick_check
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_fail "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
