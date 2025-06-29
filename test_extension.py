#!/usr/bin/env python3
"""
Comprehensive Test Suite for Claude-Jester Desktop Extension
Tests all components including MCP protocol, security, performance, and desktop integration
"""

import pytest
import asyncio
import json
import tempfile
import os
import sys
import platform
import time
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import zipfile

# Add server to Python path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

# Test fixtures and utilities
@pytest.fixture
def temp_config_dir():
    """Create temporary configuration directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir)
        # Set environment variables for testing
        os.environ['CLAUDE_JESTER_CONFIG_DIR'] = str(config_path)
        os.environ['CLAUDE_JESTER_DATA_DIR'] = str(config_path / 'data')
        yield config_path
        # Cleanup environment
        os.environ.pop('CLAUDE_JESTER_CONFIG_DIR', None)
        os.environ.pop('CLAUDE_JESTER_DATA_DIR', None)

@pytest.fixture
def mock_podman():
    """Mock Podman availability"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "podman version 4.0.0"
        yield mock_run

@pytest.fixture
async def desktop_server(temp_config_dir, mock_podman):
    """Create desktop server instance for testing"""
    # Import after setting up environment
    from claude_jester_desktop import DesktopMCPServer
    
    server = DesktopMCPServer()
    yield server
    
    # Cleanup
    if hasattr(server, 'podman_executor') and server.podman_executor:
        try:
            await server.podman_executor.cleanup_session()
        except:
            pass

# ===== CORE FUNCTIONALITY TESTS =====

class TestDesktopConfig:
    """Test desktop configuration management"""
    
    def test_config_initialization(self, temp_config_dir):
        """Test configuration directory setup"""
        from claude_jester_desktop import DesktopConfig
        
        config = DesktopConfig()
        
        assert config.config_dir.exists()
        assert config.data_dir.exists()
        assert config.workspace_dir.exists()
        assert config.security_level in ['maximum', 'balanced', 'development']
        assert isinstance(config.allowed_languages, list)
        assert len(config.allowed_languages) > 0
    
    def test_environment_variable_loading(self, temp_config_dir):
        """Test loading configuration from environment variables"""
        # Set test environment variables
        os.environ['CLAUDE_JESTER_SECURITY_LEVEL'] = 'maximum'
        os.environ['CLAUDE_JESTER_ALLOWED_LANGUAGES'] = 'python,javascript'
        os.environ['CLAUDE_JESTER_QUANTUM_ENABLED'] = 'false'
        
        try:
            from claude_jester_desktop import DesktopConfig
            config = DesktopConfig()
            
            assert config.security_level == 'maximum'
            assert config.allowed_languages == ['python', 'javascript']
            assert config.quantum_debugging == False
            
        finally:
            # Cleanup
            os.environ.pop('CLAUDE_JESTER_SECURITY_LEVEL', None)
            os.environ.pop('CLAUDE_JESTER_ALLOWED_LANGUAGES', None)
            os.environ.pop('CLAUDE_JESTER_QUANTUM_ENABLED', None)

class TestSecureStorage:
    """Test secure storage functionality"""
    
    def test_encryption_decryption(self, temp_config_dir):
        """Test data encryption and decryption"""
        from claude_jester_desktop import SecureStorage
        
        storage = SecureStorage(temp_config_dir)
        
        test_data = "sensitive_api_key_12345"
        encrypted = storage.encrypt(test_data)
        decrypted = storage.decrypt(encrypted)
        
        assert encrypted != test_data
        assert decrypted == test_data
        assert len(encrypted) > len(test_data)
    
    def test_key_persistence(self, temp_config_dir):
        """Test encryption key persistence"""
        from claude_jester_desktop import SecureStorage
        
        # Create first storage instance
        storage1 = SecureStorage(temp_config_dir)
        test_data = "test_data"
        encrypted1 = storage1.encrypt(test_data)
        
        # Create second storage instance (should use same key)
        storage2 = SecureStorage(temp_config_dir)
        decrypted2 = storage2.decrypt(encrypted1)
        
        assert decrypted2 == test_data

class TestDesktopNotifications:
    """Test desktop notification system"""
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_macos_notification(self, mock_run, mock_system):
        """Test macOS notification"""
        mock_system.return_value = "Darwin"
        mock_run.return_value.returncode = 0
        
        from claude_jester_desktop import DesktopNotification
        
        DesktopNotification.send("Test Title", "Test Message")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "osascript" in args
        assert "display notification" in ' '.join(args)
    
    @patch('platform.system')
    @patch('subprocess.run')
    def test_linux_notification(self, mock_run, mock_system):
        """Test Linux notification"""
        mock_system.return_value = "Linux"
        mock_run.return_value.returncode = 0
        
        from claude_jester_desktop import DesktopNotification
        
        DesktopNotification.send("Test Title", "Test Message")
        
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert "notify-send" in args

