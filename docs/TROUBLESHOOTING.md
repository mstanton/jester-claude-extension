# 🔧 Troubleshooting Guide

## 🚨 Quick Fixes

### Extension Won't Install
**Problem**: .dxt file won't install in Claude Desktop

**Solutions**:
1. **Check Claude Desktop Version**: Ensure you have the latest version
2. **Verify File Integrity**: Check that the .dxt file downloaded completely
3. **Clear Extension Cache**: Restart Claude Desktop and try again

### Code Execution Fails
**Problem**: "Error executing code" messages

**Quick Diagnostics**:
```bash
# Test Python availability
python3 --version

# Test container system (if using Podman)
podman --version
podman run --rm alpine echo "Container test"
```

## 🐛 Common Issues

### Extension Loading Problems

#### ❌ "Extension failed to load"
**Symptoms**: Extension appears in list but shows "Failed" status

**Solutions**:
- **Missing Python**: Install Python 3.8+ with pip
- **Permission Issues**: Check file permissions on extension directory
- **Corrupted Extension**: Re-download and reinstall .dxt file

### Performance Issues

#### ⚠️ Slow execution times
**Symptoms**: Code takes >30 seconds to execute

**Solutions**:
- **Increase Timeout**: Extension Settings → Max Execution Time
- **Reduce Memory Limit**: Extension Settings → Max Memory
- **Close Other Applications**: Free up system resources

### Security and Permissions

#### ❌ "Permission denied" errors
**Symptoms**: Cannot write to workspace directory

**Solutions**:
1. **Check Directory Permissions**: Ensure write access to workspace
2. **Change Workspace Location**: Choose accessible location in settings
3. **Run as Administrator**: Temporarily for troubleshooting (Windows)

## 🆘 Getting Help

### Before Contacting Support
Please gather this information:

1. **System Information**: OS version, Python version
2. **Extension Information**: Version, configuration settings
3. **Error Details**: Exact error messages, steps to reproduce
4. **Log Files**: Recent entries from extension logs

### Support Channels
- **GitHub Issues**: Bug reports and feature requests
- **Security Issues**: security@claude-jester.dev
- **General Support**: Create a GitHub discussion

*For the complete troubleshooting guide, see the main TROUBLESHOOTING.md file.*
