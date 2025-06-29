#!/usr/bin/env python3
"""
Claude-Jester Desktop Extension Server
Enhanced MCP server optimized for Claude Desktop Extensions with desktop integration,
enterprise security, quantum debugging, and Podman containerization.
"""

import json
import sys
import os
import asyncio
import time
import uuid
import logging
import platform
import subprocess
import tempfile
import traceback
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import psutil

# Desktop integration imports
try:
    import aiofiles
    import cryptography
    from cryptography.fernet import Fernet
    import jwt
except ImportError as e:
    logging.warning(f"Optional dependency not available: {e}")

# Set up comprehensive logging
def setup_logging():
    """Configure logging for desktop extension environment"""
    log_level = os.getenv('CLAUDE_JESTER_LOG_LEVEL', 'INFO').upper()
    config_dir = Path(os.getenv('CLAUDE_JESTER_CONFIG_DIR', Path.home() / '.claude-jester'))
    config_dir.mkdir(exist_ok=True)
    
    log_file = config_dir / f'claude-jester-{datetime.now().strftime("%Y%m%d")}.log'
    
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stderr)
        ]
    )
    
    # Rotate logs (keep last 7 days)
    for old_log in config_dir.glob('claude-jester-*.log'):
        if (datetime.now() - datetime.fromtimestamp(old_log.stat().st_mtime)).days > 7:
            old_log.unlink()

setup_logging()
logger = logging.getLogger(__name__)

# ===== DESKTOP EXTENSION FRAMEWORK =====

class DesktopNotification:
    """Cross-platform desktop notifications"""
    
    @staticmethod
    def send(title: str, message: str, notification_type: str = "info"):
        """Send desktop notification"""
        try:
            system = platform.system().lower()
            
            if system == "darwin":  # macOS
                script = f'''
                display notification "{message}" with title "{title}"
                '''
                subprocess.run(["osascript", "-e", script], check=False)
                
            elif system == "windows":  # Windows
                try:
                    import win10toast
                    toaster = win10toast.ToastNotifier()
                    toaster.show_toast(title, message, duration=5)
                except ImportError:
                    # Fallback to Windows notification
                    subprocess.run([
                        "powershell", "-Command",
                        f'[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null; [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null; $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02); $template.GetElementsByTagName("text")[0].AppendChild($template.CreateTextNode("{title}")) | Out-Null; $template.GetElementsByTagName("text")[1].AppendChild($template.CreateTextNode("{message}")) | Out-Null; [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Claude-Jester").Show([Windows.UI.Notifications.ToastNotification]::new($template))'
                    ], check=False)
                    
            elif system == "linux":  # Linux
                subprocess.run([
                    "notify-send", title, message
                ], check=False)
                
        except Exception as e:
            logger.warning(f"Failed to send notification: {e}")

