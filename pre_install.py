#!/usr/bin/env python3
"""
Pre-installation script for AI Inventory app
This script installs required packages before Frappe tries to load the modules
"""

import subprocess
import sys
import os

def install_package(package):
    """Install a single package"""
    try:
        print(f"Installing {package}...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", package, 
            "--upgrade", "--no-cache-dir"
        ], capture_output=True, text=True, check=True, timeout=300)
        print(f"✅ {package} installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package}: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error installing {package}: {str(e)}")
        return False

def main():
    """Main installation function"""
    print("🚀 AI Inventory Pre-Installation: Installing required packages...")
    
    packages = [
        "numpy>=1.21.0",
        "pandas>=1.3.0", 
        "scikit-learn>=1.0.0",
        "matplotlib>=3.3.0",
        "scipy>=1.7.0"
    ]
    
    failed_packages = []
    
    for package in packages:
        if not install_package(package):
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n⚠️  Some packages failed to install: {', '.join(failed_packages)}")
        print("You can install them manually later with:")
        for pkg in failed_packages:
            print(f"  pip install {pkg}")
        return 1
    else:
        print("✅ All packages installed successfully!")
        return 0

if __name__ == "__main__":
    exit(main())
