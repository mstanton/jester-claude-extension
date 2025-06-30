# 🃏 Claude-Jester Desktop Extension - Complete Package

## 📁 Extension Directory Structure

```
claude-jester-desktop-extension/
├── manifest.json                    # Extension manifest (required)
├── server/                          # Main server files
│   ├── claude_jester_desktop.py     # Enhanced desktop server
│   ├── standalone_mcp_server.py     # Core MCP server (from existing)
│   ├── __init__.py                  # Python package init
│   └── utils/                       # Utility modules
│       ├── __init__.py
│       ├── notifications.py         # Desktop notification helpers
│       ├── security.py              # Security analysis tools
│       └── performance.py           # Performance monitoring
├── lib/                             # Bundled Python dependencies
│   ├── aiofiles/                    # Async file operations
│   ├── cryptography/                # Encryption/security
│   ├── psutil/                      # System monitoring
│   └── ...                          # Other dependencies
├── assets/                          # Extension assets
│   ├── claude-jester-icon.png       # Extension icon (256x256)
│   ├── quantum-debugging-preview.png # Preview image
│   ├── container-execution-preview.png
│   └── security-analysis-preview.png
├── docs/                            # Documentation
│   ├── README.md                    # Extension documentation
│   ├── SECURITY.md                  # Security guidelines
│   ├── TROUBLESHOOTING.md           # Common issues
│   └── API.md                       # API documentation
├── scripts/                         # Build and utility scripts
│   ├── build.py                     # Build .dxt package
│   ├── install_deps.py              # Install dependencies
│   └── validate.py                  # Validate extension
├── tests/                           # Test suite
│   ├── test_server.py               # Server tests
│   ├── test_security.py             # Security tests
│   └── test_performance.py          # Performance tests
├── requirements.txt                 # Python dependencies
├── CHANGELOG.md                     # Version history
├── LICENSE                          # MIT License
└── README.md                        # Project README
```

## 🔨 Build Script

Create `scripts/build.py`:

```python
#!/usr/bin/env python3
"""
Claude-Jester Desktop Extension Builder
Creates a .dxt package ready for distribution
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
import tempfile
from pathlib import Path

def install_dependencies(target_dir: Path):
    """Install Python dependencies to target directory"""
    print("📦 Installing Python dependencies...")
    
    requirements = [
        "aiofiles>=0.8.0",
        "psutil>=5.8.0", 
        "cryptography>=3.4.0",
        "pyjwt>=2.4.0"
    ]
    
    for requirement in requirements:
        subprocess.run([
            sys.executable, "-m", "pip", "install",
            "--target", str(target_dir),
            "--no-deps", requirement
        ], check=True)
    
    print(f"✅ Dependencies installed to {target_dir}")

def create_dxt_package():
    """Create the .dxt package"""
    print("🃏 Building Claude-Jester Desktop Extension...")
    
    # Project root
    project_root = Path(__file__).parent.parent
    build_dir = project_root / "build"
    
    # Clean build directory
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    # Copy server files
    server_dir = build_dir / "server"
    server_dir.mkdir()
    
    # Copy main server files
    shutil.copy2(project_root / "server" / "claude_jester_desktop.py", server_dir)
    shutil.copy2(project_root / "server" / "standalone_mcp_server.py", server_dir)
    
    # Create __init__.py files
    (server_dir / "__init__.py").touch()
    
    # Install dependencies
    lib_dir = build_dir / "lib"
    lib_dir.mkdir()
    install_dependencies(lib_dir)
    
    # Copy assets
    assets_dir = build_dir / "assets"
    if (project_root / "assets").exists():
        shutil.copytree(project_root / "assets", assets_dir)
    else:
        assets_dir.mkdir()
        # Create placeholder icon
        create_placeholder_icon(assets_dir / "claude-jester-icon.png")
    
    # Copy manifest
    shutil.copy2(project_root / "manifest.json", build_dir)
    
    # Copy documentation
    docs_to_copy = ["README.md", "CHANGELOG.md", "LICENSE"]
    for doc in docs_to_copy:
        if (project_root / doc).exists():
            shutil.copy2(project_root / doc, build_dir)
    
    # Create the .dxt package
    dxt_file = project_root / "claude-jester-quantum-debugger.dxt"
    
    with zipfile.ZipFile(dxt_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in build_dir.rglob('*'):
            if file_path.is_file():
                arc_path = file_path.relative_to(build_dir)
                zf.write(file_path, arc_path)
    
    # Get package size
    size_mb = dxt_file.stat().st_size / (1024 * 1024)
    
    print(f"✅ Package created: {dxt_file}")
    print(f"📦 Package size: {size_mb:.1f} MB")
    
    # Cleanup
    shutil.rmtree(build_dir)
    
    return dxt_file

def create_placeholder_icon(icon_path: Path):
    """Create a simple placeholder icon"""
    # This would normally create a proper PNG icon
    # For now, just create a text file
    icon_path.write_text("Claude-Jester Icon Placeholder")

def validate_package(dxt_file: Path):
    """Validate the created package"""
    print("🔍 Validating package...")
    
    with zipfile.ZipFile(dxt_file, 'r') as zf:
        files = zf.namelist()
        
        # Check required files
        required_files = [
            "manifest.json",
            "server/claude_jester_desktop.py"
        ]
        
        for required in required_files:
            if required not in files:
                print(f"❌ Missing required file: {required}")
                return False
        
        # Validate manifest
        manifest_content = zf.read("manifest.json")
        try:
            manifest = json.loads(manifest_content)
            print(f"✅ Manifest valid: {manifest['name']} v{manifest['version']}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid manifest JSON: {e}")
            return False
    
    print("✅ Package validation successful")
    return True

if __name__ == "__main__":
    try:
        dxt_file = create_dxt_package()
        
        if validate_package(dxt_file):
            print(f"🎉 Claude-Jester Desktop Extension built successfully!")
            print(f"📁 Location: {dxt_file}")
            print("\n🚀 Installation Instructions:")
            print("1. Open Claude Desktop")
            print("2. Go to Settings > Extensions")  
            print("3. Drag and drop the .dxt file into the Extensions panel")
            print("4. Configure the extension settings as needed")
            print("5. Start using quantum debugging features!")
        else:
            print("❌ Package validation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

## 📋 Requirements File

Create `requirements.txt`:

```
# Core async and system dependencies
aiofiles>=0.8.0
psutil>=5.8.0

