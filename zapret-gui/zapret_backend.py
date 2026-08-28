#!/usr/bin/env python3
"""
Zapret Manager - GUI приложение для управления zapret-installer
Автор: Snowy-Fluffy zapret-installer wrapper
License: GPL-3.0
"""

import sys
import os
import json
import subprocess
import re
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# Константы
APP_ID = "io.github.snowy-fluffy.zapret-gui"
DEFAULT_CONFIG_PATH = Path("/etc/zapret-gui/config.json")
USER_CONFIG_PATH = Path.home() / ".config" / "zapret-gui" / "config.json"
DEFAULT_ZAPRET_BINARY = "/usr/bin/zapret"
DEFAULT_SYSTEMD_SERVICE = "zapret.service"


class ZapretStatus(Enum):
    """Статусы zapret"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"
    ERROR = "error"
    RUNNING = "running"


class CommandExecutor:
    """Безопасное выполнение команд с привилегиями"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.zapret_binary = config.get("zapret_binary", DEFAULT_ZAPRET_BINARY)
        self.timeout = config.get("timeout_seconds", 30)
        self.use_systemctl = config.get("systemd_service", {}).get("use_systemctl", True)
        self.service_name = config.get("systemd_service", {}).get("name", DEFAULT_SYSTEMD_SERVICE)
    
    def _build_command(self, action: str) -> List[str]:
        """Построение команды без shell-инъекций"""
        commands_config = self.config.get("commands", {})
        action_config = commands_config.get(action, {})
        args = action_config.get("args", [action])
        
        # Проверяем существование бинарника
        if not Path(self.zapret_binary).exists():
            raise FileNotFoundError(f"Zapret binary not found: {self.zapret_binary}")
        
        # Строим команду как список аргументов (безопасно)
        return [self.zapret_binary] + args
    
    def _build_systemctl_command(self, action: str) -> List[str]:
        """Построение systemctl команды"""
        # Маппинг действий GUI на systemctl команды
        # Для zapret-installer от Snowy-Fluffy используются только systemctl команды
        # Прямые команды zapret (status, start, stop) не существуют
        systemctl_map = {
            "start": ["start", self.service_name],
            "stop": ["stop", self.service_name],
            "restart": ["restart", self.service_name],
            "enable_autostart": ["enable", "--now", self.service_name],
            "disable_autostart": ["disable", "--now", self.service_name],
            "enable": ["enable", self.service_name],
            "disable": ["disable", self.service_name],
            "status": ["is-active", self.service_name],
            "show_status": ["status", self.service_name],
        }
        return ["systemctl"] + systemctl_map.get(action, [action, self.service_name])
    
    def execute(self, action: str, use_pkexec: bool = False) -> Tuple[bool, str, str]:
        """
        Выполнение команды
        
        Returns:
            Tuple[success: bool, stdout: str, stderr: str]
        """
        try:
            # Для zapret-installer от Snowy-Fluffy все операции выполняются через systemctl
            # Прямые команды zapret (status, start, stop) не существуют
            if action in ["start", "stop", "restart", "enable", "disable", "status", "enable_autostart", "disable_autostart", "show_status"]:
                cmd = self._build_systemctl_command(action)
            else:
                cmd = self._build_command(action)
            
            # Если нужны привилегии и use_pkexec=True, добавляем pkexec
            if use_pkexec and action in ["start", "stop", "restart", "enable", "disable", "enable_autostart", "disable_autostart", "install", "uninstall", "update"]:
                cmd = ["pkexec"] + cmd
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, "LANG": "C.UTF-8"}
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            return False, "", f"Command timed out after {self.timeout} seconds"
        except FileNotFoundError as e:
            return False, "", str(e)
        except PermissionError:
            return False, "", "Permission denied. Try running with privileges."
        except Exception as e:
            return False, "", f"Unexpected error: {str(e)}"
    
    def get_status(self) -> ZapretStatus:
        """Определение текущего статуса zapret"""
        # Для zapret-installer от Snowy-Fluffy используется только systemctl
        # Прямые команды zapret (status) не существуют
        try:
            cmd = ["systemctl", "is-active", self.service_name]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                env={**os.environ, "LANG": "C.UTF-8"}
            )
            status_text = result.stdout.strip().lower()
            
            if status_text == "active":
                return ZapretStatus.ACTIVE
            elif status_text in ["inactive", "failed"]:
                return ZapretStatus.INACTIVE
            else:
                return ZapretStatus.UNKNOWN
        except Exception:
            pass
        
        return ZapretStatus.UNKNOWN
    
    def get_logs(self, lines: int = 100) -> str:
        """Получение логов через journalctl"""
        try:
            cmd = ["journalctl", "-u", self.service_name, "-n", str(lines), "--no-pager"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env={**os.environ, "LANG": "C.UTF-8"}
            )
            return result.stdout
        except Exception as e:
            return f"Error getting logs: {str(e)}"


def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации"""
    # Приоритет: пользовательская > системная > встроенная
    config_paths = [USER_CONFIG_PATH, DEFAULT_CONFIG_PATH]
    
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                continue
    
    # Встроенная конфигурация по умолчанию для Snowy-Fluffy zapret-installer
    # Для zapret-installer от Snowy-Fluffy используются ТОЛЬКО systemctl команды
    # Прямые команды zapret (status, start, stop) не существуют
    builtin_config = {
        "zapret_binary": DEFAULT_ZAPRET_BINARY,
        "commands": {
            "status": {"args": [], "use_systemctl_only": True},
            "start": {"args": [], "use_systemctl_only": True},
            "stop": {"args": [], "use_systemctl_only": True},
            "restart": {"args": [], "use_systemctl_only": True},
            "enable": {"args": [], "use_systemctl_only": True},
            "disable": {"args": [], "use_systemctl_only": True},
            "enable_autostart": {"args": [], "use_systemctl_only": True},
            "disable_autostart": {"args": [], "use_systemctl_only": True},
            "install": {"args": ["install"]},
            "uninstall": {"args": ["uninstall"]},
            "update": {"args": ["update"]},
        },
        "systemd_service": {
            "name": DEFAULT_SYSTEMD_SERVICE,
            "use_systemctl": True
        },
        "timeout_seconds": 30,
        "require_privileges": True
    }
    
    return builtin_config
