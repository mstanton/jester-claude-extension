# 🔌 API Documentation

## MCP Tools

### execute_code

Execute code with quantum debugging and security analysis.

**Parameters**:
- `language` (required): Programming language ("python", "javascript", "bash", "slash")
- `code` (required): Code to execute or slash command
- `security_level` (optional): Override default security level
- `enable_quantum` (optional): Enable quantum debugging features

**Example**:
```json
{
  "name": "execute_code",
  "arguments": {
    "language": "python",
    "code": "print('Hello World')",
    "security_level": "balanced"
  }
}
```

### quantum_debug

Advanced quantum debugging with parallel algorithm testing.

**Parameters**:
- `task_description` (required): Description of optimization task
- `test_data_size` (optional): Size of test data
- `iterations` (optional): Number of iterations

### security_scan

Comprehensive security analysis of code.

**Parameters**:
- `code` (required): Code to analyze
- `language` (required): Programming language
- `scan_level` (optional): Depth of analysis ("basic", "comprehensive", "enterprise")

### system_diagnostics

System health check and diagnostics.

**Parameters**:
- `component` (required): Component to diagnose ("all", "podman", "performance", "security", "storage")
- `detailed` (optional): Include detailed information

## Slash Commands

- `/quantum [task]`: Quantum debugging optimization
- `/help`: Show available commands
- `/benchmark [language] [code] [iterations]`: Performance benchmarking
- `/secure [code]`: Security analysis
- `/container [action]`: Container management

## Configuration

Extension settings are managed through Claude Desktop's extension settings panel. All settings are automatically validated and encrypted when stored.

For detailed API documentation, see the extension source code and manifest.json file.
