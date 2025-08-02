# 🚀 Installation Troubleshooting Guide

## Common Installation Issues

### 1. "No module named 'pandas'" Error

This error occurs when pandas (or other ML packages) are not installed before the app migration.

**Solution Options:**

#### Option A: Pre-install packages (Recommended)

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Install packages first
./env/bin/pip install numpy>=1.21.0 pandas>=1.3.0 scikit-learn>=1.0.0

# Then install the app
bench get-app https://github.com/yourusername/ai_inventory.git
bench --site your-site-name install-app ai_inventory
bench --site your-site-name migrate
```

#### Option B: Use the installation script

```bash
# Navigate to your bench directory
cd /path/to/your/bench

# Download and run the installation script
wget https://raw.githubusercontent.com/yourusername/ai_inventory/main/install.sh
chmod +x install.sh
./install.sh
```

#### Option C: Manual step-by-step installation

```bash
# 1. Install packages
./env/bin/pip install -r apps/ai_inventory/requirements.txt

# 2. Install app (skip if already done)
bench --site your-site-name install-app ai_inventory

# 3. Run migrations
bench --site your-site-name migrate

# 4. Restart and clear cache
bench restart
bench --site your-site-name clear-cache
```

### 2. Migration Failures

If migration fails due to missing packages:

```bash
# 1. Install missing packages
./env/bin/pip install numpy pandas scikit-learn matplotlib scipy

# 2. Try migration again
bench --site your-site-name migrate --skip-failing

# 3. If still failing, restart and try again
bench restart
bench --site your-site-name migrate
```

### 3. Package Installation Failures

If package installation fails:

```bash
# Update pip first
./env/bin/pip install --upgrade pip

# Install packages with no cache
./env/bin/pip install --no-cache-dir numpy>=1.21.0
./env/bin/pip install --no-cache-dir pandas>=1.3.0
./env/bin/pip install --no-cache-dir scikit-learn>=1.0.0

# Verify installation
./env/bin/python -c "import numpy, pandas, sklearn; print('All packages imported successfully')"
```

### 4. Version Conflicts

If you encounter version conflicts:

```bash
# Create a clean virtual environment
python3 -m venv clean_env
source clean_env/bin/activate

# Install specific versions
pip install numpy==1.21.6 pandas==1.3.5 scikit-learn==1.0.2

# Copy packages to bench env
cp -r clean_env/lib/python*/site-packages/* env/lib/python*/site-packages/
```

## System Requirements

### Minimum Requirements
- Python 3.8+
- ERPNext v14+
- 4GB RAM
- 2GB free disk space

### Recommended Requirements
- Python 3.10+
- ERPNext v15+
- 8GB RAM
- 10GB free disk space

## Pre-Installation Checklist

Before installing AI Inventory, ensure:

- [ ] ERPNext is properly installed and running
- [ ] You have System Manager permissions
- [ ] Python development tools are installed (`python3-dev`)
- [ ] Sufficient disk space is available
- [ ] Internet connection for downloading packages

## Package Dependencies

The app requires these Python packages:

```
numpy>=1.21.0         # Numerical computing
pandas>=1.3.0         # Data manipulation
scikit-learn>=1.0.0   # Machine learning
matplotlib>=3.3.0     # Plotting (optional)
scipy>=1.7.0          # Scientific computing
```

## Installation Verification

After installation, verify everything is working:

```bash
# Check package installation
./env/bin/python -c "
import numpy as np
import pandas as pd
import sklearn
print(f'NumPy: {np.__version__}')
print(f'Pandas: {pd.__version__}')
print(f'Scikit-learn: {sklearn.__version__}')
print('✅ All packages are properly installed')
"

# Check app installation
bench --site your-site-name console

# In the console, run:
import frappe
frappe.get_all("AI Inventory Forecast", limit=1)
# Should not throw an error
```

## Getting Help

If you continue to have issues:

1. **Check the logs:**
   ```bash
   tail -f logs/worker.error.log
   tail -f logs/web.error.log
   ```

2. **Verify your environment:**
   ```bash
   ./env/bin/python --version
   ./env/bin/pip list | grep -E "(numpy|pandas|sklearn)"
   ```

3. **Contact support:**
   - Create an issue on GitHub
   - Include error logs and system information
   - Specify your ERPNext and Python versions

## Quick Fix Commands

Common quick fixes:

```bash
# Restart everything
bench restart && bench --site your-site-name clear-cache

# Reinstall packages
./env/bin/pip install --force-reinstall numpy pandas scikit-learn

# Reset migrations (CAUTION: This will lose data)
bench --site your-site-name console
# In console: frappe.db.sql("DELETE FROM tabSingles WHERE doctype = 'AI Settings'")

# Rebuild and retry
bench build
bench --site your-site-name migrate
```
