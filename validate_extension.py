#!/usr/bin/env python3
"""
Extension validation script - no external dependencies required
"""

import json
import ast
import os
from pathlib import Path

def validate_extension():
    """Validate the extension structure and files"""
    print("🃏 Claude-Jester Desktop Extension Validator")
    print("=" * 50)
    
    base_dir = Path(__file__).parent
    errors = []
    warnings = []
    
    # Check required directories
    required_dirs = [
        "server", "server/utils", "scripts", "tests", "assets", "docs"
    ]
    
    print("\n📁 Checking directory structure...")
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.exists() and dir_path.is_dir():
            print(f"  ✅ {dir_name}")
        else:
            errors.append(f"Missing directory: {dir_name}")
            print(f"  ❌ {dir_name}")
    
    # Check required files
    required_files = [
        "manifest.json",
        "server/claude_jester_desktop.py",
        "server/standalone_mcp_server.py",
        "server/__init__.py",
        "server/utils/__init__.py",
        "server/utils/notifications.py",
        "server/utils/security.py",
        "scripts/build.py",
        "requirements.txt",
        "README.md",
        "SECURITY.md",
        "CHANGELOG.md",
        "LICENSE"
    ]
    
    print("\n📄 Checking required files...")
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.exists() and file_path.is_file():
            print(f"  ✅ {file_name}")
        else:
            errors.append(f"Missing file: {file_name}")
            print(f"  ❌ {file_name}")
    
    # Validate manifest.json
    print("\n📋 Validating manifest.json...")
    manifest_file = base_dir / "manifest.json"
    if manifest_file.exists():
        try:
            with open(manifest_file) as f:
                manifest = json.load(f)
            
            required_fields = ["dxt_version", "name", "version", "description", "server"]
            for field in required_fields:
                if field in manifest:
                    print(f"  ✅ {field}: {manifest[field] if len(str(manifest[field])) < 50 else str(manifest[field])[:47] + '...'}")
                else:
                    errors.append(f"Missing manifest field: {field}")
                    print(f"  ❌ {field}")
            
            # Check version format
            version = manifest.get("version", "")
            if version:
                parts = version.split(".")
                if len(parts) == 3 and all(part.isdigit() for part in parts):
                    print(f"  ✅ Version format: {version}")
                else:
                    warnings.append(f"Version format should be x.y.z: {version}")
                    print(f"  ⚠️  Version format: {version}")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON in manifest: {e}")
            print(f"  ❌ JSON error: {e}")
    
    # Validate Python syntax
    python_files = [
        "server/claude_jester_desktop.py",
        "server/standalone_mcp_server.py", 
        "server/utils/notifications.py",
        "server/utils/security.py",
        "scripts/build.py"
    ]
    
    print("\n🐍 Validating Python syntax...")
    for file_name in python_files:
        file_path = base_dir / file_name
        if file_path.exists():
            try:
                with open(file_path) as f:
                    ast.parse(f.read())
                print(f"  ✅ {file_name}")
            except SyntaxError as e:
                errors.append(f"Syntax error in {file_name}: {e}")
                print(f"  ❌ {file_name}: {e}")
        else:
            warnings.append(f"Python file not found: {file_name}")
            print(f"  ⚠️  {file_name}: Not found")
    
    # Calculate extension size
    print("\n📊 Extension statistics...")
    total_files = len(list(base_dir.rglob('*')))
    total_size = sum(f.stat().st_size for f in base_dir.rglob('*') if f.is_file())
    print(f"  📁 Total files: {total_files}")
    print(f"  💾 Total size: {total_size / 1024 / 1024:.1f} MB")
    
    # Summary
    print("\n📋 Validation Summary:")
    print("=" * 30)
    
    if not errors:
        print("🎉 All validation checks passed!")
        print("✅ Extension is ready for building")
        
        print("\n🚀 Next steps:")
        print("1. Run: python scripts/build.py")
        print("2. Test the generated .dxt file")
        print("3. Install in Claude Desktop")
        
        return True
    else:
        print(f"❌ {len(errors)} errors found:")
        for error in errors:
            print(f"  • {error}")
        
        if warnings:
            print(f"\n⚠️  {len(warnings)} warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        return False

if __name__ == "__main__":
    success = validate_extension()
    exit(0 if success else 1)
