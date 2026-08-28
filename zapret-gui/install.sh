#!/bin/bash
#
# install.sh - Скрипт установки Zapret Manager
# 
# Использование:
#   sudo ./install.sh              # Установка в систему
#   sudo ./install.sh --uninstall  # Удаление из системы
#   ./install.sh --check           # Проверка наличия установки
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Пути установки
PREFIX="${PREFIX:-/usr}"
BINDIR="${PREFIX}/bin"
SHAREDIR="${PREFIX}/share"
ICONSDIR="${SHAREDIR}/icons/hicolor/scalable/apps"
APPSDIR="${SHAREDIR}/applications"
POLKITDIR="${SHAREDIR}/polkit-1/actions"
SYSCONFDIR="/etc"
APP_ID="io.github.snowy-fluffy.zapret-gui"

# Файлы проекта
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_PY="${SCRIPT_DIR}/main.py"
BACKEND_PY="${SCRIPT_DIR}/zapret_backend.py"
CONFIG_JSON="${SCRIPT_DIR}/zapret_commands.json"
DESKTOP_FILE="${SCRIPT_DIR}/${APP_ID}.desktop"
SVG_ICON="${SCRIPT_DIR}/${APP_ID}.svg"
POLICY_FILE="${SCRIPT_DIR}/${APP_ID}.policy"
LAUNCHER_SCRIPT="${SCRIPT_DIR}/zapret-gui.sh"

# Функции логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Проверка запуска от root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт должен запускаться от root (используйте sudo)"
        exit 1
    fi
}

# Проверка зависимостей
check_dependencies() {
    log_info "Проверка зависимостей..."
    
    local missing_deps=()
    
    # Проверка python3
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    # Проверка GTK4 и libadwaita через pkg-config
    if ! pkg-config --exists gtk4 2>/dev/null; then
        missing_deps+=("gtk4")
    fi
    
    if ! pkg-config --exists libadwaita-1 2>/dev/null; then
        missing_deps+=("libadwaita")
    fi
    
    # Проверка PyGObject
    if ! python3 -c "import gi" 2>/dev/null; then
        missing_deps+=("python3-gobject")
    fi
    
    # Проверка polkit
    if ! command -v pkexec &> /dev/null; then
        missing_deps+=("polkit")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Отсутствуют зависимости: ${missing_deps[*]}"
        log_info "Установите их командой:"
        echo "  sudo dnf install ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "Все зависимости найдены"
}

