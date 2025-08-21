# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob

project_dir = os.path.abspath(".")
icon_path = os.path.join(project_dir, "icone.ico")

# Detecta diretório do Python
python_dir = os.path.dirname(sys.executable)
python_version = f"{sys.version_info.major}{sys.version_info.minor}"

# Coleta DLLs essenciais manualmente
dlls_to_include = []

# DLLs principais do Python
for dll_name in [f"python{python_version}.dll", "python3.dll"]:
    path = os.path.join(python_dir, dll_name)
    if os.path.exists(path):
        dlls_to_include.append((path, '.'))

# DLLs do VC++
for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "concrt140.dll"]:
    for dir_try in [python_dir, os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32')]:
        path_try = os.path.join(dir_try, dll_name)
        if os.path.exists(path_try):
            dlls_to_include.append((path_try, '.'))
            break

# DLLs adicionais do diretório DLLs do Python
dlls_dir = os.path.join(python_dir, 'DLLs')
if os.path.exists(dlls_dir):
    for dll_file in glob.glob(os.path.join(dlls_dir, '*.dll')):
        dll_name = os.path.basename(dll_file)
        if dll_name.startswith(('python', '_')):
            dlls_to_include.append((dll_file, '.'))

a = Analysis(
    ['Controle Financeiro.pyw'],
    pathex=[project_dir],
    binaries=dlls_to_include,
    datas=[('icone.png', '.'), ('updater.pyw', '.')],
    hiddenimports=[
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
        'PIL.Image', 'PIL.ImageTk', 'ttkbootstrap', 'ttkbootstrap.constants'
    ],
    hookspath=[],
    hooksconfig={},
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
    upx=True,
    upx_exclude=[dll[0] for dll in dlls_to_include],  # impede UPX de compactar DLLs essenciais
    console=False,
    icon=icon_path,
)
