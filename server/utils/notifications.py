#!/usr/bin/env python3
"""
Desktop Notification System for Claude-Jester Desktop Extension
Enhanced notification utilities for desktop integration
"""

import platform
import subprocess
import logging
import json
import time
from typing import Optional, Dict, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)

class NotificationType(Enum):
    """Notification types with appropriate icons and priorities"""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUANTUM = "quantum"

class DesktopNotificationManager:
    """Advanced desktop notification system with rich features"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path.home() / '.claude-jester'
        self.system = platform.system().lower()
        self.notification_history = []
        self.rate_limit = {}  # Rate limiting for notification spam
        self._load_preferences()
    
    def _load_preferences(self):
        """Load notification preferences"""
        prefs_file = self.config_dir / 'notification_preferences.json'
        
        default_prefs = {
            'enabled': True,
            'security_alerts': True,
            'performance_insights': False,
            'quantum_results': True,
            'rate_limit_seconds': 5,
            'sound_enabled': True,
            'priority_filter': 'info'  # info, warning, error
        }
        
        try:
            if prefs_file.exists():
                with open(prefs_file) as f:
                    self.preferences = {**default_prefs, **json.load(f)}
            else:
                self.preferences = default_prefs
                self._save_preferences()
        except Exception as e:
            logger.warning(f"Failed to load notification preferences: {e}")
            self.preferences = default_prefs
    
    def _save_preferences(self):
        """Save notification preferences"""
        try:
            prefs_file = self.config_dir / 'notification_preferences.json'
            self.config_dir.mkdir(exist_ok=True)
            with open(prefs_file, 'w') as f:
                json.dump(self.preferences, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save notification preferences: {e}")
    
    def send(self, title: str, message: str, 
             notification_type: NotificationType = NotificationType.INFO,
             actions: Optional[Dict[str, str]] = None,
             persistent: bool = False) -> bool:
        """Send desktop notification with enhanced features"""
        
        if not self.preferences['enabled']:
            return False
        
        try:
            # Record notification
            notification_record = {
                'timestamp': time.time(),
                'title': title,
                'message': message,
                'type': notification_type.value,
                'system': self.system
            }
            
            self.notification_history.append(notification_record)
            
            # Keep only last 100 notifications
            if len(self.notification_history) > 100:
                self.notification_history = self.notification_history[-100:]
            
            # Send platform-specific notification
            success = False
            
            if self.system == "darwin":  # macOS
                success = self._send_macos_notification(title, message, notification_type, actions, persistent)
            elif self.system == "windows":  # Windows
                success = self._send_windows_notification(title, message, notification_type, actions, persistent)
            elif self.system == "linux":  # Linux
                success = self._send_linux_notification(title, message, notification_type, actions, persistent)
            
            logger.debug(f"Notification sent: {title} ({notification_type.value}) - Success: {success}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
    
    def _send_macos_notification(self, title: str, message: str, 
                                notification_type: NotificationType,
                                actions: Optional[Dict[str, str]] = None,
                                persistent: bool = False) -> bool:
        """Send macOS notification using osascript"""
        try:
            script = f'display notification "{message}" with title "🃏 {title}" subtitle "Claude-Jester"'
            
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"macOS notification failed: {e}")
            return False
    
    def _send_windows_notification(self, title: str, message: str,
                                  notification_type: NotificationType,
                                  actions: Optional[Dict[str, str]] = None,
                                  persistent: bool = False) -> bool:
        """Send Windows notification using PowerShell"""
        try:
            powershell_script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null
            
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $template.GetElementsByTagName("text")[0].AppendChild($template.CreateTextNode("🃏 {title}")) | Out-Null
            $template.GetElementsByTagName("text")[1].AppendChild($template.CreateTextNode("{message}")) | Out-Null
            
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude-Jester").Show($toast)
            '''
            
            result = subprocess.run(
                ["powershell", "-Command", powershell_script],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            return result.returncode == 0
                
        except Exception as e:
            logger.error(f"Windows notification failed: {e}")
            return False
    
    def _send_linux_notification(self, title: str, message: str,
                                 notification_type: NotificationType,
                                 actions: Optional[Dict[str, str]] = None,
                                 persistent: bool = False) -> bool:
        """Send Linux notification using notify-send"""
        try:
            cmd = ["notify-send", f"🃏 {title}", message]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Linux notification failed: {e}")
            return False
