#!/usr/bin/env python3
"""
Basic unit tests for Claude-Jester Desktop Extension
"""

import pytest
import tempfile
import os
from pathlib import Path

def test_directory_structure():
    """Test that required directories exist"""
    base_dir = Path(__file__).parent.parent
    
    required_dirs = [
        "server",
        "server/utils", 
        "scripts",
        "tests",
        "assets"
    ]
    
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        assert dir_path.exists(), f"Required directory {dir_name} not found"
        assert dir_path.is_dir(), f"{dir_name} is not a directory"

def test_required_files():
    """Test that required files exist"""
    base_dir = Path(__file__).parent.parent
    
    required_files = [
        "manifest.json",
        "server/claude_jester_desktop.py",
        "server/__init__.py",
        "server/utils/__init__.py",
        "server/utils/notifications.py",
        "server/utils/security.py",
        "scripts/build.py",
        "requirements.txt",
        "README.md",
        "SECURITY.md",
        "CHANGELOG.md"
    ]
    
    for file_name in required_files:
        file_path = base_dir / file_name
        assert file_path.exists(), f"Required file {file_name} not found"
        assert file_path.is_file(), f"{file_name} is not a file"

def test_manifest_json():
    """Test that manifest.json is valid JSON"""
    import json
    
    base_dir = Path(__file__).parent.parent
    manifest_file = base_dir / "manifest.json"
    
    with open(manifest_file) as f:
        manifest = json.load(f)
    
    # Check required fields
    required_fields = ["dxt_version", "name", "version", "description", "server"]
    for field in required_fields:
        assert field in manifest, f"Required field {field} missing from manifest"
    
    # Check version format
    version = manifest["version"]
    parts = version.split(".")
    assert len(parts) == 3, f"Version {version} should have 3 parts (x.y.z)"
    for part in parts:
        assert part.isdigit(), f"Version part {part} should be numeric"

def test_python_syntax():
    """Test that all Python files have valid syntax"""
    import ast
    
    base_dir = Path(__file__).parent.parent
    
    python_files = [
        "server/claude_jester_desktop.py",
        "server/utils/notifications.py", 
        "server/utils/security.py",
        "scripts/build.py"
    ]
    
    for file_name in python_files:
        file_path = base_dir / file_name
        if file_path.exists():
            with open(file_path) as f:
                try:
                    ast.parse(f.read())
                except SyntaxError as e:
                    pytest.fail(f"Syntax error in {file_name}: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
