# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run.py'],
    pathex=['src', '.'],
    binaries=[],
    datas=[('serviceAccountKey.json', '.'), ('.env', '.'), ('.env.example', '.'), ('data', 'data')],
    hiddenimports=['PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets', 'PyQt5.QtPrintSupport', 'PyQt5.sip', 'firebase_admin', 'firebase_admin.credentials', 'firebase_admin.db', 'firebase_admin.firestore', 'firebase_admin.auth', 'google.cloud.firestore', 'google.cloud.firestore_v1', 'google.auth', 'google.auth.transport.requests', 'google.oauth2.credentials', 'grpc', 'grpc._cython', 'pandas', 'pandas._libs', 'pandas._libs.tslibs.base', 'numpy', 'openpyxl', 'reportlab', 'reportlab.lib', 'reportlab.platypus', 'reportlab.pdfgen', 'reportlab.graphics', 'PIL', 'PIL._tkinter_finder', 'matplotlib', 'matplotlib.pyplot', 'matplotlib.figure', 'matplotlib.backends.backend_qt5agg', 'matplotlib.backends.backend_agg', 'dotenv', 'cryptography', 'json', 'logging', 'datetime', 'encodings', 'encodings.utf_8', 'encodings.ascii'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'scipy', 'IPython', 'notebook', 'pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='PPMS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
