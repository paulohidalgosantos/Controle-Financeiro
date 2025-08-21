# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob
from PyInstaller.utils.hooks import collect_submodules

project_dir = os.path.abspath(".")
icon_path = os.path.join(project_dir, "icone.ico")

# Diretório do Python
python_dir = os.path.dirname(sys.executable)
python_version = f"{sys.version_info.major}{sys.version_info.minor}"

# DLLs essenciais
dlls_to_include = []

# DLLs principais do Python
for dll_name in [f"python{python_version}.dll", "python3.dll"]:
    dll_path = os.path.join(python_dir, dll_name)
    if os.path.exists(dll_path):
        dlls_to_include.append((dll_path, '.'))

# DLLs do VC++
for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "concrt140.dll"]:
    for dir_try in [python_dir, os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32')]:
        path_try = os.path.join(dir_try, dll_name)
        if os.path.exists(path_try):
            dlls_to_include.append((path_try, '.'))
            break

# DLLs adicionais da pasta DLLs do Python
dlls_dir = os.path.join(python_dir, 'DLLs')
if os.path.exists(dlls_dir):
    for dll_file in glob.glob(os.path.join(dlls_dir, '*.dll')):
        dll_name = os.path.basename(dll_file)
        if dll_name.startswith(('python', '_')):
            dlls_to_include.append((dll_file, '.'))

# Hidden imports do Tkinter, PIL e ttkbootstrap
hidden_imports = collect_submodules('tkinter') + [
    'tkinter.messagebox',
    'PIL.Image', 'PIL.ImageTk',
    'ttkbootstrap', 'ttkbootstrap.constants'
]

a = Analysis(
    ['Controle Financeiro.pyw'],
    pathex=[project_dir],
    binaries=dlls_to_include,
    datas=[('icone.png', '.'), ('updater.pyw', '.')],
    hiddenimports=hidden_imports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Controle Financeiro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # ⚠️ Desativado para evitar erro de DLL
    console=False,
    icon=icon_path,
)
