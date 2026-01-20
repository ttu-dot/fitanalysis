# FIT Running Data Analyzer v1.6.0 Release Checklist

## 📋 Pre-Release Checklist

### 1. Code Preparation
- [x] Update version in `config.py`: VERSION = "1.6.0"
- [x] Update port in `config.py`: PORT = 8082
- [x] Update version in `fitanalysis.spec`: CFBundleShortVersionString = "1.6.0"
- [x] Update version in `build.py`: Auto-read from config.py
- [x] Code committed to git: ⏳ Pending

### 2. Cross-Platform Implementation
- [x] **Backend Updates** (`backend/main.py`):
  - [x] Add `/api/version` endpoint
  - [x] Change port from 8080 to 8082
  - [x] Add English startup messages
  - [x] Add auto browser launch (webbrowser + threading)
  - [x] Add favicon.ico route
  - [x] Fix duplicate startup message issue
  
- [x] **Frontend Updates**:
  - [x] Add version display in `frontend/index.html`
  - [x] Add version loading in `frontend/js/app.js`
  - [x] Add version styling in `frontend/css/styles.css`
  - [x] Add favicon link in HTML
  - [x] Update page title to English
  
- [x] **Build System** (`build.py`):
  - [x] Add platform detection (platform.system())
  - [x] Auto-read VERSION from config.py
  - [x] Windows: Generate .exe with icon + start_server.bat
  - [x] macOS: Generate .app bundle with icon
  - [x] English build messages
  
- [x] **PyInstaller Configuration** (`fitanalysis.spec`):
  - [x] Add platform detection
  - [x] Windows icon configuration (app_icon.ico)
  - [x] macOS BUNDLE configuration (app_icon.icns)
  - [x] macOS metadata (CFBundleName, etc.)
  
- [x] **Development Scripts**:
  - [x] Update `run.bat` to English and port 8082
  - [x] Create `run.sh` for macOS (UTF-8, English, port 8082)

### 3. Testing & Validation

#### Windows Testing
- [x] Development mode (`run.bat`)
  - [x] Server starts on port 8082
  - [x] English startup messages displayed
  - [x] Browser accessible at http://127.0.0.1:8082
  - [x] Version "v1.6.0" displayed in UI bottom-right
  - [x] Favicon loads without 404 errors
  
- [x] Build test (`python build.py`)
  - [x] Build completes successfully
  - [x] `dist/fitanalysis/fitanalysis.exe` created with icon
  - [x] `start_server.bat` generated with English text
  - [x] README.md and RELEASE_v1.6.0.md copied to dist
  
- [x] Packaged version test
  - [x] Double-click `fitanalysis.exe` launches
  - [x] Startup message displays once (not twice)
  - [x] Browser opens automatically
  - [x] All core features work (upload, list, detail, compare, export)

#### macOS Testing
- [ ] Development mode (`./run.sh`)
  - [ ] Virtual environment creates successfully
  - [ ] Dependencies install correctly
  - [ ] Server starts on port 8082
  - [ ] English startup messages displayed
  
- [ ] Build test (`python build.py`)
  - [ ] Build completes successfully on macOS
  - [ ] `dist/fitanalysis.app` created with icon
  - [ ] App bundle structure correct
  - [ ] Icon displays in Finder
  
- [ ] Packaged version test
  - [ ] Right-click → Open works (first time)
  - [ ] Double-click works (subsequent times)
  - [ ] Terminal window shows with startup messages
  - [ ] Browser opens automatically
  - [ ] All core features work

### 4. Documentation Updates
- [x] Create `RELEASE_v1.6.0.md`
- [x] Create `RELEASE_CHECKLIST_v1.6.0.md` (this file)
- [x] Update `README.md`:
  - [x] Version to 1.6.0
  - [x] Latest update section
  - [x] Port 8080 → 8082 globally
  - [x] Add macOS installation instructions
  - [x] Add Gatekeeper handling notes
- [x] Update `agent.md`:
  - [x] Add v1.6.0 specification in section 14
  - [x] Add development guidelines
  - [x] Update FR026-FR030 status to DONE
- [x] Update `BUGS.md`:
  - [x] Mark Bug #26 (favicon) as fixed
  - [x] Mark Bug #27 (duplicate messages) as fixed

### 5. Cleanup Work
- [ ] Delete temporary test files (if any)
- [ ] Delete cache directories:
  - [ ] `__pycache__/`
  - [ ] `.pytest_cache/`
  - [ ] `backend/__pycache__/`
- [ ] Delete old build artifacts:
  - [ ] `build/` directory
  - [ ] `dist/` directory (will rebuild)

### 6. Build & Package

