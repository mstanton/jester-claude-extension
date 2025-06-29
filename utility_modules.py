#!/usr/bin/env python3
"""
Claude-Jester Desktop Extension Utility Modules
Enhanced notification and security utilities for desktop integration
"""

# ===== NOTIFICATIONS.PY =====

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
    
    def _should_show_notification(self, notification_type: NotificationType, title: str) -> bool:
        """Check if notification should be shown based on preferences and rate limiting"""
        if not self.preferences['enabled']:
            return False
        
        # Type-specific filtering
        type_map = {
            NotificationType.SECURITY: 'security_alerts',
            NotificationType.PERFORMANCE: 'performance_insights',
            NotificationType.QUANTUM: 'quantum_results'
        }
        
        if notification_type in type_map:
            if not self.preferences.get(type_map[notification_type], True):
                return False
        
        # Priority filtering
        priority_levels = {'info': 0, 'warning': 1, 'error': 2}
        current_priority = priority_levels.get(notification_type.value, 0)
        min_priority = priority_levels.get(self.preferences['priority_filter'], 0)
        
        if current_priority < min_priority:
            return False
        
        # Rate limiting
        rate_limit_key = f"{notification_type.value}:{title}"
        current_time = time.time()
        
        if rate_limit_key in self.rate_limit:
            last_time = self.rate_limit[rate_limit_key]
            if current_time - last_time < self.preferences['rate_limit_seconds']:
                return False
        
        self.rate_limit[rate_limit_key] = current_time
        return True
    
    def send(self, title: str, message: str, 
             notification_type: NotificationType = NotificationType.INFO,
             actions: Optional[Dict[str, str]] = None,
             persistent: bool = False) -> bool:
        """Send desktop notification with enhanced features"""
        
        if not self._should_show_notification(notification_type, title):
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
            # Enhanced AppleScript with better formatting and actions
            icon_map = {
                NotificationType.INFO: "note",
                NotificationType.SUCCESS: "note", 
                NotificationType.WARNING: "caution",
                NotificationType.ERROR: "stop",
                NotificationType.SECURITY: "stop",
                NotificationType.PERFORMANCE: "note",
                NotificationType.QUANTUM: "note"
            }
            
            icon = icon_map.get(notification_type, "note")
            
            script_parts = [
                f'display notification "{message}"',
                f'with title "🃏 {title}"',
                f'subtitle "Claude-Jester"'
            ]
            
            if self.preferences.get('sound_enabled', True):
                sound_map = {
                    NotificationType.ERROR: "Basso",
                    NotificationType.SECURITY: "Sosumi", 
                    NotificationType.WARNING: "Ping",
                    NotificationType.SUCCESS: "Glass",
                    NotificationType.QUANTUM: "Tink"
                }
                sound = sound_map.get(notification_type, "default")
                script_parts.append(f'sound name "{sound}"')
            
            script = ' '.join(script_parts)
            
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
        """Send Windows notification using PowerShell and Windows API"""
        try:
            # Try win10toast first (if available)
            try:
                import win10toast
                toaster = win10toast.ToastNotifier()
                
                icon_path = None
                if hasattr(self, 'config_dir'):
                    icon_file = self.config_dir / 'assets' / 'claude-jester-icon.ico'
                    if icon_file.exists():
                        icon_path = str(icon_file)
                
                duration = 10 if persistent else 5
                
                toaster.show_toast(
                    f"🃏 {title}",
                    message,
                    icon_path=icon_path,
                    duration=duration,
                    threaded=True
                )
                return True
                
            except ImportError:
                # Fallback to PowerShell
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
            cmd = ["notify-send"]
            
            # Add urgency level
            urgency_map = {
                NotificationType.INFO: "normal",
                NotificationType.SUCCESS: "normal",
                NotificationType.WARNING: "normal", 
                NotificationType.ERROR: "critical",
                NotificationType.SECURITY: "critical",
                NotificationType.PERFORMANCE: "low",
                NotificationType.QUANTUM: "normal"
            }
            
            urgency = urgency_map.get(notification_type, "normal")
            cmd.extend(["-u", urgency])
            
            # Add icon
            icon_map = {
                NotificationType.INFO: "dialog-information",
                NotificationType.SUCCESS: "dialog-information",
                NotificationType.WARNING: "dialog-warning",
                NotificationType.ERROR: "dialog-error", 
                NotificationType.SECURITY: "security-high",
                NotificationType.PERFORMANCE: "utilities-system-monitor",
                NotificationType.QUANTUM: "applications-science"
            }
            
            icon = icon_map.get(notification_type, "dialog-information")
            cmd.extend(["-i", icon])
            
            # Add expiration time
            if persistent:
                cmd.extend(["-t", "0"])  # No expiration
            else:
                cmd.extend(["-t", "5000"])  # 5 seconds
            
            # Add title and message
            cmd.extend([f"🃏 {title}", message])
            
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
    
    def get_notification_history(self, limit: int = 50) -> list:
        """Get recent notification history"""
        return self.notification_history[-limit:]
    
    def clear_history(self):
        """Clear notification history"""
        self.notification_history.clear()
    
    def update_preferences(self, new_preferences: Dict[str, Any]):
        """Update notification preferences"""
        self.preferences.update(new_preferences)
        self._save_preferences()

