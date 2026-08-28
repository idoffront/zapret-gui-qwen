Name:           zapret-gui
Version:        1.0.0
Release:        1%{?dist}
Summary:        GNOME GUI application for managing zapret-installer
License:        GPL-3.0-or-later
URL:            https://github.com/snowy-fluffy/zapret-installer
BuildArch:      noarch

# Описание на русском и английском
%description
Zapret Manager is a native GNOME GUI application for managing zapret-installer
from Snowy-Fluffy. It provides a user-friendly interface for controlling zapret
without using TUI/CLI, following GNOME Human Interface Guidelines.

Приложение Zapret Manager предоставляет графический интерфейс для управления
zapret-installer в Fedora. Позволяет включать/выключать zapret, просматривать
логи, настраивать параметры через удобный интерфейс в стиле GNOME.

# Зависимости во время сборки (для noarch пакета не нужны, но оставим для полноты)
BuildRequires:  rpm-build >= 4.18
BuildRequires:  python3 >= 3.12
BuildRequires:  desktop-file-utils
BuildRequires:  libxml2

# Runtime зависимости
Requires:       python3 >= 3.12
Requires:       python3-gobject >= 3.48
Requires:       gtk4 >= 4.14
Requires:       libadwaita >= 1.5
Requires:       polkit >= 124
Requires:       pkexec
Requires:       systemd
Requires:       jq
Requires(post): gtk-update-icon-cache
Requires(post): desktop-file-utils
Requires(postun): gtk-update-icon-cache
Requires(postun): desktop-file-utils

# Исходники
Source0:        %{name}-%{version}.tar.gz

# Пути установки
%global _bindir /usr/bin
%global _datadir /usr/share
%global app_id io.github.snowy-fluffy.zapret-gui

%prep
%setup -q -n %{name}-%{version}

%build
# Для noarch Python приложения сборка не требуется
# Можно выполнить проверку синтаксиса
python3 -m py_compile main.py zapret_backend.py

%install
# Создаём директории
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/zapret-gui
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/polkit-1/actions
mkdir -p %{buildroot}/etc/zapret-gui

# Копируем Python файлы
install -m 644 main.py %{buildroot}%{_datadir}/zapret-gui/main.py
install -m 644 zapret_backend.py %{buildroot}%{_datadir}/zapret-gui/zapret_backend.py
install -m 644 zapret_commands.json %{buildroot}%{_datadir}/zapret-gui/zapret_commands.json

# Копируем конфигурацию по умолчанию в /etc
install -m 644 zapret_commands.json %{buildroot}/etc/zapret-gui/config.json

# Устанавливаем иконку
install -m 644 %{app_id}.svg %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg

# Устанавливаем desktop файл
install -m 644 %{app_id}.desktop %{buildroot}%{_datadir}/applications/%{app_id}.desktop

# Устанавливаем PolicyKit правила
install -m 644 %{app_id}.policy %{buildroot}%{_datadir}/polkit-1/actions/%{app_id}.policy

# Создаём скрипт запуска
cat > %{buildroot}%{_bindir}/zapret-gui << 'EOF'
#!/bin/bash
exec /usr/bin/python3 %{_datadir}/zapret-gui/main.py "$@"
EOF
chmod 755 %{buildroot}%{_bindir}/zapret-gui

# Создаём символическую ссылку
ln -sf zapret-gui %{buildroot}%{_bindir}/zapret-manager

%check
# Проверка синтаксиса Python
python3 -m py_compile main.py zapret_backend.py

# Проверка JSON
python3 -c "import json; json.load(open('zapret_commands.json'))"

# Проверка XML (PolicyKit)
python3 -c "import xml.etree.ElementTree as ET; ET.parse('%{app_id}.policy')"

# Проверка desktop файла
desktop-file-validate %{buildroot}%{_datadir}/applications/%{app_id}.desktop || true

%post
# Обновление кэша иконок
gtk-update-icon-cache -q %{_datadir}/icons/hicolor &>/dev/null || :

# Обновление базы desktop файлов
update-desktop-database %{_datadir}/applications &>/dev/null || :

# Перезагрузка polkit
systemctl reload polkit.service &>/dev/null || :

%postun
# Обновление кэша иконок при удалении
gtk-update-icon-cache -q %{_datadir}/icons/hicolor &>/dev/null || :

# Обновление базы desktop файлов при удалении
update-desktop-database %{_datadir}/applications &>/dev/null || :

# Перезагрузка polkit при удалении
systemctl reload polkit.service &>/dev/null || :

%preun
if [ $1 -eq 0 ]; then
    # Полное удаление пакета
    # Сохраняем пользовательскую конфигурацию
    if [ -d /etc/zapret-gui ]; then
        mv /etc/zapret-gui /etc/zapret-gui.backup.$(date +%Y%m%d%H%M%S) 2>/dev/null || :
    fi
fi

%files
# Python модули
%{_datadir}/zapret-gui/main.py
%{_datadir}/zapret-gui/zapret_backend.py
%{_datadir}/zapret-gui/zapret_commands.json

# Конфигурация (помечена как config, не удаляется при обновлении)
%dir /etc/zapret-gui
%config(noreplace) /etc/zapret-gui/config.json

# Иконка
%{_datadir}/icons/hicolor/scalable/apps/%{app_id}.svg

# Desktop файл
%{_datadir}/applications/%{app_id}.desktop

# PolicyKit правила
%{_datadir}/polkit-1/actions/%{app_id}.policy

# Скрипт запуска
%{_bindir}/zapret-gui
%{_bindir}/zapret-manager

%doc README.md
%license LICENSE

%changelog
* Mon Jan 01 2025 Zapret Manager Team <zapret-gui@example.com> - 1.0.0-1
- Initial package for Fedora 44
- Native GTK4/libadwaita GUI for zapret-installer
- PolicyKit integration for privileged operations
- Systemd service status monitoring
- Log viewer with journalctl integration