class SecureStorage:
    """Secure storage for sensitive configuration data"""
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.key_file = config_dir / '.encryption_key'
        self._key = self._get_or_create_key()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key"""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            self.key_file.write_bytes(key)
            self.key_file.chmod(0o600)  # Owner read/write only
            return key
    
    def encrypt(self, data: str) -> str:
        """Encrypt sensitive data"""
        try:
            f = Fernet(self._key)
            return f.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            f = Fernet(self._key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return encrypted_data

class DesktopConfig:
    """Desktop extension configuration management"""
    
    def __init__(self):
        self.config_dir = Path(os.getenv('CLAUDE_JESTER_CONFIG_DIR', Path.home() / '.claude-jester'))
        self.data_dir = Path(os.getenv('CLAUDE_JESTER_DATA_DIR', self.config_dir / 'data'))
        self.workspace_dir = None
        self.config_file = self.config_dir / 'config.json'
        
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        self.secure_storage = SecureStorage(self.config_dir)
        self._load_config()
    
    def _load_config(self):
        """Load configuration from desktop extension"""
        try:
            # Desktop extensions pass config via environment variables
            self.security_level = os.getenv('CLAUDE_JESTER_SECURITY_LEVEL', 'balanced')
            self.allowed_languages = os.getenv('CLAUDE_JESTER_ALLOWED_LANGUAGES', 'python,javascript,bash').split(',')
            self.podman_enabled = os.getenv('CLAUDE_JESTER_PODMAN_ENABLED', 'true').lower() == 'true'
            self.quantum_debugging = os.getenv('CLAUDE_JESTER_QUANTUM_ENABLED', 'true').lower() == 'true'
            self.performance_monitoring = os.getenv('CLAUDE_JESTER_PERFORMANCE_MONITORING', 'true').lower() == 'true'
            self.enterprise_mode = os.getenv('CLAUDE_JESTER_ENTERPRISE_MODE', 'false').lower() == 'true'
            self.max_execution_time = int(os.getenv('CLAUDE_JESTER_MAX_EXECUTION_TIME', '30'))
            self.max_memory_mb = int(os.getenv('CLAUDE_JESTER_MAX_MEMORY_MB', '256'))
            self.log_level = os.getenv('CLAUDE_JESTER_LOG_LEVEL', 'INFO')
            
            # Workspace directory
            workspace_env = os.getenv('CLAUDE_JESTER_WORKSPACE_DIRECTORY')
            if workspace_env:
                self.workspace_dir = Path(workspace_env)
                self.workspace_dir.mkdir(parents=True, exist_ok=True)
            else:
                self.workspace_dir = self.data_dir / 'workspace'
                self.workspace_dir.mkdir(exist_ok=True)
            
            # Notification preferences
            self.notifications = {
                'enabled': os.getenv('CLAUDE_JESTER_NOTIFICATIONS_ENABLED', 'true').lower() == 'true',
                'security_alerts': os.getenv('CLAUDE_JESTER_SECURITY_ALERTS', 'true').lower() == 'true',
                'performance_insights': os.getenv('CLAUDE_JESTER_PERFORMANCE_INSIGHTS', 'false').lower() == 'true',
                'quantum_results': os.getenv('CLAUDE_JESTER_QUANTUM_RESULTS', 'true').lower() == 'true'
            }
            
            logger.info(f"Desktop extension configuration loaded: security_level={self.security_level}, workspace={self.workspace_dir}")
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._set_defaults()
    
    def _set_defaults(self):
        """Set default configuration values"""
        self.security_level = 'balanced'
        self.allowed_languages = ['python', 'javascript', 'bash']
        self.podman_enabled = True
        self.quantum_debugging = True
        self.performance_monitoring = True
        self.enterprise_mode = False
        self.max_execution_time = 30
        self.max_memory_mb = 256
        self.log_level = 'INFO'
        self.workspace_dir = self.data_dir / 'workspace'
        self.workspace_dir.mkdir(exist_ok=True)
        self.notifications = {
            'enabled': True,
            'security_alerts': True,
            'performance_insights': False,
            'quantum_results': True
        }

# ===== ENHANCED EXECUTION FRAMEWORK =====

@dataclass
class DesktopExecutionResult:
    """Enhanced execution result with desktop features"""
    success: bool
    output: str
    error: str
    execution_time: float
    memory_usage: int
    container_id: Optional[str] = None
    security_level: str = "unknown"
    method: str = "unknown"
    session_id: str = ""
    timestamp: str = ""
    performance_metrics: Dict[str, Any] = None
    security_analysis: Dict[str, Any] = None
    quantum_insights: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.session_id:
            self.session_id = str(uuid.uuid4())
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.security_analysis is None:
            self.security_analysis = {}
        if self.quantum_insights is None:
            self.quantum_insights = {}

class DesktopAuditLogger:
    """Enhanced audit logging for enterprise compliance"""
    
    def __init__(self, config: DesktopConfig):
        self.config = config
        self.audit_file = config.data_dir / 'audit.log'
        self.session_id = str(uuid.uuid4())
    
    def log_execution(self, result: DesktopExecutionResult, code: str, language: str, user_context: Dict[str, Any] = None):
        """Log execution for audit trail"""
        try:
            audit_entry = {
                'timestamp': result.timestamp,
                'session_id': self.session_id,
                'execution_id': result.session_id,
                'language': language,
                'code_hash': hashlib.sha256(code.encode()).hexdigest(),
                'code_length': len(code),
                'security_level': result.security_level,
                'execution_time': result.execution_time,
                'memory_usage': result.memory_usage,
                'success': result.success,
                'method': result.method,
                'container_id': result.container_id,
                'user_context': user_context or {},
                'platform': {
                    'system': platform.system(),
                    'python_version': platform.python_version(),
                    'architecture': platform.architecture()[0]
                }
            }
            
            if self.config.enterprise_mode:
                # Enhanced logging for enterprise
                audit_entry.update({
                    'security_analysis': result.security_analysis,
                    'performance_metrics': result.performance_metrics,
                    'compliance_flags': self._check_compliance(code, language)
                })
            
            with open(self.audit_file, 'a') as f:
                f.write(json.dumps(audit_entry) + '\n')
                
        except Exception as e:
            logger.error(f"Audit logging failed: {e}")
    
    def _check_compliance(self, code: str, language: str) -> List[str]:
        """Check code for compliance violations"""
        flags = []
        
        # Basic compliance checks
        dangerous_patterns = [
            ('subprocess', 'SUBPROCESS_USAGE'),
            ('os.system', 'SYSTEM_COMMAND'),
            ('eval(', 'EVAL_USAGE'),
            ('exec(', 'EXEC_USAGE'),
            ('import requests', 'NETWORK_ACCESS'),
            ('urllib', 'NETWORK_ACCESS'),
            ('socket', 'SOCKET_USAGE')
        ]
        
        for pattern, flag in dangerous_patterns:
            if pattern in code:
                flags.append(flag)
        
        return flags

class EnhancedPerformanceMonitor:
    """Advanced performance monitoring with desktop integration"""
    
    def __init__(self, config: DesktopConfig):
        self.config = config
        self.metrics_file = config.data_dir / 'performance_metrics.json'
        self.performance_history = []
        self._load_history()
    
    def _load_history(self):
        """Load performance history"""
        try:
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    self.performance_history = json.load(f)
                    # Keep only last 1000 entries
                    self.performance_history = self.performance_history[-1000:]
        except Exception as e:
            logger.warning(f"Failed to load performance history: {e}")
            self.performance_history = []
    
    def record_execution(self, result: DesktopExecutionResult, code: str, language: str):
        """Record execution performance"""
        try:
            metric_entry = {
                'timestamp': result.timestamp,
                'language': language,
                'execution_time': result.execution_time,
                'memory_usage': result.memory_usage,
                'code_complexity': self._calculate_complexity(code),
                'security_level': result.security_level,
                'method': result.method,
                'success': result.success
            }
            
            self.performance_history.append(metric_entry)
            
            # Analyze for performance insights
            insights = self._analyze_performance(metric_entry)
            result.performance_metrics.update(insights)
            
            # Save to file
            with open(self.metrics_file, 'w') as f:
                json.dump(self.performance_history[-1000:], f)
            
            # Send notifications if enabled
            if self.config.notifications['performance_insights'] and insights.get('significant_change'):
                DesktopNotification.send(
                    "Performance Insight",
                    insights.get('message', 'Performance pattern detected'),
                    "info"
                )
                
        except Exception as e:
            logger.error(f"Performance recording failed: {e}")
    
    def _calculate_complexity(self, code: str) -> int:
        """Simple code complexity calculation"""
        # Basic cyclomatic complexity approximation
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'finally', 'with']
        complexity = 1  # Base complexity
        
        for keyword in complexity_keywords:
            complexity += code.count(keyword)
        
        return complexity
    
    def _analyze_performance(self, current_metric: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze performance trends"""
        insights = {}
        
        if len(self.performance_history) < 5:
            return insights
        
        # Recent history for comparison
        recent = self.performance_history[-5:]
        avg_time = sum(m['execution_time'] for m in recent) / len(recent)
        avg_memory = sum(m['memory_usage'] for m in recent) / len(recent)
        
        current_time = current_metric['execution_time']
        current_memory = current_metric['memory_usage']
        
        # Performance change detection
        time_change = (current_time - avg_time) / avg_time if avg_time > 0 else 0
        memory_change = (current_memory - avg_memory) / avg_memory if avg_memory > 0 else 0
        
        if abs(time_change) > 0.5:  # 50% change
            insights['significant_change'] = True
            insights['time_change_percent'] = time_change * 100
            insights['message'] = f"Execution time {'increased' if time_change > 0 else 'decreased'} by {abs(time_change)*100:.1f}%"
        
        if abs(memory_change) > 0.3:  # 30% change
            insights['memory_change_percent'] = memory_change * 100
        
        insights['performance_trend'] = self._calculate_trend()
        
        return insights
    
    def _calculate_trend(self) -> str:
        """Calculate overall performance trend"""
        if len(self.performance_history) < 10:
            return "insufficient_data"
        
        recent_10 = self.performance_history[-10:]
        early_5 = recent_10[:5]
        late_5 = recent_10[5:]
        
        early_avg = sum(m['execution_time'] for m in early_5) / 5
        late_avg = sum(m['execution_time'] for m in late_5) / 5
        
        if late_avg < early_avg * 0.9:
            return "improving"
        elif late_avg > early_avg * 1.1:
            return "degrading"
        else:
            return "stable"

