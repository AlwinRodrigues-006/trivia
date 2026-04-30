# -*- mode: python ; coding: utf-8 -*-
# trivia.spec — PyInstaller packaging spec for the Trivia application.
#
# Run from the project root:
#   pyinstaller --clean trivia.spec
#
# Output executable: dist/trivia  (Linux/macOS) or dist/trivia.exe (Windows)

import os

block_cipher = None

# ---------------------------------------------------------------------------
# Data files to bundle
# ---------------------------------------------------------------------------

datas = [
    # SQL seed script (read at runtime by main.py)
    ("backend/trivia.psql", "."),
]

# Bundle the React production build if it has been compiled already.
# The build step in build.sh ensures this directory exists before packaging.
react_build_dir = os.path.join("frontend", "build")
if os.path.isdir(react_build_dir):
    datas.append((react_build_dir, "build"))

# ---------------------------------------------------------------------------
# Hidden imports that PyInstaller cannot detect via static analysis
# ---------------------------------------------------------------------------

hiddenimports = [
    # PostgreSQL driver
    "psycopg2",
    "psycopg2._psycopg",
    "psycopg2.extensions",
    # SQLAlchemy PostgreSQL dialect
    "sqlalchemy.dialects.postgresql",
    "sqlalchemy.dialects.postgresql.psycopg2",
    # Flask extensions
    "flask_sqlalchemy",
    "flask_cors",
    # python-dotenv
    "dotenv",
    # Standard-library modules sometimes missed
    "email.mime.text",
    "email.mime.multipart",
]

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------

a = Analysis(
    ["backend/main.py"],
    pathex=["backend"],         # so that `from app import ...` resolves
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Single-file executable (all dependencies embedded)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="trivia",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,               # keep console for log output
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
