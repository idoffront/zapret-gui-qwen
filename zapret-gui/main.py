#!/usr/bin/env python3
"""
Zapret Manager - GTK4/libadwaita GUI приложение
Главный модуль приложения
"""

import sys
import os
from pathlib import Path

# Добавляем путь к модулю
sys.path.insert(0, str(Path(__file__).parent))

import gi
gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib, GObject, Gdk

from zapret_backend import (
    CommandExecutor, 
    ZapretStatus, 
    load_config,
    APP_ID
)


class ZapretWindow(Adw.ApplicationWindow):
    """Главное окно приложения"""
    
    def __init__(self, app: Adw.Application, executor: CommandExecutor):
        super().__init__(application=app)
        self.executor = executor
        self.set_title("Zapret Manager")
        self.set_default_size(600, 700)
        
        # Переменные состояния
        self.current_status = ZapretStatus.UNKNOWN
        self.is_running_action = False
        
        self._setup_ui()
        self._refresh_status()
    
    def _setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Toast overlay для уведомлений
        self.toast_overlay = Adw.ToastOverlay()
        self.set_content(self.toast_overlay)
        
        # Главный контейнер
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.toast_overlay.set_child(main_box)
        
        # Header bar
        header = Adw.HeaderBar()
        header.set_show_end_title_buttons(True)
        main_box.append(header)
        
        # Navigation split view для боковой панели
        self.nav_split = Adw.NavigationSplitView()
        self.nav_split.set_sidebar_width_fraction(0.25)
        self.nav_split.set_min_sidebar_width(200)
        self.nav_split.set_max_sidebar_width(300)
        main_box.append(self.nav_split)
        
        # Боковая панель
        sidebar = self._create_sidebar()
        self.nav_split.set_sidebar(sidebar)
        
        # Основная область контента
        content = self._create_main_content()
        self.nav_split.set_content(content)
    
    def _create_sidebar(self) -> Adw.NavigationPage:
        """Создание боковой панели с дополнительными функциями"""
        nav_page = Adw.NavigationPage(title="Меню")
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        nav_page.set_child(scroll)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        scroll.set_child(vbox)
        
        # Группа: Управление
        control_group = Adw.PreferencesGroup(title="Управление")
        vbox.append(control_group)
        
        actions = [
            ("restart", "Перезапуск", "view-refresh-symbolic"),
            ("stop", "Остановить", "media-playback-stop-symbolic"),
            ("enable_autostart", "Включить автозапуск", "system-run-symbolic"),
            ("disable_autostart", "Отключить автозапуск", "process-stop-symbolic"),
        ]
        
        for action_id, label, icon in actions:
            row = Adw.ActionRow(title=label)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            
            btn = Gtk.Button(label="Выполнить")
            btn.add_css_class("flat")
            btn.connect("clicked", self._on_sidebar_action, action_id)
            row.add_suffix(btn)
            
            control_group.add(row)
        
        # Группа: Установка
        install_group = Adw.PreferencesGroup(title="Установка")
        vbox.append(install_group)
        
        install_actions = [
            ("install", "Установить", "list-add-symbolic"),
            ("uninstall", "Удалить", "list-remove-symbolic"),
            ("update", "Обновить", "view-refresh-symbolic"),
        ]
        
        for action_id, label, icon in install_actions:
            row = Adw.ActionRow(title=label)
            row.add_prefix(Gtk.Image.new_from_icon_name(icon))
            
            btn = Gtk.Button(label="Выполнить")
            btn.add_css_class("flat")
            btn.add_css_class("destructive-action")
            btn.connect("clicked", self._on_sidebar_action, action_id)
            row.add_suffix(btn)
            
            install_group.add(row)
        
        # Группа: Информация
        info_group = Adw.PreferencesGroup(title="Информация")
        vbox.append(info_group)
        
        logs_row = Adw.ActionRow(title="Просмотр логов")
        logs_row.add_prefix(Gtk.Image.new_from_icon_name("document-open-symbolic"))
        logs_btn = Gtk.Button(label="Открыть")
        logs_btn.add_css_class("flat")
        logs_btn.connect("clicked", self._on_show_logs)
        logs_row.add_suffix(logs_btn)
        info_group.add(logs_row)
        
        config_row = Adw.ActionRow(title="Конфигурация")
        config_row.add_prefix(Gtk.Image.new_from_icon_name("preferences-system-symbolic"))
        config_btn = Gtk.Button(label="Открыть")
        config_btn.add_css_class("flat")
        config_btn.connect("clicked", self._on_show_settings)
        config_row.add_suffix(config_btn)
        info_group.add(config_row)
        
        about_row = Adw.ActionRow(title="О приложении")
        about_row.add_prefix(Gtk.Image.new_from_icon_name("help-about-symbolic"))
        about_btn = Gtk.Button(label="Инфо")
        about_btn.add_css_class("flat")
        about_btn.connect("clicked", self._on_show_about)
        about_row.add_suffix(about_btn)
        info_group.add(about_row)
        
        return nav_page
    
    def _create_main_content(self) -> Adw.NavigationPage:
        """Создание основной области с главным переключателем"""
        nav_page = Adw.NavigationPage(title="Zapret Manager")
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        nav_page.set_child(scroll)
        
        main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        main_container.set_margin_start(24)
        main_container.set_margin_end(24)
        main_container.set_margin_top(24)
        main_container.set_margin_bottom(24)
        main_container.set_halign(Gtk.Align.CENTER)
        main_container.set_valign(Gtk.Align.CENTER)
        scroll.set_child(main_container)
        
        # Статусная страница с главным элементом управления
        status_card = Adw.Card()
        status_card.add_css_class("card")
        status_card.set_margin_bottom(12)
        main_container.append(status_card)
        
        card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        card_box.set_margin_start(24)
        card_box.set_margin_end(24)
        card_box.set_margin_top(24)
        card_box.set_margin_bottom(24)
        status_card.set_child(card_box)
        
        # Заголовок
        title_label = Gtk.Label(label="Zapret")
        title_label.add_css_class("title-1")
        title_label.set_halign(Gtk.Align.CENTER)
        card_box.append(title_label)
        
        # Индикатор статуса
        self.status_stack = Gtk.Stack()
        self.status_stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        card_box.append(self.status_stack)
        
        # Страница: Активно
        active_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        active_box.set_halign(Gtk.Align.CENTER)
        self.status_stack.add_named(active_box, "active")
        
        active_icon = Gtk.Image.new_from_icon_name("network-wired-symbolic")
        active_icon.set_pixel_size(64)
        active_icon.add_css_class("success-color")
        active_box.append(active_icon)
        
        active_label = Gtk.Label(label="Активно")
        active_label.add_css_class("heading")
        active_label.add_css_class("success-color")
        active_box.append(active_label)
        
        # Страница: Неактивно
        inactive_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        inactive_box.set_halign(Gtk.Align.CENTER)
        self.status_stack.add_named(inactive_box, "inactive")
        
        inactive_icon = Gtk.Image.new_from_icon_name("network-offline-symbolic")
        inactive_icon.set_pixel_size(64)
        inactive_icon.add_css_class("warning-color")
        inactive_box.append(inactive_icon)
        
        inactive_label = Gtk.Label(label="Остановлено")
        inactive_label.add_css_class("heading")
        inactive_label.add_css_class("warning-color")
        inactive_box.append(inactive_label)
        
        # Страница: Неизвестно
        unknown_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        unknown_box.set_halign(Gtk.Align.CENTER)
        self.status_stack.add_named(unknown_box, "unknown")
        
        unknown_icon = Gtk.Image.new_from_icon_name("dialog-question-symbolic")
        unknown_icon.set_pixel_size(64)
        unknown_icon.add_css_class("accent-color")
        unknown_box.append(unknown_icon)
        
        unknown_label = Gtk.Label(label="Неизвестно")
        unknown_label.add_css_class("heading")
        unknown_label.add_css_class("accent-color")
        unknown_box.append(unknown_label)
        
        # Страница: Выполняется действие
        running_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        running_box.set_halign(Gtk.Align.CENTER)
        self.status_stack.add_named(running_box, "running")
        
        spinner = Adw.Spinner()
        spinner.set_size_request(64, 64)
        running_box.append(spinner)
        
        running_label = Gtk.Label(label="Выполняется...")
        running_label.add_css_class("heading")
        running_box.append(running_label)
        
        # Главный переключатель
        switch_card = Adw.Card()
        switch_card.add_css_class("card")
        card_box.append(switch_card)
        
        switch_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        switch_box.set_margin_start(24)
        switch_box.set_margin_end(24)
        switch_box.set_margin_top(18)
        switch_box.set_margin_bottom(18)
        switch_card.set_child(switch_box)
        
        # Метка
        switch_label = Gtk.Label(label="Включить Zapret")
        switch_label.add_css_class("heading")
        switch_label.set_hexpand(True)
        switch_label.set_xalign(0)
        switch_box.append(switch_label)
        
        # Переключатель
        self.main_switch = Gtk.Switch()
        self.main_switch.set_valign(Gtk.Align.CENTER)
        self.main_switch.set_sensitive(False)  # Будет включён после проверки статуса
        self.main_switch.connect("notify::active", self._on_main_switch_changed)
        switch_box.append(self.main_switch)
        
        # Кнопка обновления статуса
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_btn.add_css_class("circular")
        refresh_btn.add_css_class("flat")
        refresh_btn.set_tooltip_text("Обновить статус")
        refresh_btn.connect("clicked", lambda _: self._refresh_status())
        switch_box.append(refresh_btn)
        
        # Информационная метка
        info_label = Gtk.Label()
        info_label.set_markup("<span size='small' alpha='75%'>Используйте переключатель выше для быстрого включения/выключения</span>")
        info_label.set_wrap(True)
        info_label.set_justify(Gtk.Justification.CENTER)
        main_container.append(info_label)
        
        return nav_page
    
    def _refresh_status(self):
        """Обновление статуса zapret"""
        if self.is_running_action:
            return
        
        self.is_running_action = True
        self._update_ui_for_running("checking")
        
        # Запускаем в отдельном потоке
        GLib.timeout_add(50, self._check_status_async)
    
    def _check_status_async(self):
        """Асинхронная проверка статуса"""
        try:
            status = self.executor.get_status()
            self.current_status = status
            
            GLib.idle_add(self._update_ui_with_status, status)
        except Exception as e:
            GLib.idle_add(self._show_error, f"Ошибка проверки статуса: {str(e)}")
        
        self.is_running_action = False
        return False
    
    def _update_ui_with_status(self, status: ZapretStatus):
        """Обновление UI со статусом"""
        # Обновляем стек статуса
        if status == ZapretStatus.ACTIVE:
            self.status_stack.set_visible_child_name("active")
            self.main_switch.set_active(True)
        elif status == ZapretStatus.INACTIVE:
            self.status_stack.set_visible_child_name("inactive")
            self.main_switch.set_active(False)
        else:
            self.status_stack.set_visible_child_name("unknown")
            self.main_switch.set_active(False)
        
        self.main_switch.set_sensitive(True)
        
        # Показываем toast
        status_names = {
            ZapretStatus.ACTIVE: "Zapret активен",
            ZapretStatus.INACTIVE: "Zapret остановлен",
            ZapretStatus.UNKNOWN: "Статус неизвестен",
        }
        self._show_toast(status_names.get(status, "Неизвестный статус"))
    
    def _update_ui_for_running(self, action: str):
        """Обновление UI во время выполнения действия"""
        self.status_stack.set_visible_child_name("running")
        self.main_switch.set_sensitive(False)
    
    def _on_main_switch_changed(self, switch: Gtk.Switch, param):
        """Обработчик изменения главного переключателя"""
        if self.is_running_action:
            return
        
        is_active = switch.get_active()
        action = "start" if is_active else "stop"
        action_name = "включения" if is_active else "выключения"
        
        self.is_running_action = True
        self._update_ui_for_running(action)
        
        # Подтверждение для привилегированных действий
        if is_active:
            dialog = Adw.AlertDialog()
            dialog.set_heading("Требуется подтверждение")
            dialog.set_body(f"Для {action_name} Zapret потребуются права администратора.")
            dialog.add_response("cancel", "Отмена")
            dialog.add_response("confirm", "Продолжить")
            dialog.set_response_appearance("confirm", Adw.ResponseAppearance.SUGGESTED)
            dialog.connect("response", self._on_confirm_action, action)
            dialog.present(self)
        else:
            self._execute_action(action)
    
    def _on_confirm_action(self, dialog: Adw.AlertDialog, response: str, action: str):
        """Обработчик подтверждения действия"""
        if response == "confirm":
            self._execute_action(action)
        else:
            # Отмена - возвращаем переключатель в исходное состояние
            self.main_switch.set_active(self.current_status == ZapretStatus.ACTIVE)
            self._update_ui_with_status(self.current_status)
            self.is_running_action = False
    
    def _execute_action(self, action: str):
        """Выполнение действия"""
        # Запускаем в отдельном потоке
        GLib.timeout_add(50, self._execute_action_async, action)
    
    def _execute_action_async(self, action: str):
        """Асинхронное выполнение действия"""
        try:
            # Используем pkexec для привилегированных действий
            success, stdout, stderr = self.executor.execute(action, use_pkexec=True)
            
            if success:
                GLib.idle_add(self._on_action_success, action)
            else:
                error_msg = stderr.strip() or stdout.strip() or "Неизвестная ошибка"
                GLib.idle_add(self._on_action_error, error_msg)
                
        except Exception as e:
            GLib.idle_add(self._on_action_error, str(e))
        
        return False
    
    def _on_action_success(self, action: str):
        """Успешное выполнение действия"""
        self._show_toast(f"Действие '{action}' выполнено успешно")
        self._refresh_status()
    
    def _on_action_error(self, error: str):
        """Ошибка выполнения действия"""
        self._show_error(error)
        self._refresh_status()
    
    def _on_sidebar_action(self, btn: Gtk.Button, action: str):
        """Обработчик действий из боковой панели"""
        if self.is_running_action:
            self._show_toast("Пожалуйста, дождитесь завершения текущего действия")
            return
        
        action_names = {
            "restart": "перезапуска",
            "stop": "остановки",
            "enable_autostart": "включения автозапуска",
            "disable_autostart": "отключения автозапуска",
            "install": "установки",
            "uninstall": "удаления",
            "update": "обновления",
        }
        
        action_name = action_names.get(action, action)
        
        # Подтверждение
        dialog = Adw.AlertDialog()
        dialog.set_heading("Подтверждение действия")
        dialog.set_body(f"Вы уверены, что хотите выполнить {action_name}?")
        dialog.add_response("cancel", "Отмена")
        dialog.add_response("confirm", "Выполнить")
        dialog.set_response_appearance("confirm", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_sidebar_confirm, action)
        dialog.present(self)
    
    def _on_sidebar_confirm(self, dialog: Adw.AlertDialog, response: str, action: str):
        """Подтверждение действия из боковой панели"""
        if response == "confirm":
            self.is_running_action = True
            self._update_ui_for_running(action)
            self._execute_action(action)
    
    def _on_show_logs(self, btn: Gtk.Button):
        """Показать логи"""
        logs_dialog = LogsDialog(self, self.executor)
        logs_dialog.present(self)
    
    def _on_show_settings(self, btn: Gtk.Button):
        """Показать настройки"""
        settings_dialog = SettingsDialog(self)
        settings_dialog.present(self)
    
    def _on_show_about(self, btn: Gtk.Button):
        """Показать диалог о приложении"""
        about = Adw.AboutDialog()
        about.set_application_name("Zapret Manager")
        about.set_application_icon(APP_ID)
        about.set_version("1.0.0")
        about.set_developer_name("Snowy-Fluffy community")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_comments("GUI для управления zapret-installer")
        about.set_website("https://github.com/Snowy-Fluffy/zapret-installer")
        about.set_issue_url("https://github.com/Snowy-Fluffy/zapret-installer/issues")
        about.present(self)
    
    def _show_toast(self, message: str):
        """Показать toast-уведомление"""
        toast = Adw.Toast(title=message)
        toast.set_timeout(3)
        self.toast_overlay.add_toast(toast)
    
    def _show_error(self, message: str):
        """Показать ошибку"""
        dialog = Adw.AlertDialog()
        dialog.set_heading("Ошибка")
        dialog.set_body(message)
        dialog.add_response("ok", "OK")
        dialog.set_response_appearance("ok", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.present(self)


class LogsDialog(Adw.Dialog):
    """Диалог просмотра логов"""
    
    def __init__(self, parent: Gtk.Window, executor: CommandExecutor):
        super().__init__()
        self.executor = executor
        self.set_title("Логи Zapret")
        self.set_content_height(500)
        self.set_content_width(600)
        
        self._setup_ui()
        self._load_logs()
    
    def _setup_ui(self):
        """Настройка UI"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(18)
        vbox.set_margin_end(18)
        vbox.set_margin_top(18)
        vbox.set_margin_bottom(18)
        self.set_child(vbox)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.append(toolbar)
        
        refresh_btn = Gtk.Button.new_from_icon_name("view-refresh-symbolic")
        refresh_btn.set_tooltip_text("Обновить")
        refresh_btn.connect("clicked", lambda _: self._load_logs())
        toolbar.append(refresh_btn)
        
        copy_btn = Gtk.Button.new_from_icon_name("edit-copy-symbolic")
        copy_btn.set_tooltip_text("Копировать")
        copy_btn.connect("clicked", self._on_copy)
        toolbar.append(copy_btn)
        
        save_btn = Gtk.Button.new_from_icon_name("document-save-symbolic")
        save_btn.set_tooltip_text("Сохранить в файл")
        save_btn.connect("clicked", self._on_save)
        toolbar.append(save_btn)
        
        clear_btn = Gtk.Button.new_from_icon_name("edit-clear-symbolic")
        clear_btn.set_tooltip_text("Очистить отображение")
        clear_btn.connect("clicked", self._on_clear)
        toolbar.append(clear_btn)
        
        toolbar.append(Gtk.Box())  # Spacer
        
        close_btn = Gtk.Button(label="Закрыть")
        close_btn.connect("clicked", lambda _: self.close())
        toolbar.append(close_btn)
        
        # Text view
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_hexpand(True)
        vbox.append(scroll)
        
        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        
        buffer = self.text_view.get_buffer()
        self.text_tag = buffer.create_tag("monospace")
        
        scroll.set_child(self.text_view)
    
    def _load_logs(self):
        """Загрузка логов"""
        logs = self.executor.get_logs(200)
        buffer = self.text_view.get_buffer()
        buffer.set_text(logs)
    
    def _on_copy(self, btn: Gtk.Button):
        """Копирование логов"""
        buffer = self.text_view.get_buffer()
        text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
        
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.set(text)
    
    def _on_save(self, btn: Gtk.Button):
        """Сохранение логов в файл"""
        file_dialog = Gtk.FileDialog()
        file_dialog.set_title("Сохранить логи")
        file_dialog.set_initial_name("zapret-logs.txt")
        file_dialog.save(self, None, self._on_save_complete)
    
    def _on_save_complete(self, dialog: Gtk.FileDialog, result: Gio.AsyncResult):
        """Завершение сохранения"""
        try:
            file = dialog.save_finish(result)
            buffer = self.text_view.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            
            with open(file.get_path(), 'w') as f:
                f.write(text)
        except Exception:
            pass
    
    def _on_clear(self, btn: Gtk.Button):
        """Очистка отображения"""
        buffer = self.text_view.get_buffer()
        buffer.set_text("")


class SettingsDialog(Adw.Dialog):
    """Диалог настроек"""
    
    def __init__(self, parent: Gtk.Window):
        super().__init__()
        self.set_title("Настройки")
        self.set_content_height(400)
        self.set_content_width(500)
        
        self.config = load_config()
        self._setup_ui()
    
    def _setup_ui(self):
        """Настройка UI"""
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(18)
        vbox.set_margin_end(18)
        vbox.set_margin_top(18)
        vbox.set_margin_bottom(18)
        self.set_child(vbox)
        
        # Toolbar
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.append(toolbar)
        
        toolbar.append(Gtk.Box())  # Spacer
        
        close_btn = Gtk.Button(label="Закрыть")
        close_btn.connect("clicked", lambda _: self.close())
        toolbar.append(close_btn)
        
        # Preferences
        prefs = Adw.PreferencesPage()
        vbox.append(prefs)
        
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(prefs)
        
        # Группа: Путь к бинарнику
        path_group = Adw.PreferencesGroup(title="Путь к исполняемому файлу")
        prefs.add(path_group)
        
        binary_row = Adw.EntryRow(title="Путь к zapret")
        binary_row.set_text(self.config.get("zapret_binary", "/usr/bin/zapret"))
        binary_row.add_suffix(Gtk.Image.new_from_icon_name("folder-symbolic"))
        path_group.add(binary_row)
        
        # Группа: Systemd
        systemd_group = Adw.PreferencesGroup(title="Systemd")
        prefs.add(systemd_group)
        
        service_row = Adw.EntryRow(title="Имя сервиса")
        service_row.set_text(self.config.get("systemd_service", {}).get("name", "zapret.service"))
        systemd_group.add(service_row)
        
        systemctl_row = Adw.SwitchRow(title="Использовать systemctl")
        systemctl_row.set_active(self.config.get("systemd_service", {}).get("use_systemctl", True))
        systemd_group.add(systemctl_row)
        
        # Группа: Таймаут
        timeout_group = Adw.PreferencesGroup(title="Таймауты")
        prefs.add(timeout_group)
        
        timeout_row = Adw.SpinRow.new_with_range(5, 120, 5)
        timeout_row.set_title("Таймаут команд (сек)")
        timeout_row.set_value(self.config.get("timeout_seconds", 30))
        timeout_group.add(timeout_row)
        
        # Info label
        info_label = Gtk.Label()
        info_label.set_markup("<span size='small' alpha='75%'>Изменения вступят в силу после перезапуска приложения</span>")
        info_label.set_wrap(True)
        vbox.append(info_label)


class ZapretApplication(Adw.Application):
    """Основной класс приложения"""
    
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.executor = None
        self.window = None
    
    def do_activate(self):
        """Активация приложения"""
        # Загрузка конфигурации и создание executor
        config = load_config()
        self.executor = CommandExecutor(config)
        
        # Если окно уже существует, показываем его
        if self.window:
            self.window.present()
            return
        
        # Создаём главное окно
        self.window = ZapretWindow(self, self.executor)
        self.window.present()
    
    def do_startup(self):
        """Инициализация при запуске"""
        super().do_startup()
        
        # Установка стилевых классов
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.DEFAULT)


def main():
    """Точка входа"""
    app = ZapretApplication()
    exit_code = app.run(sys.argv)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
