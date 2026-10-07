# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for RadeonVideoAI (Reescalar-only build).
Target: Windows 10/11 64-bit with any DirectX 12 GPU (NVIDIA/AMD/Intel, via
ONNX Runtime DirectML) and any CPU. Bundles PyQt6, PyTorch (CPU, used only
to load/export AI weights), ONNX Runtime DirectML, and standalone FFmpeg
binaries.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules, collect_dynamic_libs

block_cipher = None
PROJECT_DIR = os.path.abspath(SPECPATH)

# 1. Collect PyTorch data and DLL dependencies
#
# Deliberately NOT bundling models/ (models/weights/*): every AI checkpoint
# under there is downloaded on first use at runtime, not meant to ship in
# the portable build.
datas = [
    (os.path.join(PROJECT_DIR, "core"), "core"),
    (os.path.join(PROJECT_DIR, "gui"), "gui"),
]
datas += collect_data_files('torch')
datas += collect_data_files('onnxruntime')

# 2. Binaries: Include local ffmpeg and ffprobe if present
binaries = []
for binary_name in ["ffmpeg.exe", "ffprobe.exe"]:
    bin_path = os.path.join(PROJECT_DIR, binary_name)
    if os.path.isfile(bin_path):
        binaries.append((bin_path, "."))

binaries += collect_dynamic_libs('torch')
binaries += collect_dynamic_libs('onnxruntime')

# 3. Hidden imports to prevent runtime missing module errors
hiddenimports = [
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'torch',
    'torch.nn',
    'torch.nn.functional',
    'onnx',
    'onnxruntime',
    'requests',
    'psutil',
    'numpy',
    'json',
    'platform',
    'ctypes',
    'subprocess',
]
hiddenimports += collect_submodules('torch')
hiddenimports += collect_submodules('onnxruntime')

a = Analysis(
    ['main.py'],
    pathex=[PROJECT_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'scapy', 'IPython', 'notebook'],
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
    name='RadeonVideoAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Desktop GUI app
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='RadeonVideoAI',
)
