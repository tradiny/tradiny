# This software is licensed under a dual-license model:
# 1. Under the Affero General Public License (AGPL) for open-source use.
# 2. With additional terms tailored to individual users (e.g., traders and investors):
#
#    - Individual users may use this software for personal profit (e.g., trading/investing)
#      without releasing proprietary strategies.
#
#    - Redistribution, public tools, or commercial use require compliance with AGPL
#      or a commercial license. Contact: license@tradiny.com
#
# For full details, see the LICENSE.md file in the root directory of this project.

# Import necessary modules from PyInstaller
from PyInstaller.utils.hooks import collect_submodules, collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT
from pathlib import Path

# Common data files and dependencies
common_binaries = []
common_datas = [
    ('private_key.pem', '.'),  # Extract to the current directory
    ('db.sqlite3', '.'),       # Extract to the current directory
    ('dist', 'dist'),
    ('indicators', 'indicators'),
    ('data_providers', 'data_providers'),
    ('notifications', 'notifications'),
]
hidden_imports = [
    'fastapi',
    'uvicorn',
    'websockets',
    'websocket',
    'fastapi_utils',
    'typing_inspect',
    'dotenv',
    'sqlalchemy',
    'pywebpush',
    'openai',
    'httpx',
    'binance',
    'polygon',
    'pyti',
    'pandas_ta',
    'provider'
]

# Separate Analysis blocks for each script
analysis_main = Analysis(
    ['main.py'],
    binaries=common_binaries,
    datas=common_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None
)

analysis_setup = Analysis(
    ['setup.py'],
    binaries=common_binaries,
    datas=common_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None
)

# Create separate PYZ blocks for each executable
pyz_main = PYZ(analysis_main.pure, analysis_main.zipped_data, cipher=None)
pyz_setup = PYZ(analysis_setup.pure, analysis_setup.zipped_data, cipher=None)

# EXE block for main.py
exe_main = EXE(
    pyz_main,
    analysis_main.scripts,
    [],
    exclude_binaries=True,
    name='tradiny',
    debug=True,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

# EXE block for setup.py
exe_setup = EXE(
    pyz_setup,
    analysis_setup.scripts,
    [],
    exclude_binaries=True,
    name='setup',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

# Single COLLECT block for both executables
coll = COLLECT(
    exe_main,
    exe_setup,
    analysis_main.binaries + analysis_setup.binaries,
    analysis_main.zipfiles + analysis_setup.zipfiles,
    analysis_main.datas + analysis_setup.datas,
    strip=False,
    upx=True,
    name='tradiny'
)