# Проверка наличия файлов проекта
check_project_files() {
    log_info "Проверка файлов проекта..."
    
    local required_files=(
        "$MAIN_PY"
        "$BACKEND_PY"
        "$DESKTOP_FILE"
        "$SVG_ICON"
    )
    
    local missing_files=()
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            missing_files+=("$file")
        fi
    done
    
    if [[ ${#missing_files[@]} -gt 0 ]]; then
        log_error "Отсутствуют файлы проекта:"
        for file in "${missing_files[@]}"; do
            echo "  - $file"
        done
        exit 1
    fi
    
    # Конфигурация и policy файл опциональны
    if [[ ! -f "$CONFIG_JSON" ]]; then
        log_warn "Файл конфигурации zapret_commands.json не найден, будет использована встроенная конфигурация"
    fi
    
    if [[ ! -f "$POLICY_FILE" ]]; then
        log_warn "PolicyKit файл не найден, привилегированные действия могут не работать"
    fi
    
    log_success "Файлы проекта проверены"
}

# Установка приложения
do_install() {
    log_info "Начало установки Zapret Manager..."
    
    # Создание директорий
    log_info "Создание директорий..."
    mkdir -p "$BINDIR"
    mkdir -p "$SHAREDIR/zapret-gui"
    mkdir -p "$ICONSDIR"
    mkdir -p "$APPSDIR"
    mkdir -p "$POLKITDIR"
    mkdir -p "$SYSCONFDIR/zapret-gui"
    
    # Копирование Python файлов
    log_info "Копирование Python модулей..."
    cp "$MAIN_PY" "$SHAREDIR/zapret-gui/main.py"
    cp "$BACKEND_PY" "$SHAREDIR/zapret-gui/zapret_backend.py"
    chmod 644 "$SHAREDIR/zapret-gui/main.py"
    chmod 644 "$SHAREDIR/zapret-gui/zapret_backend.py"
    
    # Копирование конфигурации (если есть)
    if [[ -f "$CONFIG_JSON" ]]; then
        log_info "Копирование конфигурации..."
        cp "$CONFIG_JSON" "$SHAREDIR/zapret-gui/zapret_commands.json"
        chmod 644 "$SHAREDIR/zapret-gui/zapret_commands.json"
        # Также копируем в /etc для возможности пользовательской настройки
        cp "$CONFIG_JSON" "$SYSCONFDIR/zapret-gui/config.json"
        chmod 644 "$SYSCONFDIR/zapret-gui/config.json"
    fi
    
    # Установка иконки
    log_info "Установка иконки..."
    cp "$SVG_ICON" "$ICONSDIR/${APP_ID}.svg"
    chmod 644 "$ICONSDIR/${APP_ID}.svg"
    
    # Обновление кэша иконок
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -q "$ICONSDIR" 2>/dev/null || true
    fi
    
    # Установка desktop файла
    log_info "Установка desktop файла..."
    cp "$DESKTOP_FILE" "$APPSDIR/${APP_ID}.desktop"
    chmod 644 "$APPSDIR/${APP_ID}.desktop"
    
    # Обновление базы desktop файлов
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$APPSDIR" 2>/dev/null || true
    fi
    
    # Установка PolicyKit правил (если есть)
    if [[ -f "$POLICY_FILE" ]]; then
        log_info "Установка PolicyKit правил..."
        cp "$POLICY_FILE" "$POLKITDIR/${APP_ID}.policy"
        chmod 644 "$POLKITDIR/${APP_ID}.policy"
        
        # Перезагрузка polkit (если возможно)
        if systemctl is-active polkit.service &>/dev/null; then
            systemctl reload polkit.service 2>/dev/null || true
        fi
    fi
    
    # Создание скрипта-лаунчера
    log_info "Создание скрипта запуска..."
    cat > "$BINDIR/zapret-gui" << 'LAUNCHER_EOF'
#!/bin/bash
exec python3 /usr/share/zapret-gui/main.py "$@"
LAUNCHER_EOF
    chmod 755 "$BINDIR/zapret-gui"
    
    # Создание символической ссылки для удобства
    if [[ ! -L "$BINDIR/zapret-manager" ]]; then
        ln -sf zapret-gui "$BINDIR/zapret-manager" 2>/dev/null || true
    fi
    
    log_success "Zapret Manager успешно установлен!"
    echo ""
    echo "Приложение доступно:"
    echo "  - В меню приложений GNOME как 'Zapret Manager'"
    echo "  - Из терминала: zapret-gui или zapret-manager"
    echo ""
    log_info "Для удаления выполните: sudo $0 --uninstall"
}

# Удаление приложения
do_uninstall() {
    log_info "Начало удаления Zapret Manager..."
    
    # Удаление Python файлов
    log_info "Удаление Python модулей..."
    rm -rf "$SHAREDIR/zapret-gui"
    
    # Удаление иконки
    log_info "Удаление иконки..."
    rm -f "$ICONSDIR/${APP_ID}.svg"
    
    # Обновление кэша иконок
    if command -v gtk-update-icon-cache &> /dev/null; then
        gtk-update-icon-cache -q "$ICONSDIR" 2>/dev/null || true
    fi
    
    # Удаление desktop файла
    log_info "Удаление desktop файла..."
    rm -f "$APPSDIR/${APP_ID}.desktop"
    
    # Обновление базы desktop файлов
    if command -v update-desktop-database &> /dev/null; then
        update-desktop-database "$APPSDIR" 2>/dev/null || true
    fi
    
    # Удаление PolicyKit правил
    log_info "Удаление PolicyKit правил..."
    rm -f "$POLKITDIR/${APP_ID}.policy"
    
    # Перезагрузка polkit
    if systemctl is-active polkit.service &>/dev/null; then
        systemctl reload polkit.service 2>/dev/null || true
    fi
    
    # Удаление скрипта-лаунчера
    log_info "Удаление скрипта запуска..."
    rm -f "$BINDIR/zapret-gui"
    rm -f "$BINDIR/zapret-manager"
    
    # Удаление конфигурации из /etc (сохраняем пользовательские настройки)
    log_info "Сохранение пользовательской конфигурации..."
    if [[ -d "$SYSCONFDIR/zapret-gui" ]]; then
        mv "$SYSCONFDIR/zapret-gui" "$SYSCONFDIR/zapret-gui.backup" 2>/dev/null || true
        log_warn "Конфигурация сохранена в $SYSCONFDIR/zapret-gui.backup"
    fi
    
    log_success "Zapret Manager успешно удалён!"
    echo ""
    log_info "Пользовательская конфигурация сохранена в /etc/zapret-gui.backup"
    log_info "Для полного удаления конфигурации выполните: sudo rm -rf /etc/zapret-gui.backup"
}

# Проверка установки
do_check() {
    local installed=true
    
    echo "Проверка установки Zapret Manager..."
    echo ""
    
    # Проверка Python файлов
    if [[ -f "$SHAREDIR/zapret-gui/main.py" ]]; then
        echo -e "${GREEN}✓${NC} Python модули установлены"
    else
        echo -e "${RED}✗${NC} Python модули не найдены"
        installed=false
    fi
    
    # Проверка иконки
    if [[ -f "$ICONSDIR/${APP_ID}.svg" ]]; then
        echo -e "${GREEN}✓${NC} Иконка установлена"
    else
        echo -e "${RED}✗${NC} Иконка не найдена"
        installed=false
    fi
    
    # Проверка desktop файла
    if [[ -f "$APPSDIR/${APP_ID}.desktop" ]]; then
        echo -e "${GREEN}✓${NC} Desktop файл установлен"
    else
        echo -e "${RED}✗${NC} Desktop файл не найден"
        installed=false
    fi
    
    # Проверка лаунчера
    if [[ -x "$BINDIR/zapret-gui" ]]; then
        echo -e "${GREEN}✓${NC} Скрипт запуска установлен"
    else
        echo -e "${RED}✗${NC} Скрипт запуска не найден"
        installed=false
    fi
    
    # Проверка PolicyKit
    if [[ -f "$POLKITDIR/${APP_ID}.policy" ]]; then
        echo -e "${GREEN}✓${NC} PolicyKit правила установлены"
    else
        echo -e "${YELLOW}!${NC} PolicyKit правила не найдены (опционально)"
    fi
    
    echo ""
    if $installed; then
        log_success "Zapret Manager полностью установлен"
        exit 0
    else
        log_error "Zapret Manager установлен не полностью или отсутствует"
        exit 1
    fi
}

# Показ справки
show_help() {
    echo "Zapret Manager - Скрипт установки/удаления"
    echo ""
    echo "Использование:"
    echo "  sudo $0 [COMMAND]"
    echo ""
    echo "Команды:"
    echo "  install      Установка приложения (по умолчанию)"
    echo "  uninstall    Удаление приложения"
    echo "  check        Проверка наличия установки"
    echo "  help         Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  sudo $0              # Установить приложение"
    echo "  sudo $0 --uninstall  # Удалить приложение"
    echo "  $0 --check           # Проверить установку"
    echo ""
}

# Основная функция
main() {
    case "${1:-install}" in
        install|--install|-i)
            check_root
            check_dependencies
            check_project_files
            do_install
            ;;
        uninstall|--uninstall|-u)
            check_root
            do_uninstall
            ;;
        check|--check|-c)
            do_check
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Неизвестная команда: $1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
