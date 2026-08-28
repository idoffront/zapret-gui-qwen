#!/bin/bash
#
# build-rpm.sh - Скрипт сборки RPM пакета для Zapret Manager
#
# Использование:
#   ./build-rpm.sh              # Сборка RPM пакета
#   ./build-rpm.sh --clean      # Очистка после сборки
#   ./build-rpm.sh --install    # Сборка и установка
#

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Пути
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RPM_DIR="${SCRIPT_DIR}/rpm"
SOURCES_DIR="${RPM_DIR}/SOURCES"
SPECS_DIR="${RPM_DIR}/SPECS"
BUILD_DIR="${RPM_DIR}/BUILD"
RPMS_DIR="${RPM_DIR}/RPMS"
SRPMS_DIR="${RPM_DIR}/SRPMS"

# Версия приложения
VERSION="1.0.0"
APP_NAME="zapret-gui"
TARBALL_NAME="${APP_NAME}-${VERSION}"

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

# Проверка зависимостей для сборки RPM
check_rpm_build_deps() {
    log_info "Проверка зависимостей для сборки RPM..."
    
    local missing_deps=()
    
    if ! command -v rpmbuild &> /dev/null; then
        missing_deps+=("rpm-build")
    fi
    
    if ! command -v spectool &> /dev/null; then
        missing_deps+=("rpmdevtools")
    fi
    
    if ! command -v python3 &> /dev/null; then
        missing_deps+=("python3")
    fi
    
    if [[ ${#missing_deps[@]} -gt 0 ]]; then
        log_error "Отсутствуют зависимости для сборки RPM: ${missing_deps[*]}"
        log_info "Установите их командой:"
        echo "  sudo dnf install ${missing_deps[*]}"
        exit 1
    fi
    
    log_success "Зависимости для сборки RPM найдены"
}

# Подготовка директорий для rpmbuild
prepare_rpmbuild_dirs() {
    log_info "Подготовка директорий для rpmbuild..."
    
    mkdir -p "$SOURCES_DIR"
    mkdir -p "$SPECS_DIR"
    mkdir -p "$BUILD_DIR"
    mkdir -p "$RPMS_DIR"
    mkdir -p "$SRPMS_DIR"
    
    log_success "Директории созданы"
}

# Создание tarball с исходниками
create_tarball() {
    log_info "Создание tarball с исходниками..."
    
    # Список файлов для включения в tarball
    local files_to_include=(
        "main.py"
        "zapret_backend.py"
        "zapret_commands.json"
        "io.github.snowy-fluffy.zapret-gui.desktop"
        "io.github.snowy-fluffy.zapret-gui.svg"
        "io.github.snowy-fluffy.zapret-gui.policy"
        "README.md"
        "install.sh"
        "zapret-gui.sh"
    )
    
    # Создаём временную директорию для tarball
    local temp_dir=$(mktemp -d)
    local package_dir="${temp_dir}/${TARBALL_NAME}"
    mkdir -p "$package_dir"
    
    # Копируем файлы
    for file in "${files_to_include[@]}"; do
        if [[ -f "${SCRIPT_DIR}/${file}" ]]; then
            cp "${SCRIPT_DIR}/${file}" "$package_dir/"
        else
            log_warn "Файл ${file} не найден, пропускаем"
        fi
    done
    
    # Создаём LICENSE файл если нет
    if [[ ! -f "${SCRIPT_DIR}/LICENSE" ]]; then
        cat > "$package_dir/LICENSE" << 'EOF'
GNU GENERAL PUBLIC LICENSE
Version 3, 29 June 2007

Copyright (C) 2025 Zapret Manager Team

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
EOF
    else
        cp "${SCRIPT_DIR}/LICENSE" "$package_dir/"
    fi
    
    # Создаём tar.gz архив
    cd "$temp_dir"
    tar -czf "${SOURCES_DIR}/${TARBALL_NAME}.tar.gz" "${TARBALL_NAME}"
    cd "$SCRIPT_DIR"
    
    # Очистка временной директории
    rm -rf "$temp_dir"
    
    log_success "Tarball создан: ${SOURCES_DIR}/${TARBALL_NAME}.tar.gz"
}

# Сборка RPM пакета
build_rpm() {
    log_info "Сборка RPM пакета..."
    
    local spec_file="${SPECS_DIR}/${APP_NAME}.spec"
    
    if [[ ! -f "$spec_file" ]]; then
        log_error "Spec файл не найден: $spec_file"
        exit 1
    fi
    
    # Сборка binary и source пакетов
    rpmbuild \
        --define "_topdir ${RPM_DIR}" \
        --define "_sourcedir ${SOURCES_DIR}" \
        --define "_specdir ${SPECS_DIR}" \
        --define "_builddir ${BUILD_DIR}" \
        --define "_rpmdir ${RPMS_DIR}" \
        --define "_srcrpmdir ${SRPMS_DIR}" \
        -ba "$spec_file"
    
    log_success "RPM пакеты собраны"
    echo ""
    echo "Binary RPM:"
    find "$RPMS_DIR" -name "*.rpm" -not -name "*.src.rpm" | while read rpm; do
        echo "  - $rpm"
    done
    echo ""
    echo "Source RPM:"
    find "$SRPMS_DIR" -name "*.src.rpm" | while read rpm; do
        echo "  - $rpm"
    done
}

# Установка собранного RPM
install_rpm() {
    log_info "Установка RPM пакета..."
    
    local rpm_file=$(find "$RPMS_DIR" -name "*.rpm" -not -name "*.src.rpm" | head -n1)
    
    if [[ -z "$rpm_file" || ! -f "$rpm_file" ]]; then
        log_error "RPM файл не найден. Сначала выполните сборку."
        exit 1
    fi
    
    sudo dnf install -y "$rpm_file"
    
    log_success "RPM пакет установлен из: $rpm_file"
}

# Очистка результатов сборки
clean_build() {
    log_info "Очистка результатов сборки..."
    
    rm -rf "$BUILD_DIR"
    rm -rf "$RPMS_DIR"
    rm -rf "$SRPMS_DIR"
    rm -rf "$SOURCES_DIR/${TARBALL_NAME}.tar.gz"
    
    log_success "Очистка завершена"
    log_info "Spec файл и исходники сохранены"
}

# Полная очистка
clean_all() {
    log_info "Полная очистка..."
    
    rm -rf "$RPM_DIR"
    
    log_success "Все очищено"
}

# Показ справки
show_help() {
    echo "Zapret Manager - Сборка RPM пакета"
    echo ""
    echo "Использование:"
    echo "  $0 [COMMAND]"
    echo ""
    echo "Команды:"
    echo "  build       Сборка RPM пакета (по умолчанию)"
    echo "  install     Сборка и установка RPM пакета"
    echo "  clean       Очистка результатов сборки (сохраняет spec и sources)"
    echo "  clean-all   Полная очистка включая spec и sources"
    echo "  help        Показать эту справку"
    echo ""
    echo "Примеры:"
    echo "  $0                  # Собрать RPM пакет"
    echo "  $0 --install        # Собрать и установить"
    echo "  $0 --clean          # Очистить результаты сборки"
    echo ""
}

# Основная функция
main() {
    case "${1:-build}" in
        build|--build|-b)
            check_rpm_build_deps
            prepare_rpmbuild_dirs
            create_tarball
            build_rpm
            ;;
        install|--install|-i)
            check_rpm_build_deps
            prepare_rpmbuild_dirs
            create_tarball
            build_rpm
            install_rpm
            ;;
        clean|--clean|-c)
            clean_build
            ;;
        clean-all|--clean-all)
            clean_all
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
