# 🔧 Development Guide

## Quick Start

```bash
# One-command setup and build
python3 setup_and_build.py

# Or step by step:
python3 validate_extension.py    # Validate structure
python3 scripts/build.py         # Build .dxt package
```

## Development Workflow

1. **Make Changes**: Edit files in server/, add features, fix bugs
2. **Validate**: `python3 validate_extension.py`
3. **Test**: `python3 -m pytest tests/` (requires pytest)
4. **Build**: `python3 scripts/build.py`
5. **Install**: Drag .dxt file into Claude Desktop

## Key Files

- `manifest.json` - Extension configuration
- `server/claude_jester_desktop.py` - Main server implementation
- `server/utils/` - Utility modules (notifications, security)
- `scripts/build.py` - Build script for .dxt packaging
- `requirements.txt` - Python dependencies

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
python3 -m pytest tests/ -v

# Run specific test
python3 tests/test_basic.py
```

## Building

The build process:
1. Validates all files
2. Installs dependencies to lib/
3. Creates .dxt package with all components
4. Generates installation scripts
5. Validates final package

## Deployment

The extension is ready for:
- ✅ Local installation (drag & drop)
- ✅ GitHub releases (automated)
- ✅ Enterprise deployment (MDM/Group Policy)
- ✅ Anthropic extension directory (future)

## Security

All code execution happens in:
- 🛡️ Podman containers (if available)
- 🔒 Subprocess isolation (fallback)
- 📝 Complete audit logging
- 🔐 Encrypted configuration storage

Ready to revolutionize AI-assisted programming! 🃏✨
