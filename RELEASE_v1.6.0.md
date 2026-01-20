# FIT Running Data Analyzer v1.6.0 Release Notes

**Release Date**: 2026-01-19

## 🍎 Major Update: macOS Cross-Platform Support

### Overview
Version 1.6.0 brings full macOS support, making FIT Running Data Analyzer available on both Windows and macOS platforms with identical features and user experience.

## ✨ New Features

### FR026: macOS Platform Support
- 🍎 **Native macOS .app Bundle** - Double-click to launch native macOS application
- 🏃 **Application Icon** - Running-themed icon for both Windows and macOS (app_icon.ico/icns)
- 🖥️ **Terminal Window** - Console window remains visible showing server status (configurable)
- 📦 **Cross-Platform Build System** - Automated platform detection and packaging

### FR027: Auto Browser Launch
- 🚀 **Automatic Opening** - Browser automatically opens after server starts (packaged versions only)
- ⏱️ **Smart Delay** - 1.5s delay ensures server is fully ready
- 🎯 **Correct Port** - Opens at http://127.0.0.1:8082

### FR028: UI Version Display
- 📌 **Bottom-Right Display** - Version number shown in UI (e.g., "v1.6.0")
- 🎨 **Consistent Styling** - Black text, smaller font, subtle opacity
- 🔄 **Dynamic Loading** - Version fetched from backend API

### FR029: Port Change 8080 → 8082
- 🔧 **New Default Port** - Changed from 8080 to 8082 to avoid common conflicts
- 🌐 **Global Update** - All references updated across codebase

### FR030: English Interface
- 🌍 **Unified Language** - All startup messages, scripts, and build logs in English
- 🔤 **Consistent Text** - Windows and macOS show identical startup messages
- 📝 **Script Names** - Windows startup script renamed to `start_server.bat`

## 🔧 Technical Implementation

### Cross-Platform Build System
**File**: `build.py`
- Auto-detects operating system (`platform.system()`)
- Reads version from `config.py` automatically
- Windows: Generates `.exe` with icon + `start_server.bat`
- macOS: Generates `.app` bundle with icon and metadata

### PyInstaller Configuration
**File**: `fitanalysis.spec`
- Platform detection logic
- Windows: `icon='app_icon.ico'`
- macOS: BUNDLE configuration with `icon='app_icon.icns'`
- Metadata: CFBundleName, CFBundleVersion, etc.

### Backend Updates
**File**: `backend/main.py`
- `/api/version` endpoint returns version from config
- English startup messages with version display
- Auto browser launch (webbrowser + threading)
- Port 8082 configuration
- Fixed duplicate startup message issue

### Frontend Updates
**Files**: `frontend/index.html`, `frontend/js/app.js`, `frontend/css/styles.css`
- Version display element in HTML
- JavaScript function to fetch and display version
- CSS styling for bottom-right positioning

### Development Scripts
- **Windows**: `run.bat` - Updated to English, port 8082
- **macOS**: `run.sh` - New UTF-8 script with English messages

## 🐛 Bug Fixes

### Bug #26: Missing favicon.ico
- ✅ Added `/favicon.ico` route serving `app_icon.ico`
- ✅ Added `<link rel="icon">` in HTML
- ✅ No more 404 errors in logs

### Bug #27: Duplicate Startup Messages
- ✅ Fixed double printing in packaged Windows version
- ✅ Added main process detection to prevent reload-triggered duplicates

## 📦 Installation & Usage

### Windows

#### Option 1: Packaged Executable (Recommended)
1. Download `fitanalysis-v1.6.0-windows.zip`
2. Extract to any directory
3. Double-click `fitanalysis.exe` or `start_server.bat`
4. Browser opens automatically at http://127.0.0.1:8082

#### Option 2: Development Mode
1. Run `run.bat` to setup and start
2. Or manually: `python build.py` then run the executable

### macOS

#### Option 1: Packaged Application (Recommended)
1. Download `fitanalysis-v1.6.0-macos.zip`
2. Extract `fitanalysis.app`
3. **First time**: Right-click → Open (bypass Gatekeeper)
4. **Subsequent**: Double-click to launch
5. Browser opens automatically at http://127.0.0.1:8082

