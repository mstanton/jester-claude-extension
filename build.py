#!/usr/bin/env python3
"""
Claude-Jester Desktop Extension Production Builder
Creates a production-ready .dxt package with all dependencies and optimizations
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
import tempfile
import hashlib
import platform
from pathlib import Path
from datetime import datetime
import argparse

class ExtensionBuilder:
    """Professional extension builder with validation and optimization"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.build_dir = project_root / "build"
        self.dist_dir = project_root / "dist"
        self.version = self._get_version()
        
    def _get_version(self) -> str:
        """Get version from manifest or git"""
        manifest_file = self.project_root / "manifest.json"
        if manifest_file.exists():
            with open(manifest_file) as f:
                manifest = json.load(f)
                return manifest.get("version", "1.0.0")
        return "1.0.0"
    
    def clean(self):
        """Clean previous builds"""
        print("🧹 Cleaning previous builds...")
        
        for directory in [self.build_dir, self.dist_dir]:
            if directory.exists():
                shutil.rmtree(directory)
        
        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)
        
        print("✅ Build directories cleaned")
    
    def install_dependencies(self):
        """Install and bundle Python dependencies"""
        print("📦 Installing and bundling dependencies...")
        
        lib_dir = self.build_dir / "lib"
        lib_dir.mkdir(exist_ok=True)
        
        # Core dependencies for the extension
        dependencies = [
            "aiofiles>=0.8.0",
            "psutil>=5.8.0",
            "cryptography>=39.0.0",
            "pyjwt>=2.8.0",
        ]
        
        # Platform-specific dependencies
        system = platform.system().lower()
        if system == "windows":
            dependencies.append("win10toast>=0.9")
        elif system == "linux":
            dependencies.append("plyer>=2.0")
        
        # Install each dependency
        for dep in dependencies:
            print(f"  Installing {dep}...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install",
                    "--target", str(lib_dir),
                    "--no-deps", "--no-compile",
                    dep
                ], check=True, capture_output=True, text=True)
                
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Warning: Failed to install {dep}: {e}")
                # Continue with other dependencies
        
        # Clean up unnecessary files
        self._cleanup_dependencies(lib_dir)
        
        dep_size = sum(f.stat().st_size for f in lib_dir.rglob('*') if f.is_file())
        print(f"✅ Dependencies bundled ({dep_size // 1024 // 1024} MB)")
    
    def _cleanup_dependencies(self, lib_dir: Path):
        """Remove unnecessary files from dependencies"""
        patterns_to_remove = [
            "*.pyc", "*.pyo", "__pycache__",
            "*.dist-info", "*.egg-info",
            "tests", "test", "testing",
            "docs", "doc", "examples",
            "*.md", "*.rst", "*.txt",
            ".git*", ".tox", ".pytest_cache"
        ]
        
        for pattern in patterns_to_remove:
            for path in lib_dir.rglob(pattern):
                if path.is_file():
                    path.unlink()
                elif path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
    
    def copy_server_files(self):
        """Copy and optimize server files"""
        print("📋 Copying server files...")
        
        server_dir = self.build_dir / "server"
        server_dir.mkdir(exist_ok=True)
        
        # Essential server files
        server_files = [
            "claude_jester_desktop.py",
            "standalone_mcp_server.py"  # From original project
        ]
        
        for filename in server_files:
            src_file = self.project_root / "server" / filename
            if src_file.exists():
                dst_file = server_dir / filename
                shutil.copy2(src_file, dst_file)
                
                # Optimize Python files
                self._optimize_python_file(dst_file)
                print(f"  ✅ {filename}")
            else:
                print(f"  ⚠️  Missing: {filename}")
        
        # Create __init__.py
        (server_dir / "__init__.py").write_text(
            '"""Claude-Jester Desktop Extension Server"""\n'
            f'__version__ = "{self.version}"\n'
        )
        
        # Copy utility modules if they exist
        utils_src = self.project_root / "server" / "utils"
        if utils_src.exists():
            utils_dst = server_dir / "utils"
            shutil.copytree(utils_src, utils_dst)
            print("  ✅ Utils modules")
    
    def _optimize_python_file(self, file_path: Path):
        """Basic Python file optimization"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Remove debug prints and excessive comments
        lines = content.split('\n')
        optimized_lines = []
        
        for line in lines:
            stripped = line.strip()
            # Keep the line unless it's a debug print
            if not (stripped.startswith('print(') and 'debug' in stripped.lower()):
                optimized_lines.append(line)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(optimized_lines))
    
    def create_assets(self):
        """Create or copy assets"""
        print("🎨 Creating assets...")
        
        assets_dir = self.build_dir / "assets"
        assets_dir.mkdir(exist_ok=True)
        
        # Copy existing assets if available
        src_assets = self.project_root / "assets"
        if src_assets.exists():
            for asset_file in src_assets.iterdir():
                if asset_file.is_file():
                    shutil.copy2(asset_file, assets_dir)
            print("  ✅ Copied existing assets")
        else:
            # Create placeholder assets
            self._create_placeholder_assets(assets_dir)
            print("  ✅ Created placeholder assets")
    
    def _create_placeholder_assets(self, assets_dir: Path):
        """Create placeholder assets for testing"""
        # Create a simple SVG icon
        icon_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="32" fill="#4A90E2"/>
  <text x="128" y="140" text-anchor="middle" fill="white" font-family="Arial" font-size="120" font-weight="bold">🃏</text>
  <text x="128" y="200" text-anchor="middle" fill="white" font-family="Arial" font-size="20">Quantum</text>
</svg>"""
        
        (assets_dir / "claude-jester-icon.svg").write_text(icon_svg)
        
        # Create preview image placeholders
        for preview in ["quantum-debugging-preview", "container-execution-preview", "security-analysis-preview"]:
            (assets_dir / f"{preview}.txt").write_text(f"Preview image placeholder for {preview}")
    
    def validate_manifest(self):
        """Validate and update manifest"""
        print("📋 Validating manifest...")
        
        manifest_src = self.project_root / "manifest.json"
        manifest_dst = self.build_dir / "manifest.json"
        
        if not manifest_src.exists():
            raise FileNotFoundError("manifest.json not found in project root")
        
        with open(manifest_src) as f:
            manifest = json.load(f)
        
        # Validation checks
        required_fields = ["dxt_version", "name", "version", "description", "server"]
        for field in required_fields:
            if field not in manifest:
                raise ValueError(f"Required field '{field}' missing from manifest")
        
        # Update paths to be relative to extension root
        if "server" in manifest and "entry_point" in manifest["server"]:
            manifest["server"]["entry_point"] = "server/claude_jester_desktop.py"
        
        # Update version with build timestamp
        build_time = datetime.now().strftime("%Y%m%d.%H%M")
        if "+" not in manifest["version"]:
            manifest["version"] = f"{manifest['version']}+{build_time}"
        
        # Validate server config
        if "mcp_config" in manifest["server"]:
            mcp_config = manifest["server"]["mcp_config"]
            mcp_config["args"] = ["${__dirname}/server/claude_jester_desktop.py"]
            if "env" not in mcp_config:
                mcp_config["env"] = {}
            mcp_config["env"]["PYTHONPATH"] = "${__dirname}/server:${__dirname}/lib"
        
        with open(manifest_dst, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        print(f"  ✅ Manifest validated: {manifest['name']} v{manifest['version']}")
        return manifest
    
    def copy_documentation(self):
        """Copy documentation files"""
        print("📚 Copying documentation...")
        
        docs_to_copy = [
            ("README.md", "README.md"),
            ("CHANGELOG.md", "CHANGELOG.md"), 
            ("LICENSE", "LICENSE"),
            ("docs/SECURITY.md", "SECURITY.md"),
            ("docs/TROUBLESHOOTING.md", "TROUBLESHOOTING.md")
        ]
        
        for src_path, dst_name in docs_to_copy:
            src_file = self.project_root / src_path
            if src_file.exists():
                dst_file = self.build_dir / dst_name
                shutil.copy2(src_file, dst_file)
                print(f"  ✅ {dst_name}")
    
    def create_package(self, manifest: dict):
        """Create the final .dxt package"""
        print("📦 Creating .dxt package...")
        
        package_name = manifest["name"]
        version = manifest["version"].split('+')[0]  # Remove build timestamp
        dxt_filename = f"{package_name}-{version}.dxt"
        dxt_path = self.dist_dir / dxt_filename
        
        # Create the ZIP archive
        with zipfile.ZipFile(dxt_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file_path in self.build_dir.rglob('*'):
                if file_path.is_file():
                    arc_path = file_path.relative_to(self.build_dir)
                    zf.write(file_path, arc_path)
                    
            # Add build metadata
            build_info = {
                "build_time": datetime.now().isoformat(),
                "builder_platform": platform.platform(),
                "python_version": platform.python_version(),
                "package_version": version
            }
            
            zf.writestr("build_info.json", json.dumps(build_info, indent=2))
        
        # Calculate package hash
        package_hash = self._calculate_file_hash(dxt_path)
        
        # Get package size
        size_mb = dxt_path.stat().st_size / (1024 * 1024)
        
        print(f"✅ Package created: {dxt_path.name}")
        print(f"📦 Size: {size_mb:.1f} MB")
        print(f"🔒 SHA256: {package_hash[:16]}...")
        
        # Create package info file
        package_info = {
            "filename": dxt_filename,
            "size_bytes": dxt_path.stat().st_size,
            "size_mb": round(size_mb, 1),
            "sha256": package_hash,
            "version": version,
            "build_time": datetime.now().isoformat(),
            "platform": platform.platform()
        }
        
        info_file = self.dist_dir / f"{package_name}-{version}.json"
        with open(info_file, 'w') as f:
            json.dump(package_info, f, indent=2)
        
        return dxt_path, package_info
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def validate_package(self, dxt_path: Path):
        """Validate the created package"""
        print("🔍 Validating package...")
        
        errors = []
        warnings = []
        
        with zipfile.ZipFile(dxt_path, 'r') as zf:
            files = zf.namelist()
            
            # Check required files
            required_files = [
                "manifest.json",
                "server/claude_jester_desktop.py"
            ]
            
            for required in required_files:
                if required not in files:
                    errors.append(f"Missing required file: {required}")
            
            # Validate manifest
            try:
                manifest_content = zf.read("manifest.json")
                manifest = json.loads(manifest_content)
                
                # Check manifest structure
                if not manifest.get("dxt_version"):
                    errors.append("Missing dxt_version in manifest")
                
                if not manifest.get("server", {}).get("entry_point"):
                    errors.append("Missing server.entry_point in manifest")
                    
            except json.JSONDecodeError as e:
                errors.append(f"Invalid manifest JSON: {e}")
            except Exception as e:
                errors.append(f"Manifest validation error: {e}")
            
            # Check file sizes
            total_size = sum(zinfo.file_size for zinfo in zf.infolist())
            if total_size > 100 * 1024 * 1024:  # 100MB limit
                warnings.append(f"Package is large: {total_size // 1024 // 1024}MB")
            
            # Check for common issues
            py_files = [f for f in files if f.endswith('.py')]
            if not py_files:
                warnings.append("No Python files found")
            
            # Check for unnecessary files
            unnecessary_patterns = ['.pyc', '__pycache__', '.git', '.DS_Store']
            unnecessary_files = []
            for pattern in unnecessary_patterns:
                unnecessary_files.extend([f for f in files if pattern in f])
            
            if unnecessary_files:
                warnings.append(f"Unnecessary files found: {len(unnecessary_files)} files")
        
        # Report validation results
        if errors:
            print("❌ Validation failed:")
            for error in errors:
                print(f"  💥 {error}")
            return False
        
        if warnings:
            print("⚠️  Validation warnings:")
            for warning in warnings:
                print(f"  ⚠️  {warning}")
        
        print("✅ Package validation successful")
        return True
    
    def generate_installation_script(self, package_info: dict):
        """Generate installation scripts for different platforms"""
        print("📝 Generating installation helpers...")
        
        scripts_dir = self.dist_dir / "installation"
        scripts_dir.mkdir(exist_ok=True)
        
        package_name = package_info["filename"]
        
        # PowerShell script for Windows
        powershell_script = f'''# Claude-Jester Desktop Extension Installer
# Run this script to install the extension automatically

Write-Host "🃏 Claude-Jester Desktop Extension Installer" -ForegroundColor Cyan
Write-Host "Package: {package_name}" -ForegroundColor Green

$claudeConfigPath = "$env:APPDATA\\Claude\\claude_desktop_config.json"
$extensionPath = ".\{package_name}"

if (-not (Test-Path $extensionPath)) {{
    Write-Host "❌ Extension package not found: $extensionPath" -ForegroundColor Red
    exit 1
}}

Write-Host "📁 Found Claude Desktop config: $claudeConfigPath" -ForegroundColor Green
Write-Host "📦 Installing extension..." -ForegroundColor Yellow

# Launch Claude Desktop with extension
Start-Process "claude://install-extension?path=$((Resolve-Path $extensionPath).Path)"

Write-Host "✅ Installation initiated. Check Claude Desktop for completion." -ForegroundColor Green
Write-Host "🔧 Configure the extension in Settings > Extensions" -ForegroundColor Yellow
'''
        
        (scripts_dir / "install-windows.ps1").write_text(powershell_script)
        
        # Bash script for macOS/Linux
        bash_script = f'''#!/bin/bash
# Claude-Jester Desktop Extension Installer

echo "🃏 Claude-Jester Desktop Extension Installer"
echo "Package: {package_name}"

CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    CLAUDE_CONFIG="$HOME/.config/claude/claude_desktop_config.json"
fi

EXTENSION_PATH="./{package_name}"

if [ ! -f "$EXTENSION_PATH" ]; then
    echo "❌ Extension package not found: $EXTENSION_PATH"
    exit 1
fi

echo "📁 Claude Desktop config: $CLAUDE_CONFIG"
echo "📦 Installing extension..."

# Launch Claude Desktop with extension
if [[ "$OSTYPE" == "darwin"* ]]; then
    open "claude://install-extension?path=$(realpath "$EXTENSION_PATH")"
else
    xdg-open "claude://install-extension?path=$(realpath "$EXTENSION_PATH")"
fi

echo "✅ Installation initiated. Check Claude Desktop for completion."
echo "🔧 Configure the extension in Settings > Extensions"
'''
        
        (scripts_dir / "install-unix.sh").write_text(bash_script)
        os.chmod(scripts_dir / "install-unix.sh", 0o755)
        
        # Create README for installation
        install_readme = f'''# Claude-Jester Desktop Extension Installation

## Automatic Installation

### Windows
1. Download `{package_name}` and `installation/install-windows.ps1`
2. Place both files in the same directory
3. Right-click `install-windows.ps1` and select "Run with PowerShell"
4. Follow the prompts in Claude Desktop

### macOS/Linux
1. Download `{package_name}` and `installation/install-unix.sh`
2. Place both files in the same directory
3. Run: `./installation/install-unix.sh`
4. Follow the prompts in Claude Desktop

## Manual Installation

1. Open Claude Desktop
2. Go to Settings > Extensions
3. Drag and drop `{package_name}` into the Extensions panel
4. Configure extension preferences
5. Start using quantum debugging features!

## Package Information

- **Version**: {package_info["version"]}
- **Size**: {package_info["size_mb"]} MB
- **SHA256**: `{package_info["sha256"]}`
- **Build**: {package_info["build_time"]}

## Support

- Documentation: https://claude-jester.dev
- Issues: https://github.com/mstanton/claude-jester/issues
- Security: security@claude-jester.dev
'''
        
        (scripts_dir / "README.md").write_text(install_readme)
        
        print(f"  ✅ Installation scripts created in {scripts_dir}")

def main():
    """Main build process"""
    parser = argparse.ArgumentParser(description="Build Claude-Jester Desktop Extension")
    parser.add_argument("--clean", action="store_true", help="Clean build directories only")
    parser.add_argument("--validate-only", action="store_true", help="Only validate existing package")
    parser.add_argument("--project-root", type=Path, default=Path.cwd(), help="Project root directory")
    
    args = parser.parse_args()
    
    builder = ExtensionBuilder(args.project_root)
    
    try:
        if args.clean:
            builder.clean()
            print("✅ Clean completed")
            return
        
        if args.validate_only:
            # Find existing package
            for dxt_file in builder.dist_dir.glob("*.dxt"):
                print(f"🔍 Validating {dxt_file.name}...")
                if builder.validate_package(dxt_file):
                    print("✅ Validation successful")
                else:
                    print("❌ Validation failed")
                    sys.exit(1)
            return
        
        # Full build process
        print("🃏 Claude-Jester Desktop Extension Builder")
        print("=" * 50)
        
        builder.clean()
        builder.install_dependencies()
        builder.copy_server_files()
        builder.create_assets()
        manifest = builder.validate_manifest()
        builder.copy_documentation()
        
        dxt_path, package_info = builder.create_package(manifest)
        
        if builder.validate_package(dxt_path):
            builder.generate_installation_script(package_info)
            
            print("\n🎉 Build completed successfully!")
            print(f"📦 Package: {dxt_path}")
            print(f"📏 Size: {package_info['size_mb']} MB")
            print(f"🔒 SHA256: {package_info['sha256'][:16]}...")
            print("\n🚀 Next steps:")
            print("1. Test the extension in Claude Desktop")
            print("2. Use installation scripts for easy deployment")
            print("3. Submit to Anthropic extension directory")
            
        else:
            print("❌ Build completed but validation failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Build failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
