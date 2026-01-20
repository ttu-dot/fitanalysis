# FIT Running Data Analyzer v1.7.0 Release Checklist

## 📋 Pre-Release Checklist

### 1. Code Preparation
- [x] Update version in `config.py`: VERSION = "1.7.0"
- [x] Update version in `fitanalysis.spec`: CFBundleShortVersionString = "1.7.0"
- [x] Update version in `agent.md`: Section 14版本发布记录
- [ ] Code committed to git

### 2. Feature Implementation

#### 2.1 localStorage Persistence
- [x] Add `saveFieldSelection()` function in charts.js
- [x] Add `loadFieldSelection()` function in charts.js
- [ ] Test localStorage save/load for trend fields
- [ ] Test localStorage save/load for lap fields
- [ ] Test default value fallback when no saved data

#### 2.2 Field Groups Configuration
- [x] Define `FIELD_GROUPS` in charts.js
- [x] Define `LAP_FIELD_GROUPS` in charts.js
- [ ] Verify standard field grouping correctness
- [ ] Verify IQ field grouping correctness
- [ ] Test uncategorized field auto-categorization

#### 2.3 Unified Field Selector Refactoring
- [x] Add `groupFieldsByConfig()` helper function
- [x] Refactor `renderUnifiedFieldSelector()` to support grouping
- [x] Add control buttons (全选/全不选/展开折叠全部)
- [x] Add collapsible group support
- [ ] Test group expand/collapse interaction
- [ ] Test "Select All" button
- [ ] Test "Deselect All" button
- [ ] Test "Toggle All Groups" button

#### 2.4 Trend Chart Field Selector Update
- [x] Update `renderFieldSelector()` to use FIELD_GROUPS
- [x] Add localStorage persistence support
- [ ] Test trend field selection persistence
- [ ] Test field grouping display
- [ ] Test group collapse/expand
- [ ] Test backward compatibility (no regression)

#### 2.5 Lap Field Selector Implementation
- [x] Add `extractAvailableLapFields()` in app.js
- [x] Add `renderLapFieldSelector()` in app.js
- [x] Add `formatRelativeTime()` in app.js
- [x] Add field selector container in index.html
- [ ] Test lap field extraction (standard + IQ)
- [ ] Test 100% empty field filtering
- [ ] Test lap field selection persistence
- [ ] Test lap field selector UI rendering

#### 2.6 Lap Table Dynamic Rendering
- [x] Refactor `renderLapsTable()` to accept selectedFields
- [x] Implement dynamic column generation
- [x] Add relative time formatting for start_time
- [ ] Test dynamic table header generation
- [ ] Test dynamic table body generation
- [ ] Test field value formatting (time/distance/pace/etc)
- [ ] Test IQ field value display
- [ ] Test relative time display (+MM:SS format)

#### 2.7 CSS Styling
- [x] Add `.field-selector-controls` styles
- [x] Add button styles (select-all/deselect-all/toggle-groups)
- [x] Add `.field-group.collapsible` styles
- [x] Add `.field-group-header` styles
- [x] Add `.toggle-icon` with rotation animation
- [x] Add `.field-group-content` with collapse state
- [ ] Test styling consistency across browsers
- [ ] Test responsive behavior (window resize)
- [ ] Test animation smoothness

### 3. Testing & Validation

#### 3.1 Functional Testing

**Field Grouping:**
- [ ] Standard fields display in correct groups
- [ ] IQ fields display in correct groups
- [ ] Uncategorized IQ fields auto-added to "未分类" group
- [ ] Imported fields match pattern and display in "导入数据" group
- [ ] All groups default to expanded state

**Group Interaction:**
- [ ] Click group header to toggle expand/collapse
- [ ] Toggle icon rotates correctly (▼ → ▶)
- [ ] "展开/折叠全部" button toggles all groups
- [ ] Group content shows/hides correctly

**Control Buttons:**
- [ ] "全选" button checks all visible checkboxes
- [ ] "全不选" button unchecks all checkboxes
- [ ] Button clicks trigger onChange callback
- [ ] Button state updates correctly

**localStorage Persistence:**
- [ ] Trend field selection saves to 'trend_selected_fields'
- [ ] Lap field selection saves to 'lap_selected_fields'
- [ ] Page refresh restores saved selections
- [ ] Default values used when no saved data exists
- [ ] Invalid saved data handled gracefully

