#!/usr/bin/env python3
"""
Claude-Jester Desktop Extension Setup and Build Script
One-command setup for production deployment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"Output: {e.stdout}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def main():
    print("🃏 Claude-Jester Desktop Extension Setup & Build")
    print("=" * 55)
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required. Current: {python_version.major}.{python_version.minor}")
        return False
    
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Change to extension directory
    extension_dir = Path(__file__).parent
    os.chdir(extension_dir)
    
    # Step 1: Validate extension
    print("\n📋 Step 1: Validating extension...")
    if not run_command("python3 validate_extension.py", "Extension validation"):
        return False
    
    # Step 2: Install dependencies (optional)
    print("\n📦 Step 2: Installing dependencies...")
    if run_command("python3 -m pip install --user -r requirements.txt", "Dependency installation"):
        print("✅ Dependencies installed")
    else:
        print("⚠️  Dependencies install failed (optional for building)")
    
    # Step 3: Build extension
    print("\n🔨 Step 3: Building extension...")
    if not run_command("python3 scripts/build.py", "Extension build"):
        return False
    
    # Step 4: Validate package
    print("\n🔍 Step 4: Validating package...")
    dist_dir = Path("dist")
    if dist_dir.exists():
        dxt_files = list(dist_dir.glob("*.dxt"))
        if dxt_files:
            dxt_file = dxt_files[0]
            print(f"✅ Package created: {dxt_file}")
            print(f"📦 Size: {dxt_file.stat().st_size / 1024 / 1024:.1f} MB")
            
            # Check installation scripts
            install_dir = dist_dir / "installation"
            if install_dir.exists():
                print("✅ Installation scripts created")
            
            return True
        else:
            print("❌ No .dxt file found in dist/")
            return False
    else:
        print("❌ dist/ directory not found")
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 BUILD SUCCESSFUL!")
        print("=" * 20)
        print("\n📥 Installation Instructions:")
        print("1. Open Claude Desktop")
        print("2. Go to Settings → Extensions")
        print("3. Drag the .dxt file from dist/ into the Extensions panel")
        print("4. Configure your preferences")
        print("5. Start quantum debugging! 🌌")
        
        print("\n🔧 Development Commands:")
        print("• Validate: python3 validate_extension.py")
        print("• Build: python3 scripts/build.py")
        print("• Test: python3 -m pytest tests/ (requires pytest)")
        
        print("\n📚 Documentation:")
        print("• README.md - Complete user guide")
        print("• SECURITY.md - Security policy")
        print("• docs/ - Additional documentation")
        
    else:
        print("\n❌ BUILD FAILED!")
        print("Check the errors above and fix them before building.")
    
    exit(0 if success else 1)
