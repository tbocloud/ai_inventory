# VS Code Optimization Guide for AI Inventory

## 🚀 Performance Optimizations Applied

The following optimizations have been configured to improve VS Code performance:

### ✅ Files Created:
- `.vscode/settings.json` - Core performance settings
- `.vscode/extensions.json` - Recommended/unwanted extensions
- `.vscodeignore` - Files to exclude from VS Code indexing

### ⚙️ Key Optimizations:

1. **Python Analysis**: Disabled heavy analysis features
2. **File Watching**: Excluded large directories (env, sites, logs)
3. **Search Exclusions**: Faster search by ignoring irrelevant files
4. **Linting**: Disabled resource-intensive linters
5. **Type Checking**: Turned off for better performance

### 🔧 Next Steps:

1. **Restart VS Code** completely
2. **Open only the ai_inventory folder** (not the whole bench)
3. **Select the correct Python interpreter**: `../../../../env/bin/python`
4. **Wait for initial indexing** (1-2 minutes)

### 📊 Expected Improvements:
- ✅ 50-70% faster file opening
- ✅ Reduced CPU usage
- ✅ Quicker autocomplete
- ✅ Less memory consumption
- ✅ Faster search operations

### 🐛 If Still Slow:

1. Check if you have many browser tabs open
2. Close other heavy applications
3. Consider increasing VS Code's memory limit
4. Use `code --disable-extensions` to test without extensions

### 💡 Additional Tips:

- Work with individual files rather than browsing the entire tree
- Use `Ctrl+P` (Quick Open) instead of file explorer for navigation
- Close unused editor tabs
- Use workspace-specific settings for different projects