# ===== ENHANCED MCP SERVER =====

class DesktopMCPServer:
    """Enhanced MCP server for desktop extension environment"""
    
    def __init__(self):
        self.config = DesktopConfig()
        self.audit_logger = DesktopAuditLogger(self.config)
        self.performance_monitor = EnhancedPerformanceMonitor(self.config)
        
        # Import enhanced components from standalone server
        from standalone_mcp_server import PodmanCodeExecutor, IntegratedSlashCommands
        
        self.podman_executor = PodmanCodeExecutor() if self.config.podman_enabled else None
        self.slash_commands = IntegratedSlashCommands(self)
        
        logger.info("Claude-Jester Desktop Extension Server initialized")
        
        # Send startup notification
        if self.config.notifications['enabled']:
            DesktopNotification.send(
                "Claude-Jester Started",
                f"Quantum debugging platform ready (Security: {self.config.security_level})",
                "info"
            )
    
    async def execute_code_enhanced(self, language: str, code: str, 
                                   security_level: Optional[str] = None,
                                   enable_quantum: Optional[bool] = None) -> DesktopExecutionResult:
        """Enhanced code execution with desktop features"""
        
        # Validate language is allowed
        if language not in self.config.allowed_languages and language != 'slash':
            return DesktopExecutionResult(
                success=False,
                output="",
                error=f"Language {language} not allowed in current configuration",
                execution_time=0,
                memory_usage=0,
                security_level="denied"
            )
        
        # Use provided security level or default
        sec_level = security_level or self.config.security_level
        
        # Security analysis
        security_analysis = self._analyze_code_security(code, language)
        
        # Send security alert if needed
        if security_analysis.get('risk_level') == 'high' and self.config.notifications['security_alerts']:
            DesktopNotification.send(
                "Security Alert",
                f"High-risk code patterns detected: {', '.join(security_analysis.get('issues', []))}",
                "warning"
            )
        
        start_time = time.time()
        
        try:
            if language == 'slash':
                # Handle slash commands
                output = await self.slash_commands.process_command(code)
                result = DesktopExecutionResult(
                    success=True,
                    output=output,
                    error="",
                    execution_time=time.time() - start_time,
                    memory_usage=0,
                    security_level="command",
                    method="slash_command"
                )
            elif self.podman_executor and sec_level in ['maximum', 'balanced']:
                # Use Podman execution
                exec_result = await self.podman_executor.execute_code(code, language, sec_level)
                result = DesktopExecutionResult(
                    success=exec_result.success,
                    output=exec_result.output,
                    error=exec_result.error,
                    execution_time=exec_result.execution_time,
                    memory_usage=exec_result.memory_usage,
                    container_id=exec_result.container_id,
                    security_level=exec_result.security_level,
                    method=exec_result.method
                )
            else:
                # Fallback to subprocess execution
                output = self._execute_subprocess(code, language)
                result = DesktopExecutionResult(
                    success="Error:" not in output,
                    output=output if "Error:" not in output else "",
                    error=output if "Error:" in output else "",
                    execution_time=time.time() - start_time,
                    memory_usage=0,
                    security_level="subprocess",
                    method="subprocess"
                )
            
            # Add security analysis to result
            result.security_analysis = security_analysis
            
            # Record performance metrics
            if self.config.performance_monitoring:
                self.performance_monitor.record_execution(result, code, language)
            
            # Audit logging
            if self.config.enterprise_mode:
                self.audit_logger.log_execution(result, code, language)
            
            # Store execution artifact
            await self._store_execution_artifact(result, code, language)
            
            return result
            
        except Exception as e:
            error_result = DesktopExecutionResult(
                success=False,
                output="",
                error=f"Execution failed: {str(e)}",
                execution_time=time.time() - start_time,
                memory_usage=0,
                security_level=sec_level,
                method="error"
            )
            error_result.security_analysis = security_analysis
            
            # Log error
            logger.error(f"Code execution failed: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            
            return error_result
    
    def _analyze_code_security(self, code: str, language: str) -> Dict[str, Any]:
        """Enhanced security analysis"""
        analysis = {
            'risk_level': 'low',
            'issues': [],
            'recommendations': [],
            'patterns_detected': []
        }
        
        # High-risk patterns
        high_risk_patterns = [
            ('os.system', 'System command execution'),
            ('subprocess.call', 'Subprocess execution'),
            ('eval(', 'Dynamic code evaluation'),
            ('exec(', 'Dynamic code execution'),
            ('__import__', 'Dynamic imports'),
            ('open(', 'File access'),
        ]
        
        # Medium-risk patterns
        medium_risk_patterns = [
            ('import os', 'Operating system access'),
            ('import subprocess', 'Subprocess module'),
            ('import socket', 'Network socket access'),
            ('urllib', 'Network requests'),
            ('requests', 'HTTP requests'),
        ]
        
        # Check patterns
        high_risk_found = []
        medium_risk_found = []
        
        for pattern, description in high_risk_patterns:
            if pattern in code:
                high_risk_found.append(description)
        
        for pattern, description in medium_risk_patterns:
            if pattern in code:
                medium_risk_found.append(description)
        
        # Determine risk level
        if high_risk_found:
            analysis['risk_level'] = 'high'
            analysis['issues'] = high_risk_found
            analysis['recommendations'].append('Consider using containerized execution')
        elif medium_risk_found:
            analysis['risk_level'] = 'medium'
            analysis['issues'] = medium_risk_found
            analysis['recommendations'].append('Review network and file access patterns')
        
        analysis['patterns_detected'] = high_risk_found + medium_risk_found
        
        return analysis
    
    def _execute_subprocess(self, code: str, language: str) -> str:
        """Fallback subprocess execution"""
        try:
            if language == 'python':
                return self._execute_python_subprocess(code)
            elif language in ['javascript', 'js']:
                return self._execute_javascript_subprocess(code)
            elif language == 'bash':
                return self._execute_bash_subprocess(code)
            else:
                return f"Error: Unsupported language {language}"
        except Exception as e:
            return f"Error: Subprocess execution failed: {str(e)}"
    
    def _execute_python_subprocess(self, code: str) -> str:
        """Python subprocess execution"""
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(code)
                temp_file = f.name
            
            try:
                result = subprocess.run(
                    [sys.executable, temp_file],
                    capture_output=True,
                    text=True,
                    timeout=self.config.max_execution_time,
                    cwd=tempfile.gettempdir()
                )
                
                output = ""
                if result.stdout:
                    output += f"Output:\n{result.stdout.strip()}"
                if result.stderr:
                    if output:
                        output += f"\n\nErrors/Warnings:\n{result.stderr.strip()}"
                    else:
                        output += f"Errors:\n{result.stderr.strip()}"
                
                return output or "Code executed successfully (no output)"
                
            finally:
                try:
                    os.unlink(temp_file)
                except:
                    pass
                    
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out ({self.config.max_execution_time} seconds)"
        except Exception as e:
            return f"Error executing Python code: {str(e)}"
    
    def _execute_javascript_subprocess(self, code: str) -> str:
        """JavaScript subprocess execution"""
        try:
            result = subprocess.run(
                ["node", "-e", code],
                capture_output=True,
                text=True,
                timeout=self.config.max_execution_time
            )
            
            output = ""
            if result.stdout:
                output += f"Output:\n{result.stdout.strip()}"
            if result.stderr:
                if output:
                    output += f"\n\nErrors:\n{result.stderr.strip()}"
                else:
                    output += f"Errors:\n{result.stderr.strip()}"
            
            return output or "Code executed successfully (no output)"
            
        except FileNotFoundError:
            return "Error: Node.js not found. Please install Node.js to run JavaScript code."
        except subprocess.TimeoutExpired:
            return f"Error: Code execution timed out ({self.config.max_execution_time} seconds)"
        except Exception as e:
            return f"Error executing JavaScript code: {str(e)}"
    
    def _execute_bash_subprocess(self, code: str) -> str:
        """Bash subprocess execution"""
        try:
            result = subprocess.run(
                code,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.config.max_execution_time
            )
            
            output = ""
            if result.stdout:
                output += f"Output:\n{result.stdout.strip()}"
            if result.stderr:
                if output:
                    output += f"\n\nErrors:\n{result.stderr.strip()}"
                else:
                    output += f"Errors:\n{result.stderr.strip()}"
            
            return output or "Command executed successfully (no output)"
            
        except subprocess.TimeoutExpired:
            return f"Error: Command execution timed out ({self.config.max_execution_time} seconds)"
        except Exception as e:
            return f"Error executing bash command: {str(e)}"
    
    async def _store_execution_artifact(self, result: DesktopExecutionResult, code: str, language: str):
        """Store execution artifacts for later analysis"""
        try:
            artifacts_dir = self.config.workspace_dir / 'artifacts' / datetime.now().strftime('%Y%m%d')
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            
            artifact_file = artifacts_dir / f"{result.session_id}.json"
            
            artifact_data = {
                'session_id': result.session_id,
                'timestamp': result.timestamp,
                'language': language,
                'code': code,
                'result': asdict(result),
                'platform_info': {
                    'system': platform.system(),
                    'python_version': platform.python_version(),
                    'processor': platform.processor()
                }
            }
            
            async with aiofiles.open(artifact_file, 'w') as f:
                await f.write(json.dumps(artifact_data, indent=2))
            
        except Exception as e:
            logger.warning(f"Failed to store execution artifact: {e}")
    
    # ===== MCP PROTOCOL HANDLERS =====
    
    def handle_initialize(self, request):
        """Handle MCP initialize request"""
        logger.info("Handling initialize request")
        
        try:
            request_id = request.get("id", 1)
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "prompts": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "claude-jester-desktop",
                        "version": "3.1.0",
                        "description": "Claude-Jester Quantum Debugger Desktop Extension"
                    }
                }
            }
            
            logger.info("Initialize request handled successfully")
            return response
        
        except Exception as e:
            logger.error(f"Error handling initialize: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": f"Initialize error: {str(e)}"
                }
            }
    
    def handle_list_tools(self, request):
        """Handle tools/list request"""
        logger.info("Handling list tools request")
        
        try:
            request_id = request.get("id", 1)
            
            tools = [
                {
                    "name": "execute_code",
                    "description": "Execute code with quantum debugging, security analysis, and performance monitoring",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "language": {
                                "type": "string",
                                "enum": ["python", "javascript", "bash", "slash"],
                                "description": "Programming language or 'slash' for advanced commands"
                            },
                            "code": {
                                "type": "string",
                                "description": "Code to execute or slash command"
                            },
                            "security_level": {
                                "type": "string",
                                "enum": ["maximum", "balanced", "development"],
                                "description": "Override default security level"
                            },
                            "enable_quantum": {
                                "type": "boolean",
                                "description": "Enable quantum debugging features"
                            }
                        },
                        "required": ["language", "code"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "quantum_debug",
                    "description": "Advanced quantum debugging with parallel algorithm testing",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "task_description": {
                                "type": "string",
                                "description": "Description of optimization task"
                            },
                            "test_data_size": {
                                "type": "number",
                                "description": "Size of test data"
                            },
                            "iterations": {
                                "type": "number",
                                "description": "Number of iterations"
                            }
                        },
                        "required": ["task_description"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "security_scan",
                    "description": "Comprehensive security analysis of code",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "scan_level": {
                                "type": "string",
                                "enum": ["basic", "comprehensive", "enterprise"]
                            }
                        },
                        "required": ["code", "language"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "performance_benchmark",
                    "description": "Statistical performance analysis",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "string"},
                            "language": {"type": "string"},
                            "iterations": {"type": "number", "minimum": 1, "maximum": 1000}
                        },
                        "required": ["code", "language"],
                        "additionalProperties": False
                    }
                },
                {
                    "name": "system_diagnostics",
                    "description": "System health check and diagnostics",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "component": {
                                "type": "string",
                                "enum": ["all", "podman", "performance", "security", "storage"]
                            },
                            "detailed": {"type": "boolean"}
                        },
                        "required": ["component"],
                        "additionalProperties": False
                    }
                }
            ]
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": tools
                }
            }
            
            logger.info("List tools request handled successfully")
            return response
        
        except Exception as e:
            logger.error(f"Error handling list tools: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": f"List tools error: {str(e)}"
                }
            }
    
    async def handle_call_tool(self, request):
        """Handle tools/call request"""
        logger.info("Handling call tool request")
        
        try:
            request_id = request.get("id", 1)
            params = request.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if not tool_name:
                raise ValueError("Tool name is required")
            
            logger.debug(f"Tool: {tool_name}, Arguments: {arguments}")
            
            if tool_name == "execute_code":
                language = arguments.get("language", "").lower()
                code = arguments.get("code", "")
                security_level = arguments.get("security_level")
                enable_quantum = arguments.get("enable_quantum")
                
                if not code.strip():
                    result_text = "Error: No code provided"
                else:
                    exec_result = await self.execute_code_enhanced(
                        language, code, security_level, enable_quantum
                    )
                    result_text = self._format_execution_result(exec_result)
                    
            elif tool_name == "quantum_debug":
                task = arguments.get("task_description", "")
                result_text = await self._handle_quantum_debug(task, arguments)
                
            elif tool_name == "security_scan":
                code = arguments.get("code", "")
                language = arguments.get("language", "")
                scan_level = arguments.get("scan_level", "basic")
                result_text = self._handle_security_scan(code, language, scan_level)
                
            elif tool_name == "performance_benchmark":
                code = arguments.get("code", "")
                language = arguments.get("language", "")
                iterations = arguments.get("iterations", 10)
                result_text = await self._handle_performance_benchmark(code, language, iterations)
                
            elif tool_name == "system_diagnostics":
                component = arguments.get("component", "all")
                detailed = arguments.get("detailed", False)
                result_text = await self._handle_system_diagnostics(component, detailed)
                
            else:
                result_text = f"Unknown tool: {tool_name}"
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": result_text
                        }
                    ]
                }
            }
            
            logger.info("Call tool request handled successfully")
            return response
            
        except Exception as e:
            error_msg = f"Internal error: {str(e)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": error_msg
                }
            }
    
    def _format_execution_result(self, result: DesktopExecutionResult) -> str:
        """Format execution result for display"""
        status_emoji = "✅" if result.success else "❌"
        
        output = f"🃏 **Claude-Jester Desktop Execution Result:**\n\n"
        output += f"**Status:** {status_emoji} {'Success' if result.success else 'Failed'}\n"
        output += f"**Security Level:** {result.security_level}\n"
        output += f"**Method:** {result.method}\n"
        output += f"**Execution Time:** {result.execution_time:.3f}s\n"
        output += f"**Memory Usage:** {result.memory_usage}MB\n"
        
        if result.container_id:
            output += f"**Container:** {result.container_id}\n"
        
        # Security analysis
        if result.security_analysis:
            risk_level = result.security_analysis.get('risk_level', 'unknown')
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "⚪")
            output += f"**Security Risk:** {risk_emoji} {risk_level.upper()}\n"
            
            if result.security_analysis.get('issues'):
                output += f"**Security Issues:** {', '.join(result.security_analysis['issues'])}\n"
        
        # Performance insights
        if result.performance_metrics:
            if result.performance_metrics.get('significant_change'):
                output += f"**Performance Alert:** {result.performance_metrics.get('message', 'Change detected')}\n"
            
            trend = result.performance_metrics.get('performance_trend')
            if trend:
                trend_emoji = {"improving": "📈", "degrading": "📉", "stable": "➡️"}.get(trend, "")
                output += f"**Performance Trend:** {trend_emoji} {trend.title()}\n"
        
        output += "\n"
        
        if result.output:
            output += f"**Output:**\n```\n{result.output}\n```\n"
        
        if result.error:
            output += f"**Errors:**\n```\n{result.error}\n```\n"
        
        # Session info
        output += f"\n**Session ID:** `{result.session_id}`\n"
        output += f"**Timestamp:** {result.timestamp}\n"
        
        return output
    
    async def _handle_quantum_debug(self, task: str, arguments: Dict[str, Any]) -> str:
        """Handle quantum debugging request"""
        if not self.config.quantum_debugging:
            return "❌ Quantum debugging is disabled in current configuration"
        
        # Use slash commands for quantum debugging
        quantum_command = f"/quantum {task}"
        result = await self.slash_commands.process_command(quantum_command)
        
        # Send notification if enabled
        if self.config.notifications['quantum_results']:
            DesktopNotification.send(
                "Quantum Debugging Complete",
                f"Task: {task[:50]}...",
                "info"
            )
        
        return result
    
    def _handle_security_scan(self, code: str, language: str, scan_level: str) -> str:
        """Handle security scan request"""
        analysis = self._analyze_code_security(code, language)
        
        output = f"🛡️ **Security Analysis Report**\n\n"
        output += f"**Language:** {language}\n"
        output += f"**Scan Level:** {scan_level}\n"
        
        risk_level = analysis.get('risk_level', 'unknown')
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_level, "⚪")
        output += f"**Risk Level:** {risk_emoji} {risk_level.upper()}\n\n"
        
        if analysis.get('issues'):
            output += f"**Security Issues Found:**\n"
            for issue in analysis['issues']:
                output += f"  - {issue}\n"
            output += "\n"
        
        if analysis.get('recommendations'):
            output += f"**Recommendations:**\n"
            for rec in analysis['recommendations']:
                output += f"  - {rec}\n"
            output += "\n"
        
        if analysis.get('patterns_detected'):
            output += f"**Patterns Detected:**\n"
            for pattern in analysis['patterns_detected']:
                output += f"  - {pattern}\n"
        
        return output
    
    async def _handle_performance_benchmark(self, code: str, language: str, iterations: int) -> str:
        """Handle performance benchmark request"""
        if not self.config.performance_monitoring:
            return "❌ Performance monitoring is disabled in current configuration"
        
        # Create benchmark code
        benchmark_command = f"/benchmark {language} {code} {iterations}"
        result = await self.slash_commands.process_command(benchmark_command)
        
        return result
    
    async def _handle_system_diagnostics(self, component: str, detailed: bool) -> str:
        """Handle system diagnostics request"""
        output = f"🔧 **System Diagnostics Report**\n\n"
        
        if component in ["all", "system"]:
            output += f"**System Information:**\n"
            output += f"  - Platform: {platform.system()} {platform.release()}\n"
            output += f"  - Python: {platform.python_version()}\n"
            output += f"  - Architecture: {platform.architecture()[0]}\n"
            output += f"  - Processor: {platform.processor()}\n"
            
            # Memory info
            memory = psutil.virtual_memory()
            output += f"  - Total Memory: {memory.total // (1024**3)}GB\n"
            output += f"  - Available Memory: {memory.available // (1024**3)}GB\n"
            output += f"  - Memory Usage: {memory.percent}%\n\n"
        
        if component in ["all", "podman"]:
            output += f"**Podman Status:**\n"
            if self.podman_executor:
                podman_info = await self.podman_executor.get_system_info()
                if podman_info.get("status") == "available":
                    output += f"  - Status: ✅ Available\n"
                    if detailed and podman_info.get("version"):
                        version_info = podman_info["version"]
                        output += f"  - Version: {version_info.get('Version', 'Unknown')}\n"
                        output += f"  - API Version: {version_info.get('APIVersion', 'Unknown')}\n"
                else:
                    output += f"  - Status: ❌ Not Available\n"
                    output += f"  - Reason: {podman_info.get('reason', 'Unknown')}\n"
            else:
                output += f"  - Status: ⚠️ Disabled in configuration\n"
            output += "\n"
        
        if component in ["all", "performance"]:
            output += f"**Performance Monitoring:**\n"
            output += f"  - Enabled: {'✅' if self.config.performance_monitoring else '❌'}\n"
            
            if self.config.performance_monitoring and hasattr(self, 'performance_monitor'):
                history_count = len(self.performance_monitor.performance_history)
                output += f"  - History Records: {history_count}\n"
                
                if history_count > 0:
                    recent = self.performance_monitor.performance_history[-10:]
                    avg_time = sum(r['execution_time'] for r in recent) / len(recent)
                    output += f"  - Average Execution Time (last 10): {avg_time:.3f}s\n"
            output += "\n"
        
        if component in ["all", "security"]:
            output += f"**Security Configuration:**\n"
            output += f"  - Default Security Level: {self.config.security_level}\n"
            output += f"  - Allowed Languages: {', '.join(self.config.allowed_languages)}\n"
            output += f"  - Enterprise Mode: {'✅' if self.config.enterprise_mode else '❌'}\n"
            output += f"  - Audit Logging: {'✅' if self.config.enterprise_mode else '❌'}\n"
            output += "\n"
        
        if component in ["all", "storage"]:
            output += f"**Storage Information:**\n"
            output += f"  - Config Directory: {self.config.config_dir}\n"
            output += f"  - Data Directory: {self.config.data_dir}\n"
            output += f"  - Workspace Directory: {self.config.workspace_dir}\n"
            
            # Storage usage
            try:
                usage = psutil.disk_usage(str(self.config.data_dir))
                output += f"  - Disk Free: {usage.free // (1024**3)}GB\n"
                output += f"  - Disk Usage: {(usage.used / usage.total) * 100:.1f}%\n"
            except:
                pass
        
        return output