#### Windows Package
- [x] Run `python build.py` on Windows
- [ ] Verify output:
  - [ ] `dist/fitanalysis/fitanalysis.exe` (with icon)
  - [ ] `dist/fitanalysis/start_server.bat`
  - [ ] `dist/fitanalysis/_internal/` (dependencies)
  - [ ] `dist/fitanalysis/README.md`
  - [ ] `dist/fitanalysis/RELEASE_v1.6.0.md`
- [ ] Test run the packaged version
- [ ] Create ZIP: `fitanalysis-v1.6.0-windows.zip`
- [ ] Verify ZIP size and contents

#### macOS Package
- [ ] Run `python build.py` on macOS
- [ ] Verify output:
  - [ ] `dist/fitanalysis.app`
  - [ ] `dist/README.md`
  - [ ] `dist/RELEASE_v1.6.0.md`
- [ ] Test run the .app bundle
- [ ] Create ZIP: `fitanalysis-v1.6.0-macos.zip`
- [ ] Verify ZIP size and contents

## 📦 Release Package Information

### Windows Package
- **Filename**: `fitanalysis-v1.6.0-windows.zip`
- **Estimated Size**: ~40 MB
- **Contents**:
  - fitanalysis.exe (with running icon)
  - start_server.bat (English)
  - _internal/ (dependencies)
  - README.md
  - RELEASE_v1.6.0.md

### macOS Package
- **Filename**: `fitanalysis-v1.6.0-macos.zip`
- **Estimated Size**: ~45 MB
- **Contents**:
  - fitanalysis.app (with running icon)
  - README.md
  - RELEASE_v1.6.0.md

## 🚀 Release Steps

### 1. GitHub Release

```bash
# Stage all changes
git add .

# Commit
git commit -m "Release v1.6.0: macOS cross-platform support

- Add macOS .app bundle packaging
- Add auto browser launch
- Add UI version display
- Change port 8080 → 8082
- Add favicon support
- Update all text to English
- Fix duplicate startup messages
- Add development guidelines"

# Create tag
git tag -a v1.6.0 -m "Release v1.6.0: macOS Cross-Platform Support"

# Push to remote
git push origin main
git push origin v1.6.0
```

### 2. Create GitHub Release

**Release Details**:
- **Tag**: `v1.6.0`
- **Title**: `v1.6.0 - macOS Cross-Platform Support`
- **Description**: Copy content from `RELEASE_v1.6.0.md`
- **Attachments**:
  - `fitanalysis-v1.6.0-windows.zip`
  - `fitanalysis-v1.6.0-macos.zip`

### 3. User Notification
- Update project homepage/README
- Post release announcement
- Notify testers to upgrade
- Highlight macOS availability

## ✅ Post-Release Verification

### GitHub Verification
- [ ] Release page displays correctly
- [ ] Tag appears in repository
- [ ] Both download links work

### Download & Installation Testing
- [ ] Windows ZIP downloads and extracts correctly
- [ ] macOS ZIP downloads and extracts correctly
- [ ] Windows .exe runs without issues
- [ ] macOS .app runs without issues (after Gatekeeper approval)

### Functionality Verification
- [ ] Version number shows "v1.6.0" in UI
- [ ] Server runs on port 8082
- [ ] Browser opens automatically
- [ ] Favicon displays in browser tab
- [ ] Upload FIT file works
- [ ] Activity list loads
- [ ] Charts render correctly
- [ ] Multi-activity compare works
- [ ] CSV export works

### Cross-Platform Consistency
- [ ] Windows and macOS show identical UI
- [ ] Windows and macOS show identical startup messages
- [ ] Windows and macOS have same feature set
- [ ] Data files are compatible between platforms

## 📝 Known Issues

### Windows
- None reported

### macOS
- Unsigned app requires manual Gatekeeper approval (documented in README)

### Both Platforms
- None reported

## 🔜 Post-Release Tasks

- [ ] Monitor for bug reports
- [ ] Gather user feedback
- [ ] Plan v1.7.0 features
- [ ] Consider code signing for macOS

## 📊 Version Comparison

| Aspect | v1.5.0 | v1.6.0 |
|--------|--------|--------|
| Platforms | Windows only | Windows + macOS |
| Port | 8080 | 8082 |
| Browser Launch | Manual | Auto |
| Version Display | No | Yes (UI) |
| Interface Language | Chinese | English |
| App Icon | No | Yes (both platforms) |
| Favicon | Missing (404) | Supported |

---

**Release Manager**: AI Assistant  
**Release Date**: 2026-01-19  
**Previous Version**: [v1.5.0](RELEASE_v1.5.0.md)  
**Next Version**: v1.7.0 (planned)