# Security and encryption
cryptography>=3.4.0
pyjwt>=2.4.0

# Optional desktop integration (platform-specific)
win10toast>=0.9; platform_system=="Windows"
plyer>=2.0; platform_system=="Linux"

# Development dependencies (not bundled)
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

## 🎨 Assets Creation

### Extension Icon (assets/claude-jester-icon.png)
Create a 256x256 PNG icon representing:
- A stylized joker card (♠️🃏) 
- Quantum/code elements (⚛️💻)
- Modern flat design aesthetic
- Claude brand colors if possible

### Preview Images
Create preview screenshots showing:
1. **quantum-debugging-preview.png**: Quantum debugging in action
2. **container-execution-preview.png**: Podman container execution
3. **security-analysis-preview.png**: Security analysis interface

## 📝 Documentation Files

### README.md
```markdown
# Claude-Jester: Quantum Code Debugger Desktop Extension

Revolutionary AI code execution platform with quantum debugging, Podman containerization, and enterprise-grade security.

## Features

- **Quantum Debugging**: Parallel algorithm testing and optimization
- **Container Security**: Podman-based execution isolation  
- **Performance Monitoring**: Real-time execution analytics
- **Enterprise Security**: Audit logging and compliance
- **Multi-Language Support**: Python, JavaScript, Bash, Rust, Go

## Quick Start

1. Install the extension via Claude Desktop
2. Configure security preferences
3. Start coding with `/quantum optimize sorting algorithm`

## Security Levels

- **Maximum**: Isolated containers, no network
- **Balanced**: Session containers, moderate security  
- **Development**: Relaxed security, network access

## Requirements

- **Optional**: Podman ≥3.0 for enhanced security
- **Optional**: Node.js ≥14.0 for JavaScript execution
- **System**: 256MB RAM, 100MB disk space

## Configuration

All settings are configured through Claude Desktop's extension settings panel:

- Security level and allowed languages
- Performance monitoring preferences  
- Desktop notification settings
- Workspace directory location
- Enterprise compliance features

## Support

- Documentation: https://claude-jester.dev/docs
- Issues: https://github.com/mstanton/claude-jester/issues
- Security: security@claude-jester.dev
```

### SECURITY.md
```markdown
# Security Guidelines

## Security Architecture

Claude-Jester uses multiple security layers:

1. **Input Validation**: Dangerous pattern detection
2. **Container Isolation**: Podman rootless containers
3. **Resource Limits**: Memory, CPU, and time constraints
4. **Audit Logging**: Complete execution tracking
5. **Encrypted Storage**: Sensitive data protection

## Security Levels

### Maximum Security
- Ephemeral containers (destroyed after use)
- No network access
- Read-only filesystem
- User namespace isolation
- Complete audit trail

### Balanced Security  
- Session containers (reused)
- No network access
- Limited filesystem access
- Resource monitoring
- Performance optimization

### Development Mode
- Relaxed container settings
- Limited network access
- Larger resource limits
- Enhanced debugging features

## Enterprise Features

- SOC2 and ISO27001 compliance logging
- Group policy support
- Custom security profiles
- Advanced audit reporting
- Integration with enterprise security tools

## Reporting Security Issues

Email security concerns to: security@claude-jester.dev
```

## 🧪 Testing Suite

Create `tests/test_server.py`:

