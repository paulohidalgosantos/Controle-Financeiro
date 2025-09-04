# -*- mode: python ; coding: utf-8 -*-
import os
import sys
import glob
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.building.build_main import Analysis, PYZ, EXE

project_dir = os.path.abspath(".")
icon_path = os.path.join(project_dir, "icone.ico")

# DLLs essenciais
python_dir = os.path.dirname(sys.executable)
python_version = f"{sys.version_info.major}{sys.version_info.minor}"

dlls_to_include = []

# Python core DLLs
for dll_name in [f"python{python_version}.dll", "python3.dll"]:
    path = os.path.join(python_dir, dll_name)
    if os.path.exists(path):
        dlls_to_include.append((path, '.'))

# Runtime DLLs comuns do Visual C++
for dll_name in ["vcruntime140.dll", "vcruntime140_1.dll", "msvcp140.dll", "concrt140.dll"]:
    for dir_try in [python_dir, os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32')]:
        path_try = os.path.join(dir_try, dll_name)
        if os.path.exists(path_try):
            dlls_to_include.append((path_try, '.'))
            break

# DLLs e PYDs da pasta DLLs
dlls_dir = os.path.join(python_dir, 'DLLs')
if os.path.exists(dlls_dir):
    for dll_file in glob.glob(os.path.join(dlls_dir, '*.*')):
        if dll_file.endswith(('.dll', '.pyd')):
            dll_name = os.path.basename(dll_file)
            if dll_name.startswith(('python', '_')):
                dlls_to_include.append((dll_file, '.'))

# 🔑 Forçar a inclusão de módulos críticos (_socket, ssl, etc)
hidden_imports = [
    'tkinter', 'tkinter.ttk', 'tkinter.messagebox',
    'PIL.Image', 'PIL.ImageTk',
    'ttkbootstrap', 'ttkbootstrap.constants',
    '_socket', 'ssl', '_ssl', 'select'
]

# Arquivos extras
datas = [
    ('icone.png', '.'),
    ('updater.py', '.')
]

# --------- Analysis ----------
a = Analysis(
    ['Controle Financeiro.py'],  # seu script principal com espaço no nome
    pathex=[project_dir],
    binaries=dlls_to_include,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False
)

# --------- PYZ ----------
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# --------- EXE ----------
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
    upx_exclude=[dll[0] for dll in dlls_to_include],
    console=True,  # console ativo para debug; depois pode trocar para False
    icon=icon_path
)
