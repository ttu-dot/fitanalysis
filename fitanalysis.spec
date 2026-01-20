# -*- mode: python ; coding: utf-8 -*-

import sys
import platform

block_cipher = None

# Detect platform
is_macos = sys.platform == 'darwin'
is_windows = sys.platform == 'win32'

# Icon file based on platform
if is_windows:
    icon_file = 'app_icon.ico'
elif is_macos:
    icon_file = 'app_icon.icns'
else:
    icon_file = None

a = Analysis(
    ['backend/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('frontend', 'frontend'),
        ('backend/*.py', 'backend'),
        ('README.md', '.'),
    ],
    hiddenimports=[
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fitdecode',
        'pandas',
        'backend.models',
        'backend.fit_parser',
        'backend.data_store',
        'backend.csv_exporter',
        'backend.device_mappings',
        'backend.field_units',
        'backend.hr_csv_merge',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'test_api',
        'test_iq_fix',
        'diagnose_fit',
        'verify_vosc_fix',
        'charts.test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fitanalysis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep terminal window visible on both platforms
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file if icon_file else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='fitanalysis',
)

# macOS .app bundle
if is_macos:
    app = BUNDLE(
        coll,
        name='fitanalysis.app',
        icon=icon_file,
        bundle_identifier='com.fitanalysis.app',
        info_plist={
            'CFBundleName': 'FIT Running Data Analyzer',
            'CFBundleDisplayName': 'FIT Running Data Analyzer',
            'CFBundleShortVersionString': '1.8.0',
            'CFBundleVersion': '1.8.0',
            'NSHighResolutionCapable': 'True',
        },
    )