# ===== MCP PROTOCOL TESTS =====

class TestMCPProtocol:
    """Test MCP protocol compliance"""
    
    def test_initialize_request(self, desktop_server):
        """Test MCP initialize protocol"""
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {}
        }
        
        response = desktop_server.handle_initialize(request)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 1
        assert "result" in response
        assert "serverInfo" in response["result"]
        assert response["result"]["serverInfo"]["name"] == "claude-jester-desktop"
        assert "version" in response["result"]["serverInfo"]
    
    def test_list_tools_request(self, desktop_server):
        """Test tools/list protocol"""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }
        
        response = desktop_server.handle_list_tools(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "tools" in response["result"]
        
        tools = response["result"]["tools"]
        tool_names = [tool["name"] for tool in tools]
        
        expected_tools = [
            "execute_code",
            "quantum_debug", 
            "security_scan",
            "performance_benchmark",
            "system_diagnostics"
        ]
        
        for expected_tool in expected_tools:
            assert expected_tool in tool_names
        
        # Validate tool schemas
        for tool in tools:
            assert "name" in tool
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"
    
    @pytest.mark.asyncio
    async def test_execute_code_tool(self, desktop_server):
        """Test execute_code tool"""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "execute_code",
                "arguments": {
                    "language": "python",
                    "code": "print('Hello from test')"
                }
            }
        }
        
        response = await desktop_server.handle_call_tool(request)
        
        assert response["jsonrpc"] == "2.0"
        assert "result" in response
        assert "content" in response["result"]
        assert len(response["result"]["content"]) > 0
        
        content = response["result"]["content"][0]["text"]
        assert "Hello from test" in content
        assert "✅" in content  # Success indicator

# ===== CODE EXECUTION TESTS =====

class TestCodeExecution:
    """Test code execution functionality"""
    
    @pytest.mark.asyncio
    async def test_python_execution(self, desktop_server):
        """Test Python code execution"""
        result = await desktop_server.execute_code_enhanced(
            "python", 
            "result = 2 + 2\nprint(f'Result: {result}')"
        )
        
        assert result.success
        assert "Result: 4" in result.output
        assert result.execution_time > 0
        assert result.security_level in ["subprocess", "balanced", "maximum"]
        assert result.session_id
        assert result.timestamp
    
    @pytest.mark.asyncio 
    async def test_javascript_execution(self, desktop_server):
        """Test JavaScript code execution"""
        result = await desktop_server.execute_code_enhanced(
            "javascript",
            "console.log('JavaScript test:', 3 * 7);"
        )
        
        # JavaScript might not be available in test environment
        if result.success:
            assert "JavaScript test: 21" in result.output
        else:
            assert "Node.js not found" in result.error or "not allowed" in result.error
    
    @pytest.mark.asyncio
    async def test_language_restriction(self, desktop_server):
        """Test language restriction enforcement"""
        # Temporarily restrict languages
        original_languages = desktop_server.config.allowed_languages
        desktop_server.config.allowed_languages = ["python"]
        
        try:
            result = await desktop_server.execute_code_enhanced(
                "javascript",
                "console.log('This should be blocked');"
            )
            
            assert not result.success
            assert "not allowed" in result.error
            
        finally:
            desktop_server.config.allowed_languages = original_languages
    
    @pytest.mark.asyncio
    async def test_slash_commands(self, desktop_server):
        """Test slash command execution"""
        result = await desktop_server.execute_code_enhanced(
            "slash",
            "/help"
        )
        
        assert result.success
        assert "Claude-Jester" in result.output
        assert result.security_level == "command"

# ===== SECURITY TESTS =====

