# Zapret Manager

Графический интерфейс для управления **zapret-installer** от Snowy-Fluffy в Fedora 44 с использованием GTK4 и libadwaita.

## Описание

Приложение предоставляет удобный GUI для управления zapret вместо TUI/CLI интерфейса оригинального `/usr/bin/zapret`. 

### Возможности

- **Главный переключатель** - включение/выключение zapret одним кликом
- **Индикатор статуса** - отображение текущего состояния (активно, остановлено, неизвестно)
- **Дополнительные функции**:
  - Перезапуск службы
  - Включение/отключение автозапуска
  - Установка/удаление/обновление
  - Просмотр логов через journalctl
  - Настройка параметров подключения
- **Безопасность** - использование pkexec/PolicyKit для привилегированных действий
- **GNOME-style интерфейс** - соответствует Human Interface Guidelines

## Структура проекта

```
zapret-gui/
├── main.py                          # Главный модуль GTK4 приложения
├── zapret_backend.py                # Модуль выполнения команд и определения статуса
├── zapret_commands.json             # Конфигурация команд (можно редактировать)
├── zapret-gui.sh                    # Скрипт запуска
├── io.github.snowy-fluffy.zapret-gui.desktop  # Desktop файл для GNOME
├── io.github.snowy-fluffy.zapret-gui.svg      # Иконка приложения
├── io.github.snowy-fluffy.zapret-gui.policy   # PolicyKit правила
├── Makefile                         # Установка через make
└── README.md                        # Этот файл
```

## Зависимости

Для Fedora 44:

```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita polkit pkexec
```

## Установка

### Вариант 1: Через Makefile (рекомендуется)

```bash
cd zapret-gui
sudo make install
```

Это установит:
- Приложение в `/usr/bin/zapret-gui`
- Desktop файл в `/usr/share/applications/`
- Иконку в `/usr/share/icons/hicolor/scalable/apps/`
- PolicyKit правила в `/usr/share/polkit-1/actions/`

### Вариант 2: Ручная установка

```bash
# Копирование файлов
sudo cp zapret-gui.sh /usr/bin/zapret-gui
sudo chmod +x /usr/bin/zapret-gui
sudo cp io.github.snowy-fluffy.zapret-gui.desktop /usr/share/applications/
sudo cp io.github.snowy-fluffy.zapret-gui.svg /usr/share/icons/hicolor/scalable/apps/
sudo cp io.github.snowy-fluffy.zapret-gui.policy /usr/share/polkit-1/actions/

# Обновление кэша иконок
sudo gtk-update-icon-cache /usr/share/icons/hicolor
```

### Вариант 3: Локальный запуск без установки

```bash
cd zapret-gui
chmod +x zapret-gui.sh
./zapret-gui.sh
```

## Использование

1. Запустите приложение из меню приложений GNOME (найдите "Zapret Manager")
2. При первом запуске приложение попытается определить текущий статус zapret
3. Используйте главный переключатель для включения/выключения
4. Дополнительные функции доступны в боковой панели

## Конфигурация

По умолчанию приложение использует следующие команды:

| Действие | Команда |
|----------|---------|
| Статус | `systemctl is-active zapret.service` или `/usr/bin/zapret status` |
| Включение | `systemctl start zapret.service` |
| Выключение | `systemctl stop zapret.service` |
| Перезапуск | `systemctl restart zapret.service` |
| Автозапуск вкл | `systemctl enable zapret.service` |
| Автозапуск выкл | `systemctl disable zapret.service` |
| Установка | `/usr/bin/zapret install` |
| Удаление | `/usr/bin/zapret uninstall` |
| Обновление | `/usr/bin/zapret update` |

### Изменение конфигурации

Если команды отличаются в вашей версии zapret, создайте файл конфигурации:

**Системная конфигурация** (`/etc/zapret-gui/config.json`):
```json
{
    "zapret_binary": "/usr/bin/zapret",
    "commands": {
        "status": {"args": ["status"]},
        "start": {"args": ["start"]},
        "stop": {"args": ["stop"]}
    },
    "systemd_service": {
        "name": "zapret.service",
        "use_systemctl": true
    }
}
```

**Пользовательская конфигурация** (`~/.config/zapret-gui/config.json`):
```json
{
    "timeout_seconds": 60
}
```

## Безопасность

- Приложение **не запускается от root**
- Для привилегированных действий используется `pkexec`
- Все команды выполняются через `subprocess` с передачей аргументов списком (защита от shell-инъекций)
- PolicyKit правила ограничивают список разрешённых команд

## Troubleshooting

### Приложение не запускается

Проверьте зависимости:
```bash
python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')"
```

### Не определяется статус

1. Проверьте наличие systemd сервиса:
   ```bash
   systemctl list-unit-files | grep zapret
   ```

2. Если сервис называется иначе, измените в конфигурации `systemd_service.name`

### pkexec запрашивает пароль каждый раз

Это нормальное поведение. Для более удобной работы можно настроить PolicyKit правила в `/etc/polkit-1/rules.d/`.

### Ошибка "Zapret binary not found"

Убедитесь, что zapret установлен:
```bash
ls -la /usr/bin/zapret
```

Если путь отличается, укажите правильный в конфигурации.

## Лицензия

GPL-3.0

## Авторы

- Оригинал zapret-installer: [Snowy-Fluffy](https://github.com/Snowy-Fluffy/zapret-installer)
- GUI обёртка: Community contribution

## Вклад в проект

Если команды `/usr/bin/zapret` отличаются в вашей версии, пожалуйста, отправьте PR с обновлением `zapret_commands.json`.
