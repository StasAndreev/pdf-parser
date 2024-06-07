# main.spec
from PyInstaller.building.api import PYZ, EXE, COLLECT
from PyInstaller.building.build_main import Analysis
# Importing necessary modules from PyInstaller
from PyInstaller.utils.hooks import collect_data_files
import os

# Define the output directory relative to the spec file
output_dir = os.path.join(os.path.dirname(__file__), 'output')

# Collect data files to be included
"""
data_files = [
    ('path/to/data/file1.ext', 'destination/folder/'),
    ('path/to/data/file2.ext', 'destination/folder/'),
    ('path/to/data/file3.ext', 'destination/folder/'),
]
"""

# PyInstaller analysis configuration
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # datas=data_files,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
)

# PyInstaller PYZ configuration
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=None,
)

# PyInstaller EXE configuration
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='main',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    icon=None,
)

# Collect additional files to be added to the final directory
additional_files = [
    ('path/to/extra/file1.ext', '.'),
    ('path/to/extra/file2.ext', '.'),
    ('path/to/extra/file3.ext', '.'),
]

# PyInstaller COLLECT configuration
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    additional_files,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='main',
)