class TestSecurity:
    """Test security analysis and enforcement"""
    
    def test_security_analysis_high_risk(self, desktop_server):
        """Test high-risk code detection"""
        dangerous_code = """
import os
import subprocess
os.system("rm -rf /")
subprocess.call(["dangerous", "command"])
"""
        
        analysis = desktop_server._analyze_code_security(dangerous_code, "python")
        
        assert analysis["risk_level"] == "high"
        assert len(analysis["issues"]) > 0
        assert "System command execution" in analysis["issues"]
        assert len(analysis["recommendations"]) > 0
    
    def test_security_analysis_medium_risk(self, desktop_server):
        """Test medium-risk code detection"""
        medium_code = """
import os
import requests
data = requests.get("https://api.example.com")
print(os.getcwd())
"""
        
        analysis = desktop_server._analyze_code_security(medium_code, "python")
        
        assert analysis["risk_level"] == "medium"
        assert "Operating system access" in analysis["issues"] or "HTTP requests" in analysis["issues"]
    
    def test_security_analysis_low_risk(self, desktop_server):
        """Test low-risk code detection"""
        safe_code = """
def calculate_fibonacci(n):
    if n <= 1:
        return n
    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)

print(calculate_fibonacci(10))
"""
        
        analysis = desktop_server._analyze_code_security(safe_code, "python")
        
        assert analysis["risk_level"] == "low"
        assert len(analysis["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_security_notifications(self, desktop_server):
        """Test security alert notifications"""
        with patch('claude_jester_desktop.DesktopNotification.send') as mock_notify:
            desktop_server.config.notifications['security_alerts'] = True
            
            result = await desktop_server.execute_code_enhanced(
                "python",
                "import os; os.system('echo dangerous')"
            )
            
            # Should trigger security notification
            mock_notify.assert_called_once()
            args = mock_notify.call_args[0]
            assert "Security Alert" in args[0]

# ===== PERFORMANCE TESTS =====

class TestPerformanceMonitoring:
    """Test performance monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_performance_recording(self, desktop_server):
        """Test performance metrics recording"""
        if not desktop_server.config.performance_monitoring:
            pytest.skip("Performance monitoring disabled")
        
        result = await desktop_server.execute_code_enhanced(
            "python",
            "import time; time.sleep(0.1); print('Performance test')"
        )
        
        assert result.success
        assert result.execution_time >= 0.1
        assert result.performance_metrics is not None
    
    def test_complexity_calculation(self, desktop_server):
        """Test code complexity calculation"""
        if not hasattr(desktop_server, 'performance_monitor'):
            pytest.skip("Performance monitor not available")
        
        simple_code = "print('hello')"
        complex_code = """
for i in range(10):
    if i % 2 == 0:
        try:
            with open('file', 'r') as f:
                while True:
                    if f.readline():
                        break
        except Exception as e:
            pass
    else:
        continue
"""
        
        monitor = desktop_server.performance_monitor
        simple_complexity = monitor._calculate_complexity(simple_code)
        complex_complexity = monitor._calculate_complexity(complex_code)
        
        assert complex_complexity > simple_complexity
        assert simple_complexity >= 1

# ===== AUDIT AND COMPLIANCE TESTS =====

class TestAuditLogging:
    """Test audit logging and compliance"""
    
    @pytest.mark.asyncio
    async def test_audit_log_creation(self, desktop_server):
        """Test audit log entry creation"""
        if not desktop_server.config.enterprise_mode:
            desktop_server.config.enterprise_mode = True
        
        result = await desktop_server.execute_code_enhanced(
            "python",
            "print('Audit test')"
        )
        
        assert result.success
        
        # Check if audit file exists
        audit_file = desktop_server.config.data_dir / 'audit.log'
        if audit_file.exists():
            with open(audit_file) as f:
                audit_entries = [json.loads(line) for line in f if line.strip()]
            
            # Find our test entry
            test_entries = [e for e in audit_entries if 'Audit test' in str(e)]
            assert len(test_entries) > 0
            
            entry = test_entries[-1]
            assert 'timestamp' in entry
            assert 'session_id' in entry
            assert 'code_hash' in entry
            assert entry['language'] == 'python'
    
    def test_compliance_checking(self, desktop_server):
        """Test compliance flag detection"""
        audit_logger = desktop_server.audit_logger
        
        dangerous_code = "import subprocess; subprocess.call(['rm', '-rf', '/'])"
        flags = audit_logger._check_compliance(dangerous_code, "python")
        
        assert len(flags) > 0
        assert "SUBPROCESS_USAGE" in flags

# ===== INTEGRATION TESTS =====

class TestIntegration:
    """Integration tests for full workflow"""
    
    @pytest.mark.asyncio
    async def test_full_quantum_debugging_workflow(self, desktop_server):
        """Test complete quantum debugging workflow"""
        # Enable quantum debugging
        desktop_server.config.quantum_debugging = True
        
        result = await desktop_server.execute_code_enhanced(
            "slash",
            "/quantum find fastest sorting algorithm"
        )
        
        assert result.success
        assert "quantum" in result.output.lower()
    
    @pytest.mark.asyncio
    async def test_security_scan_tool(self, desktop_server):
        """Test security scan tool integration"""
        request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "security_scan",
                "arguments": {
                    "code": "import os; os.system('dangerous')",
                    "language": "python",
                    "scan_level": "comprehensive"
                }
            }
        }
        
        response = await desktop_server.handle_call_tool(request)
        
        assert "result" in response
        content = response["result"]["content"][0]["text"]
        assert "Security Analysis" in content
        assert "🔴" in content  # High risk indicator
    
    @pytest.mark.asyncio
    async def test_system_diagnostics_tool(self, desktop_server):
        """Test system diagnostics tool"""
        request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "system_diagnostics",
                "arguments": {
                    "component": "all",
                    "detailed": True
                }
            }
        }
        
        response = await desktop_server.handle_call_tool(request)
        
        assert "result" in response
        content = response["result"]["content"][0]["text"]
        assert "System Diagnostics" in content
        assert "Platform:" in content

# ===== PACKAGING TESTS =====

class TestPackaging:
    """Test extension packaging and validation"""
    
    def test_manifest_validation(self):
        """Test manifest.json validation"""
        from build import ExtensionBuilder
        
        # Create test manifest
        test_manifest = {
            "dxt_version": "0.1",
            "name": "test-extension",
            "version": "1.0.0",
            "description": "Test extension",
            "server": {
                "type": "python",
                "entry_point": "server/main.py",
                "mcp_config": {
                    "command": "python",
                    "args": ["${__dirname}/server/main.py"]
                }
            }
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            manifest_file = temp_path / "manifest.json"
            
            with open(manifest_file, 'w') as f:
                json.dump(test_manifest, f)
            
            builder = ExtensionBuilder(temp_path)
            
            # Should not raise exception
            validated_manifest = builder.validate_manifest()
            assert validated_manifest["name"] == "test-extension"
    
    def test_package_creation(self):
        """Test .dxt package creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal extension structure
            manifest = {
                "dxt_version": "0.1",
                "name": "test-extension",
                "version": "1.0.0",
                "description": "Test",
                "server": {
                    "type": "python",
                    "entry_point": "server/main.py"
                }
            }
            
            (temp_path / "manifest.json").write_text(json.dumps(manifest))
            
            server_dir = temp_path / "server"
            server_dir.mkdir()
            (server_dir / "main.py").write_text("# Test server")
            
            from build import ExtensionBuilder
            builder = ExtensionBuilder(temp_path)
            builder.clean()
            
            # Copy files to build directory
            (builder.build_dir / "manifest.json").write_text(json.dumps(manifest))
            build_server_dir = builder.build_dir / "server"
            build_server_dir.mkdir()
            (build_server_dir / "main.py").write_text("# Test server")
            
            # Create package
            dxt_path, package_info = builder.create_package(manifest)
            
            assert dxt_path.exists()
            assert dxt_path.suffix == ".dxt"
            assert package_info["version"] == "1.0.0"
            
            # Validate package contents
            with zipfile.ZipFile(dxt_path, 'r') as zf:
                files = zf.namelist()
                assert "manifest.json" in files
                assert "server/main.py" in files

# ===== PERFORMANCE BENCHMARKS =====

class TestPerformanceBenchmarks:
    """Performance benchmarks for the extension"""
    
    @pytest.mark.asyncio
    async def test_execution_performance(self, desktop_server):
        """Benchmark code execution performance"""
        start_time = time.time()
        
        # Execute multiple code snippets
        for i in range(10):
            result = await desktop_server.execute_code_enhanced(
                "python",
                f"result = {i} * 2\nprint(f'Result {i}: {{result}}')"
            )
            assert result.success
        
        total_time = time.time() - start_time
        avg_time_per_execution = total_time / 10
        
        # Should complete within reasonable time
        assert avg_time_per_execution < 2.0  # 2 seconds per execution max
        print(f"Average execution time: {avg_time_per_execution:.3f}s")
    
    @pytest.mark.asyncio
    async def test_security_analysis_performance(self, desktop_server):
        """Benchmark security analysis performance"""
        code_samples = [
            "print('hello world')",
            "import os; print(os.getcwd())",
            "import subprocess; result = subprocess.run(['echo', 'test'])",
            """
import os
import sys
import subprocess
import socket
import urllib.request

def dangerous_function():
    os.system("rm -rf /")
    subprocess.call(["dangerous", "command"])
    eval("malicious_code")
    exec("more_malicious_code")
""" * 10  # Large code sample
        ]
        
        start_time = time.time()
        
        for code in code_samples:
            analysis = desktop_server._analyze_code_security(code, "python")
            assert "risk_level" in analysis
        
        total_time = time.time() - start_time
        avg_time = total_time / len(code_samples)
        
        # Security analysis should be fast
        assert avg_time < 0.1  # 100ms per analysis max
        print(f"Average security analysis time: {avg_time:.3f}s")

# ===== TEST CONFIGURATION =====

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as performance benchmark"
    )

if __name__ == "__main__":
    # Run tests directly
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--asyncio-mode=auto"
    ])