def main():
    """Main entry point for desktop extension server"""
    logger.info("=== Claude-Jester Desktop Extension Server Starting ===")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Mode: Desktop Extension")
    
    server = DesktopMCPServer()
    
    try:
        line_count = 0
        
        for line in sys.stdin:
            line_count += 1
            line = line.strip()
            
            if not line:
                logger.debug(f"Skipping empty line {line_count}")
                continue
            
            logger.debug(f"Processing line {line_count}: {line[:100]}...")
            
            try:
                request = json.loads(line)
                logger.debug(f"Parsed JSON request: {request.get('method', 'unknown')}")
                
                response = None
                method = request.get("method")
                
                if method == "initialize":
                    response = server.handle_initialize(request)
                elif method == "tools/list":
                    response = server.handle_list_tools(request)
                elif method == "tools/call":
                    # Handle async call
                    response = asyncio.run(server.handle_call_tool(request))
                elif method == "notifications/initialized":
                    logger.info("Received initialized notification")
                    continue
                else:
                    logger.warning(f"Unknown method: {method}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request.get("id", 1),
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                
                if response:
                    response_json = json.dumps(response)
                    print(response_json, flush=True)
                    logger.debug(f"Sent response for {method}")
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error on line {line_count}: {e}")
                logger.error(f"Problematic line: {line}")
                try:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32700,
                            "message": f"Parse error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"Request handling error on line {line_count}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                try:
                    error_response = {
                        "jsonrpc": "2.0",
                        "id": None,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
                    print(json.dumps(error_response), flush=True)
                except:
                    pass
                
    except KeyboardInterrupt:
        logger.info("Server stopped by keyboard interrupt")
    except Exception as e:
        logger.error(f"Server error: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        logger.info("Claude-Jester Desktop Extension Server shutting down")
        
        # Send shutdown notification
        try:
            DesktopNotification.send(
                "Claude-Jester Stopped",
                "Quantum debugging platform has been shut down",
                "info"
            )
        except:
            pass

if __name__ == "__main__":
    main()
