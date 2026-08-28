# Zapret Manager Makefile
# Установка приложения в систему

PREFIX = /usr
BINDIR = $(PREFIX)/bin
DESKTOPDIR = $(PREFIX)/share/applications
ICONDIR = $(PREFIX)/share/icons/hicolor/scalable/apps
POLKITDIR = $(PREFIX)/share/polkit-1/actions

APP_NAME = zapret-gui
APP_ID = io.github.snowy-fluffy.zapret-gui

.PHONY: all install uninstall check-deps clean

all: check-deps
	@echo "Zapret Manager готов к установке"
	@echo "Запустите 'sudo make install' для установки"

check-deps:
	@echo "Проверка зависимостей..."
	@command -v python3 >/dev/null 2>&1 || { echo "Требуется python3"; exit 1; }
	@python3 -c "import gi; gi.require_version('Gtk', '4.0'); gi.require_version('Adw', '1')" 2>/dev/null || { \
		echo "Требуется: sudo dnf install gtk4 libadwaita python3-gobject"; \
		exit 1; \
	}
	@echo "Зависимости установлены"

install: check-deps
	@echo "Установка Zapret Manager..."
	
	# Установка скрипта запуска
	install -Dm755 zapret-gui.sh $(BINDIR)/$(APP_NAME)
	
	# Установка desktop файла
	install -Dm644 $(APP_ID).desktop $(DESKTOPDIR)/$(APP_ID).desktop
	
	# Установка иконки
	install -Dm644 $(APP_ID).svg $(ICONDIR)/$(APP_ID).svg
	
	# Установка PolicyKit правил
	install -Dm644 $(APP_ID).policy $(POLKITDIR)/$(APP_ID).policy
	
	# Обновление кэша иконок
	if command -v gtk-update-icon-cache >/dev/null 2>&1; then \
		gtk-update-icon-cache $(ICONDIR)/../.. 2>/dev/null || true; \
	fi
	
	@echo ""
	@echo "✓ Установка завершена"
	@echo ""
	@echo "Приложение доступно в меню GNOME как 'Zapret Manager'"
	@echo "Или запустите командой: $(APP_NAME)"

uninstall:
	@echo "Удаление Zapret Manager..."
	
	rm -f $(BINDIR)/$(APP_NAME)
	rm -f $(DESKTOPDIR)/$(APP_ID).desktop
	rm -f $(ICONDIR)/$(APP_ID).svg
	rm -f $(POLKITDIR)/$(APP_ID).policy
	
	# Обновление кэша иконок
	if command -v gtk-update-icon-cache >/dev/null 2>&1; then \
		gtk-update-icon-cache $(ICONDIR)/../.. 2>/dev/null || true; \
	fi
	
	@echo "✓ Удаление завершено"

clean:
	@echo "Очистка временных файлов..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✓ Очистка завершена"

# Проверка после установки
verify:
	@echo "Проверка установки..."
	@test -f $(BINDIR)/$(APP_NAME) && echo "✓ Скрипт установлен" || echo "✗ Скрипт не найден"
	@test -f $(DESKTOPDIR)/$(APP_ID).desktop && echo "✓ Desktop файл установлен" || echo "✗ Desktop файл не найден"
	@test -f $(ICONDIR)/$(APP_ID).svg && echo "✓ Иконка установлена" || echo "✗ Иконка не найдена"
	@test -f $(POLKITDIR)/$(APP_ID).policy && echo "✓ PolicyKit правила установлены" || echo "✗ PolicyKit правила не найдены"
