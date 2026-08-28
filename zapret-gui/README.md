# Zapret Manager

Нативное GNOME GUI-приложение для управления zapret-installer от Snowy-Fluffy в Fedora 44.

## Описание

Zapret Manager предоставляет удобный графический интерфейс для управления zapret-installer без необходимости использовать TUI/CLI. Приложение соответствует GNOME Human Interface Guidelines и использует GTK4/libadwaita.

### Возможности

- **Главный переключатель**: Включение/выключение zapret одним кликом
- **Статус в реальном времени**: Отображение текущего состояния (активно, остановлено, ошибка)
- **Дополнительные функции**: Перезапуск, автозапуск, установка, удаление, обновление
- **Просмотр логов**: Интеграция с journalctl для просмотра логов systemd
- **Настройки**: Конфигурация путей к командам и параметров
- **Безопасность**: Использование PolicyKit/pkexec для привилегированных операций

## Требования

### Для запуска приложения

```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita polkit pkexec
```

### Для сборки RPM пакета

```bash
sudo dnf install rpm-build rpmdevtools
```

## Установка

### Вариант 1: Через скрипт установки (рекомендуется)

```bash
# Установка
sudo ./install.sh

# Проверка установки
./install.sh --check

# Удаление
sudo ./install.sh --uninstall
```

### Вариант 2: Из RPM пакета

```bash
# Сборка RPM пакета
./build-rpm.sh

# Сборка и установка
./build-rpm.sh --install

# После сборки пакеты находятся в:
# - rpm/RPMS/noarch/ (binary пакет)
# - rpm/SRPMS/ (source пакет)
```

### Вариант 3: Локальный запуск без установки

```bash
chmod +x zapret-gui.sh
./zapret-gui.sh
```

## Структура проекта

```
zapret-gui/
├── main.py                          # GTK4/libadwaita GUI
├── zapret_backend.py                # Backend логика
├── zapret_commands.json             # Конфигурация команд
├── zapret-gui.sh                    # Скрипт локального запуска
├── install.sh                       # Скрипт установки/удаления
├── build-rpm.sh                     # Скрипт сборки RPM
├── io.github.snowy-fluffy.zapret-gui.desktop  # Desktop файл
├── io.github.snowy-fluffy.zapret-gui.svg      # Иконка приложения
├── io.github.snowy-fluffy.zapret-gui.policy   # PolicyKit правила
├── rpm/
│   ├── SOURCES/                     # Исходники для RPM
│   ├── SPECS/                       # Spec файл
│   ├── BUILD/                       # Директория сборки
│   ├── RPMS/                        # Binary пакеты
│   └── SRPMS/                       # Source пакеты
└── README.md                        # Этот файл
```

## Использование

### Запуск приложения

После установки приложение доступно:

- В меню приложений GNOME как "Zapret Manager"
- Из терминала: `zapret-gui` или `zapret-manager`

### Главное окно

- **Центральный элемент**: Большой переключатель включения/выключения
- **Индикатор статуса**: Показывает текущее состояние zapret
- **Боковая панель**: Дополнительные функции

### Дополнительные функции

- **Перезапуск**: Перезапуск службы zapret
- **Автозапуск**: Включение/выключение автозагрузки при старте системы
- **Установка**: Установка компонентов zapret
- **Удаление**: Удаление компонентов zapret
- **Обновление**: Обновление до последней версии
- **Логи**: Просмотр логов через journalctl
- **Настройки**: Конфигурация приложения

## Конфигурация

### Системная конфигурация

Файл `/etc/zapret-gui/config.json` содержит настройки по умолчанию:

```json
{
    "zapret_path": "/usr/bin/zapret",
    "service_name": "zapret.service",
    "use_systemctl": true,
    "commands": {
        "start": ["start"],
        "stop": ["stop"],
        "restart": ["restart"],
        "status": ["status"]
    }
}
```

### Пользовательская конфигурация

Приложение проверяет конфигурацию в следующем порядке:

1. `/etc/zapret-gui/config.json` (системная)
2. `~/.config/zapret-gui/config.json` (пользовательская)
3. Встроенная конфигурация

## Безопасность

- Приложение запускается от имени обычного пользователя
- Привилегированные операции выполняются через pkexec/PolicyKit
- Все команды выполняются через subprocess с аргументами списком (без shell-инъекций)
- PolicyKit правила ограничивают список разрешённых команд

## PolicyKit

Для работы привилегированных операций установлен PolicyKit файл:
`/usr/share/polkit-1/actions/io.github.snowy-fluffy.zapret-gui.policy`

Разрешения:
- `io.github.snowy-fluffy.zapret-gui.start` - Запуск zapret
- `io.github.snowy-fluffy.zapret-gui.stop` - Остановка zapret
- `io.github.snowy-fluffy.zapret-gui.restart` - Перезапуск zapret
- `io.github.snowy-fluffy.zapret-gui.enable` - Включение автозапуска
- `io.github.snowy-fluffy.zapret-gui.disable` - Отключение автозапуска
- `io.github.snowy-fluffy.zapret-gui.install` - Установка
- `io.github.snowy-fluffy.zapret-gui.uninstall` - Удаление

## Решение проблем

### Приложение не запускается

Проверьте зависимости:
```bash
sudo dnf install python3 python3-gobject gtk4 libadwaita
```

Проверьте логи:
```bash
journalctl -f | grep zapret-gui
```

### Привилегированные операции не работают

Убедитесь, что polkit активен:
```bash
systemctl status polkit
```

Проверьте наличие PolicyKit файла:
```bash
ls -la /usr/share/polkit-1/actions/io.github.snowy-fluffy.zapret-gui.policy
```

### Статус отображается как "Неизвестно"

- Проверьте, установлен ли zapret: `which zapret`
- Проверьте статус systemd сервиса: `systemctl status zapret`
- Возможно, требуется настройка команд в конфигурации

## Команды zapret

По умолчанию используются следующие команды:

| Действие | Команда |
|----------|---------|
| Старт | `pkexec /usr/bin/zapret start` |
| Стоп | `pkexec /usr/bin/zapret stop` |
| Перезапуск | `pkexec /usr/bin/zapret restart` |
| Статус | `/usr/bin/zapret status` |
| Вкл. автозапуск | `pkexec systemctl enable zapret` |
| Выкл. автозапуск | `pkexec systemctl disable zapret` |

Если команды отличаются в вашей версии zapret, отредактируйте `/etc/zapret-gui/config.json`.

## Лицензия

GPL-3.0-or-later

## Поддержка

Вопросы и предложения направляйте на GitHub: https://github.com/snowy-fluffy/zapret-installer