# ===== SECURITY.PY =====

import re
import hashlib
import ast
import inspect
from typing import List, Dict, Set, Any, Optional, Tuple
from dataclasses import dataclass
import keyword

@dataclass
class SecurityViolation:
    """Represents a security violation found in code"""
    severity: str  # low, medium, high, critical
    category: str  # injection, file_access, network, system, etc.
    description: str
    line_number: Optional[int] = None
    suggestion: Optional[str] = None
    pattern: Optional[str] = None

class SecurityPattern:
    """Represents a security pattern to check"""
    def __init__(self, pattern: str, severity: str, category: str, 
                 description: str, suggestion: str = ""):
        self.pattern = pattern
        self.severity = severity
        self.category = category
        self.description = description
        self.suggestion = suggestion

class AdvancedSecurityAnalyzer:
    """Advanced security analyzer with multiple detection methods"""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.ast_checkers = self._initialize_ast_checkers()
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_patterns(self) -> List[SecurityPattern]:
        """Initialize security patterns for detection"""
        return [
            # Critical patterns
            SecurityPattern(
                r"os\.system\s*\(",
                "critical", "system",
                "Direct system command execution",
                "Use subprocess with specific arguments instead"
            ),
            SecurityPattern(
                r"eval\s*\(",
                "critical", "injection",
                "Dynamic code evaluation - code injection risk",
                "Avoid eval() - use specific parsing functions"
            ),
            SecurityPattern(
                r"exec\s*\(",
                "critical", "injection", 
                "Dynamic code execution - code injection risk",
                "Avoid exec() - use specific parsing functions"
            ),
            SecurityPattern(
                r"subprocess\.(call|run|Popen)\s*\(\s*shell\s*=\s*True",
                "high", "system",
                "Shell command execution with shell=True",
                "Use shell=False and pass arguments as list"
            ),
            
            # High severity patterns
            SecurityPattern(
                r"__import__\s*\(",
                "high", "injection",
                "Dynamic module import",
                "Use static imports when possible"
            ),
            SecurityPattern(
                r"compile\s*\(",
                "high", "injection",
                "Dynamic code compilation", 
                "Avoid dynamic compilation"
            ),
            SecurityPattern(
                r"open\s*\(\s*['\"].*\.\./",
                "high", "file_access",
                "Path traversal attempt in file access",
                "Validate and sanitize file paths"
            ),
            
            # Medium severity patterns  
            SecurityPattern(
                r"import\s+os\b",
                "medium", "system",
                "Operating system access imported",
                "Review OS access requirements"
            ),
            SecurityPattern(
                r"import\s+subprocess\b",
                "medium", "system", 
                "Subprocess module imported",
                "Review subprocess usage for security"
            ),
            SecurityPattern(
                r"import\s+(urllib|requests|httplib)\b",
                "medium", "network",
                "Network access module imported",
                "Review network access requirements"
            ),
            SecurityPattern(
                r"import\s+socket\b",
                "medium", "network",
                "Socket programming imported",
                "Review socket usage for security"
            ),
            
            # Low severity patterns
            SecurityPattern(
                r"import\s+pickle\b",
                "low", "serialization",
                "Pickle module can execute arbitrary code",
                "Consider safer serialization formats like JSON"
            ),
            SecurityPattern(
                r"input\s*\(",
                "low", "input",
                "User input without validation",
                "Validate and sanitize user input"
            )
        ]
    
    def _initialize_ast_checkers(self) -> List[callable]:
        """Initialize AST-based security checkers"""
        return [
            self._check_dangerous_functions,
            self._check_import_statements,
            self._check_string_operations,
            self._check_file_operations,
            self._check_network_operations
        ]
    
    def _initialize_compliance_rules(self) -> Dict[str, List[str]]:
        """Initialize compliance rules for different standards"""
        return {
            "OWASP": [
                "injection", "broken_auth", "sensitive_data", 
                "xxe", "broken_access", "security_misconfig",
                "xss", "insecure_deser", "vulnerable_components", "logging"
            ],
            "SOC2": [
                "access_control", "encryption", "monitoring", 
                "backup", "incident_response"
            ],
            "ISO27001": [
                "risk_assessment", "access_management", "cryptography",
                "physical_security", "operational_security"
            ]
        }
    
    def analyze_code(self, code: str, language: str = "python") -> Dict[str, Any]:
        """Comprehensive security analysis of code"""
        violations = []
        
        try:
            # Pattern-based analysis
            pattern_violations = self._analyze_patterns(code)
            violations.extend(pattern_violations)
            
            # AST-based analysis (for Python)
            if language.lower() == "python":
                try:
                    tree = ast.parse(code)
                    ast_violations = self._analyze_ast(tree, code)
                    violations.extend(ast_violations)
                except SyntaxError as e:
                    violations.append(SecurityViolation(
                        "medium", "syntax",
                        f"Syntax error may indicate obfuscated code: {e}",
                        line_number=getattr(e, 'lineno', None)
                    ))
            
            # Complexity analysis
            complexity_score = self._analyze_complexity(code)
            if complexity_score > 50:
                violations.append(SecurityViolation(
                    "low", "complexity",
                    f"High code complexity ({complexity_score}) may hide security issues",
                    suggestion="Break down complex functions for easier review"
                ))
            
            # Generate overall assessment
            risk_level = self._calculate_risk_level(violations)
            compliance_status = self._check_compliance_violations(violations)
            
            return {
                "risk_level": risk_level,
                "violations": [self._violation_to_dict(v) for v in violations],
                "compliance_status": compliance_status,
                "complexity_score": complexity_score,
                "total_violations": len(violations),
                "critical_violations": len([v for v in violations if v.severity == "critical"]),
                "recommendations": self._generate_recommendations(violations)
            }
            
        except Exception as e:
            logger.error(f"Security analysis failed: {e}")
            return {
                "risk_level": "unknown",
                "violations": [],
                "error": str(e),
                "compliance_status": {},
                "complexity_score": 0,
                "total_violations": 0,
                "critical_violations": 0,
                "recommendations": []
            }
    
    def _analyze_patterns(self, code: str) -> List[SecurityViolation]:
        """Analyze code using regex patterns"""
        violations = []
        lines = code.split('\n')
        
        for pattern_obj in self.patterns:
            matches = re.finditer(pattern_obj.pattern, code, re.IGNORECASE | re.MULTILINE)
            
            for match in matches:
                # Find line number
                line_number = code[:match.start()].count('\n') + 1
                
                violation = SecurityViolation(
                    severity=pattern_obj.severity,
                    category=pattern_obj.category,
                    description=pattern_obj.description,
                    line_number=line_number,
                    suggestion=pattern_obj.suggestion,
                    pattern=pattern_obj.pattern
                )
                violations.append(violation)
        
        return violations
    
    def _analyze_ast(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Analyze code using AST parsing"""
        violations = []
        
        for checker in self.ast_checkers:
            try:
                checker_violations = checker(tree, code)
                violations.extend(checker_violations)
            except Exception as e:
                logger.warning(f"AST checker failed: {e}")
        
        return violations
    
    def _check_dangerous_functions(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous function calls"""
        violations = []
        dangerous_functions = {
            'eval': 'critical',
            'exec': 'critical', 
            'compile': 'high',
            '__import__': 'high',
            'getattr': 'medium',
            'setattr': 'medium',
            'delattr': 'medium'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name in dangerous_functions:
                        violations.append(SecurityViolation(
                            severity=dangerous_functions[func_name],
                            category="dangerous_function",
                            description=f"Use of dangerous function: {func_name}",
                            line_number=node.lineno,
                            suggestion=f"Avoid using {func_name} function"
                        ))
        
        return violations
    
    def _check_import_statements(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for suspicious imports"""
        violations = []
        suspicious_modules = {
            'os': 'medium',
            'subprocess': 'medium', 
            'socket': 'medium',
            'urllib': 'medium',
            'requests': 'medium',
            'pickle': 'low',
            'marshal': 'low',
            'ctypes': 'high'
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in suspicious_modules:
                        violations.append(SecurityViolation(
                            severity=suspicious_modules[module_name],
                            category="suspicious_import",
                            description=f"Import of potentially dangerous module: {module_name}",
                            line_number=node.lineno,
                            suggestion=f"Review usage of {module_name} module"
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    if module_name in suspicious_modules:
                        violations.append(SecurityViolation(
                            severity=suspicious_modules[module_name],
                            category="suspicious_import", 
                            description=f"Import from potentially dangerous module: {module_name}",
                            line_number=node.lineno,
                            suggestion=f"Review usage of {module_name} module"
                        ))
        
        return violations
    
    def _check_string_operations(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for dangerous string operations"""
        violations = []
        
        for node in ast.walk(tree):
            # Check for string formatting that might lead to injection
            if isinstance(node, ast.Call):
                if (isinstance(node.func, ast.Attribute) and 
                    node.func.attr == 'format'):
                    violations.append(SecurityViolation(
                        severity="low",
                        category="string_injection",
                        description="String formatting may be vulnerable to injection",
                        line_number=node.lineno,
                        suggestion="Validate and sanitize format arguments"
                    ))
            
            # Check for f-strings with user input
            elif isinstance(node, ast.JoinedStr):
                violations.append(SecurityViolation(
                    severity="low", 
                    category="string_injection",
                    description="F-string may include unsanitized data",
                    line_number=node.lineno,
                    suggestion="Ensure f-string values are properly sanitized"
                ))
        
        return violations
    
    def _check_file_operations(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for unsafe file operations"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id == 'open':
                    # Check for path traversal patterns in file operations
                    if node.args:
                        if isinstance(node.args[0], ast.Constant):
                            path = str(node.args[0].value)
                            if '..' in path or path.startswith('/'):
                                violations.append(SecurityViolation(
                                    severity="high",
                                    category="path_traversal",
                                    description="Potential path traversal in file operation",
                                    line_number=node.lineno,
                                    suggestion="Validate and sanitize file paths"
                                ))
        
        return violations
    
    def _check_network_operations(self, tree: ast.AST, code: str) -> List[SecurityViolation]:
        """Check for network-related security issues"""
        violations = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # Check for URL construction that might be vulnerable
                if (isinstance(node.func, ast.Attribute) and 
                    hasattr(node.func.value, 'id') and
                    node.func.value.id in ['urllib', 'requests']):
                    violations.append(SecurityViolation(
                        severity="medium",
                        category="network_access",
                        description="Network request - verify URL validation",
                        line_number=node.lineno,
                        suggestion="Validate URLs and use HTTPS"
                    ))
        
        return violations
    
    def _analyze_complexity(self, code: str) -> int:
        """Calculate code complexity score"""
        complexity = 1  # Base complexity
        
        # Count control structures
        control_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with']
        for keyword in control_keywords:
            complexity += code.count(keyword)
        
        # Count function definitions
        complexity += code.count('def ')
        complexity += code.count('class ')
        
        # Count nested structures (rough approximation)
        lines = code.split('\n')
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(max_indent, indent // 4)  # Assuming 4-space indents
        
        complexity += max_indent * 2
        
        return complexity
    
    def _calculate_risk_level(self, violations: List[SecurityViolation]) -> str:
        """Calculate overall risk level"""
        if not violations:
            return "low"
        
        severity_weights = {
            "critical": 10,
            "high": 5,
            "medium": 2, 
            "low": 1
        }
        
        total_score = sum(severity_weights.get(v.severity, 0) for v in violations)
        
        if total_score >= 20:
            return "critical"
        elif total_score >= 10:
            return "high"
        elif total_score >= 5:
            return "medium"
        else:
            return "low"
    
    def _check_compliance_violations(self, violations: List[SecurityViolation]) -> Dict[str, Any]:
        """Check for compliance violations"""
        compliance_status = {}
        
        for standard, categories in self.compliance_rules.items():
            violations_in_standard = []
            for violation in violations:
                if violation.category in categories or any(cat in violation.description.lower() for cat in categories):
                    violations_in_standard.append(violation)
            
            compliance_status[standard] = {
                "violations": len(violations_in_standard),
                "status": "fail" if violations_in_standard else "pass",
                "risk_areas": list(set(v.category for v in violations_in_standard))
            }
        
        return compliance_status
    
    def _generate_recommendations(self, violations: List[SecurityViolation]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Category-based recommendations
        categories = set(v.category for v in violations)
        
        if "injection" in categories:
            recommendations.append("Implement input validation and sanitization")
            recommendations.append("Use parameterized queries and prepared statements")
        
        if "system" in categories:
            recommendations.append("Minimize system-level access")
            recommendations.append("Use containerization for additional isolation")
        
        if "network" in categories:
            recommendations.append("Validate all network requests and responses")
            recommendations.append("Use HTTPS for all network communications")
        
        if "file_access" in categories:
            recommendations.append("Implement proper file access controls")
            recommendations.append("Validate and sanitize all file paths")
        
        # Severity-based recommendations
        critical_violations = [v for v in violations if v.severity == "critical"]
        if critical_violations:
            recommendations.append("Address critical security violations immediately")
            recommendations.append("Consider code review by security expert")
        
        return recommendations
    
    def _violation_to_dict(self, violation: SecurityViolation) -> Dict[str, Any]:
        """Convert violation to dictionary"""
        return {
            "severity": violation.severity,
            "category": violation.category,
            "description": violation.description,
            "line_number": violation.line_number,
            "suggestion": violation.suggestion,
            "pattern": violation.pattern
        }

# Usage examples and testing
if __name__ == "__main__":
    # Test notification system
    print("Testing notification system...")
    notification_manager = DesktopNotificationManager()
    
    notification_manager.send(
        "Test Notification",
        "Claude-Jester desktop integration test",
        NotificationType.INFO
    )
    
    # Test security analyzer
    print("Testing security analyzer...")
    security_analyzer = AdvancedSecurityAnalyzer()
    
    test_code = """
import os
import subprocess

def dangerous_function():
    os.system("rm -rf /")
    eval("malicious_code")
    subprocess.run("dangerous command", shell=True)

def safe_function():
    result = 2 + 2
    print(f"Result: {result}")
    return result
"""
    
    analysis = security_analyzer.analyze_code(test_code)
    print(f"Security analysis complete:")
    print(f"Risk level: {analysis['risk_level']}")
    print(f"Total violations: {analysis['total_violations']}")
    print(f"Critical violations: {analysis['critical_violations']}")