**Empty Field Filtering:**
- [ ] Fields with 100% null values are hidden
- [ ] Fields with partial null values are shown
- [ ] Empty filtering works for standard fields
- [ ] Empty filtering works for IQ fields

**Lap Table Rendering:**
- [ ] Table displays selected fields only
- [ ] Table header shows correct field labels
- [ ] Table cells show correctly formatted values
- [ ] lap_number displays as integer
- [ ] total_elapsed_time displays as MM:SS
- [ ] total_distance displays as X.XX km
- [ ] avg_speed/max_speed display as MM:SS pace
- [ ] start_time displays as +MM:SS relative time
- [ ] total_ascent/total_descent display as Xm
- [ ] IQ field values display correctly
- [ ] Empty cells display '--'

**Activity Switching:**
- [ ] Field selections restore correctly when switching activities
- [ ] Different activities can have different field selections
- [ ] localStorage keys remain independent

**Backward Compatibility:**
- [ ] Existing export functionality works unchanged
- [ ] Multi-activity compare works unchanged
- [ ] No regression in existing features
- [ ] Activities without laps handle gracefully

#### 3.2 Cross-Browser Testing
- [x] **Chrome** (latest): All features working
- [x] **Edge** (latest): All features working (Bug #28 fixed - script load order)
- [ ] **Firefox** (latest): All features working
- [ ] **Safari** (macOS): All features working

#### 3.3 Platform Testing
- [ ] **Windows**: Field selectors render correctly
- [ ] **macOS**: Field selectors render correctly
- [ ] **Windows**: localStorage persistence works
- [ ] **macOS**: localStorage persistence works

### 4. Documentation Updates

- [x] Update `agent.md` Section 6.2 (Field Selector Component Design)
- [x] Update `agent.md` Section 14 (Version History - v1.7.0)
- [x] Create `RELEASE_v1.7.0.md` (Release Notes)
- [x] Create `RELEASE_CHECKLIST_v1.7.0.md` (This document)
- [ ] Update `README.md` if needed

### 5. Build & Package

#### 5.1 Build Preparation
- [ ] Verify all tests pass
- [ ] Verify no console errors
- [ ] Verify no compilation warnings
- [ ] Clean build artifacts: `rm -rf build/ dist/`

#### 5.2 Windows Build
- [ ] Run `python build.py` on Windows
- [ ] Verify `dist/fitanalysis.exe` created
- [ ] Verify `dist/start_server.bat` created
- [ ] Test executable runs and starts server
- [ ] Test browser auto-opens to http://127.0.0.1:8082
- [ ] Test field selectors display correctly
- [ ] Test localStorage persistence works
- [ ] Create ZIP: `fitanalysis-v1.7.0-windows.zip`

#### 5.3 macOS Build
- [ ] Run `python build.py` on macOS
- [ ] Verify `dist/FitAnalysis.app` created
- [ ] Test .app bundle runs and starts server
- [ ] Test browser auto-opens to http://127.0.0.1:8082
- [ ] Test field selectors display correctly
- [ ] Test localStorage persistence works
- [ ] Create ZIP: `fitanalysis-v1.7.0-macos.zip`

### 6. Final Checks

- [ ] All features from RELEASE_v1.7.0.md implemented
- [ ] No critical bugs found
- [ ] Documentation complete and accurate
- [ ] Release notes reviewed
- [ ] Code committed and tagged: `git tag v1.7.0`

### 7. Post-Release

- [ ] Upload release packages
- [ ] Publish release notes
- [ ] Update distribution channels
- [ ] Monitor for bug reports

---

## 🚀 Release Approval

**Prepared by**: _______________  
**Date**: _______________

**Reviewed by**: _______________  
**Date**: _______________

**Approved for release**: [ ] Yes [ ] No

**Release Date**: _______________

---

## 📝 Notes

### Known Issues (if any)
_None currently (Bug #28 fixed - Edge browser script loading order issue)_

### Deferred Items (if any)
_None currently_

### Additional Testing Notes
_Add notes here during testing_

---

**Checklist Version**: 1.0  
**Last Updated**: 2026-01-19