**macOS Security Note**: Unsigned apps require manual approval:
- System Preferences → Security & Privacy → Click "Open Anyway"

#### Option 2: Development Mode
1. Run `chmod +x run.sh` (first time only)
2. Run `./run.sh` to setup and start

## 🔄 Upgrading from v1.5.0

### Windows
1. Backup your `data/` directory (optional, data is compatible)
2. Extract new version to replace old files
3. Launch as usual - all existing activities work

### macOS (New Installation)
1. Download macOS package
2. Follow installation steps above
3. Optionally copy existing `data/` folder from Windows installation

**Data Compatibility**: ✅ All v1.5.0 activity data works in v1.6.0

## 📊 Version Comparison

| Feature | v1.5.0 | v1.6.0 |
|---------|--------|--------|
| Windows Support | ✅ | ✅ |
| macOS Support | ❌ | ✅ New |
| Auto Browser Launch | ❌ | ✅ New |
| UI Version Display | ❌ | ✅ New |
| Server Port | 8080 | 8082 Changed |
| Startup Messages | Chinese | English |
| Application Icon | ❌ | ✅ New |
| Favicon Support | ❌ | ✅ Fixed |

## 🎯 Platform Compatibility Matrix

| OS | Development | Packaged | Build Platform |
|----|-------------|----------|----------------|
| Windows 10/11 | ✅ run.bat | ✅ .exe | Windows |
| macOS 10.15+ | ✅ run.sh | ✅ .app | macOS |
| Linux | ✅ run.sh | ⚠️ Not tested | Linux |

## 🛠️ Build Instructions

### Build Windows Package (on Windows)
```bash
python build.py
# Output: dist/fitanalysis/fitanalysis.exe
```

### Build macOS Package (on macOS)
```bash
python build.py
# Output: dist/fitanalysis.app
```

### Build Requirements
- Python 3.8+ (3.11+ recommended)
- PyInstaller (auto-installed by build.py)
- Platform-specific icon files (app_icon.ico/icns)

## 📝 Complete Changelog

### Added
- ✨ macOS platform support with .app bundle packaging
- ✨ Auto browser launch on application startup
- ✨ Version number display in UI (bottom-right)
- ✨ Application icon for Windows (.ico) and macOS (.icns)
- ✨ Favicon support to eliminate 404 errors
- ✨ `/api/version` endpoint
- ✨ macOS development script `run.sh`
- 📚 Development guidelines in agent.md
- 📚 macOS installation instructions in README.md

### Changed
- 🔧 Server port from 8080 to 8082 (global update)
- 🌍 All startup messages to English for cross-platform consistency
- 🔧 Windows startup script renamed to `start_server.bat`
- 🔧 Page title to "FIT Running Data Analyzer" (English)
- 🔧 Build system to auto-detect platform and read version from config.py

### Fixed
- 🐛 Missing favicon.ico causing 404 errors
- 🐛 Duplicate startup messages in Windows packaged version
- 🐛 Platform-specific path handling in build system

## 🧪 Testing

### Tested Platforms
- ✅ Windows 10/11 - Development mode (run.bat)
- ✅ Windows 11 - Packaged .exe with icon
- ⏳ macOS - Pending testing after deployment

### Test Scenarios
1. ✅ Development mode startup on Windows
2. ✅ Windows build with icon and auto browser
3. ✅ Version display in UI
4. ✅ Port 8082 accessibility
5. ✅ Favicon loading
6. ✅ No duplicate startup messages

### Known Issues
- None reported for v1.6.0

## 📚 Documentation Updates

- Updated `README.md` with macOS instructions
- Updated `agent.md` with v1.6.0 specification
- Added development guidelines in agent.md
- Updated `BUGS.md` with fixed issues

## 🔜 Future Enhancements

Potential for v1.7.0:
- Code signing for macOS (eliminate Gatekeeper warnings)
- Linux .deb/.rpm packages
- Automated release builds via GitHub Actions
- Multi-language UI support

---

**Previous Version**: [v1.5.0](RELEASE_v1.5.0.md)  
**Next Version**: In development

## 🙏 Acknowledgments

Thank you to all users for testing and feedback!

**Questions or Issues?** Check [BUGS.md](BUGS.md) or open an issue.