```python
#!/usr/bin/env python3
"""
Test suite for Claude-Jester Desktop Extension
"""

import pytest
import asyncio
import json
from pathlib import Path
import tempfile
import sys

# Add server to path
sys.path.insert(0, str(Path(__file__).parent.parent / "server"))

from claude_jester_desktop import DesktopMCPServer, DesktopConfig

@pytest.fixture
async def server():
    """Create test server instance"""
    server = DesktopMCPServer()
    return server

@pytest.mark.asyncio
async def test_python_execution(server):
    """Test basic Python execution"""
    result = await server.execute_code_enhanced("python", "print('Hello World')")
    
    assert result.success
    assert "Hello World" in result.output
    assert result.execution_time > 0
    assert result.security_level in ["subprocess", "balanced", "maximum"]

@pytest.mark.asyncio  
async def test_security_analysis(server):
    """Test security analysis functionality"""
    dangerous_code = "import os; os.system('rm -rf /')"
    result = await server.execute_code_enhanced("python", dangerous_code)
    
    assert result.security_analysis is not None
    assert result.security_analysis['risk_level'] == 'high'
    assert len(result.security_analysis['issues']) > 0

@pytest.mark.asyncio
async def test_slash_commands(server):
    """Test slash command functionality"""
    result = await server.execute_code_enhanced("slash", "/help")
    
    assert result.success
    assert "Claude-Jester" in result.output

def test_mcp_initialize(server):
    """Test MCP initialize protocol"""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }
    
    response = server.handle_initialize(request)
    
    assert response["jsonrpc"] == "2.0"
    assert response["id"] == 1
    assert "result" in response
    assert response["result"]["serverInfo"]["name"] == "claude-jester-desktop"

def test_mcp_list_tools(server):
    """Test MCP tools list"""
    request = {
        "jsonrpc": "2.0", 
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    response = server.handle_list_tools(request)
    
    assert response["jsonrpc"] == "2.0"
    assert "result" in response
    assert "tools" in response["result"]
    
    tools = response["result"]["tools"]
    tool_names = [tool["name"] for tool in tools]
    
    assert "execute_code" in tool_names
    assert "quantum_debug" in tool_names
    assert "security_scan" in tool_names

if __name__ == "__main__":
    pytest.main([__file__])
```

## 🚀 Installation & Distribution

### Build the Extension

```bash
# 1. Clone or create the extension directory
mkdir claude-jester-desktop-extension
cd claude-jester-desktop-extension

# 2. Set up the structure (copy files from artifacts above)
# - manifest.json
# - server/claude_jester_desktop.py  
# - server/standalone_mcp_server.py (from your existing code)
# - scripts/build.py
# - requirements.txt

# 3. Install build dependencies
pip install build setuptools wheel

# 4. Run the build script
python scripts/build.py
```

### Manual Installation

```bash
# 1. Install the Anthropic DXT CLI
npm install -g @anthropic-ai/dxt

# 2. Initialize the extension
dxt init

# 3. Build the package
dxt pack

# 4. Install in Claude Desktop
# Drag the .dxt file into Claude Desktop Settings > Extensions
```

### Distribution Options

1. **Direct Distribution**: Share the .dxt file directly
2. **GitHub Releases**: Attach to GitHub releases
3. **Official Directory**: Submit to Anthropic's extension directory
4. **Enterprise Distribution**: Deploy via group policy or MDM

## 🔧 Development Workflow

### Local Development

1. **Setup Development Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   pip install -r requirements.txt
   ```

2. **Test the Server Directly**:
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' | python server/claude_jester_desktop.py
   ```

3. **Run Tests**:
   ```bash
   pytest tests/
   ```

4. **Build and Test Package**:
   ```bash
   python scripts/build.py
   # Test the created .dxt file in Claude Desktop
   ```

### Continuous Integration

Create `.github/workflows/build.yml`:

```yaml
name: Build Claude-Jester Extension

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
  release:
    types: [ published ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-asyncio
    - name: Run tests
      run: pytest tests/

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Build extension
      run: python scripts/build.py
    - name: Upload artifact
      uses: actions/upload-artifact@v3
      with:
        name: claude-jester-extension
        path: "*.dxt"
    - name: Release
      if: github.event_name == 'release'
      uses: softprops/action-gh-release@v1
      with:
        files: "*.dxt"
```

## 🎯 Advanced Features

### Enterprise Deployment

For enterprise environments, create additional configuration:

1. **Group Policy Templates**: Windows .admx files
2. **MDM Profiles**: macOS configuration profiles  
3. **Registry Settings**: Windows registry configuration
4. **Custom Registries**: Internal extension distribution

### Performance Optimization

- **Lazy Loading**: Load components on demand
- **Caching**: Cache execution results and analysis
- **Background Processing**: Async operations
- **Memory Management**: Cleanup temporary files

### Security Enhancements

- **Code Signing**: Sign the .dxt package
- **Integrity Checks**: Verify package integrity
- **Sandboxing**: Additional isolation layers
- **Compliance**: SOC2, ISO27001, FedRAMP support

This complete package transforms your Claude-Jester MCP server into a production-ready desktop extension with enterprise features, enhanced security, and seamless user experience! 🚀
