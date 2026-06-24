# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

root = SPECPATH

# 1. Recopilar archivos de datos
pyside6_datas = collect_data_files('PySide6')
easyocr_datas = collect_data_files('easyocr')

datas = [
    (os.path.join(root, 'ui', 'assets'), 'ui/assets'),
    (os.path.join(root, 'models'), 'models'),
] + pyside6_datas + easyocr_datas

# Archivos de raíz
for extra_file in ['README.md', 'LICENSE', 'calendarios.db', 'credentials.json', 'credentials_supa.env']:
    file_path = os.path.join(root, extra_file)
    if os.path.exists(file_path):
        datas.append((file_path, '.'))

if os.path.exists(os.path.join(root, 'docs')):
    datas.append((os.path.join(root, 'docs'), 'docs'))

block_cipher = None

# Lista de exclusiones que NO rompen el programa
excluir = ['tensorflow', 'tensorboard', 'keras', 'matplotlib', 'tkinter', 'h5py']

a = Analysis(
    [os.path.join(root, 'app.py')],
    pathex=[root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'dotenv',
        'PySide6',
        'cv2',
        'easyocr',
        'torch',
        'torchvision',
        'pdf2image',
        'PIL.ImageResampling',
        'core.document_extractor',
        'core.segmentacion_dinamica',
        'core.preprocessing',
        'services.ocr_service',
        'services.pdf_service',
        'ui.main_window',
        'ui.splash_screen',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=excluir,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Limpieza manual de archivos de TensorFlow/Keras que se logren filtrar
a.binaries = [x for x in a.binaries if not any(bad in x[0].lower() for bad in excluir)]

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='REDOCNIZER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False, # Desactivado para evitar bloqueos al iniciar
    console=False,
    icon=os.path.join(root, 'ui', 'assets', 'logo_redocnizer.ico'),
)

# ==========================================
# COMPILACIÓN 2: MGRADOR DE CARPETAS (Script Auxiliar)
# ==========================================
a_migrador = Analysis(
    [os.path.join(root, 'migrate_nombramientos.py')], # <--- Tu nuevo script de UI
    pathex=[root],
    binaries=[],
    datas=pyside6_datas, # Solo necesita las dependencias visuales de PySide6
    hiddenimports=['PySide6'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=excluir + ['torch', 'torchvision', 'easyocr', 'cv2'], # Excluimos la IA para que sea ligero
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

a_migrador.binaries = [x for x in a_migrador.binaries if not any(bad in x[0].lower() for bad in excluir)]
pyz_migrador = PYZ(a_migrador.pure, a_migrador.zipped_data, cipher=block_cipher)

exe_migrador = EXE(
    pyz_migrador,
    a_migrador.scripts,
    [],
    exclude_binaries=True,
    name='MigradorCarpetas', # <--- Nombre del segundo ejecutable
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=False,
    icon=os.path.join(root, 'ui', 'assets', 'logo_redocnizer.ico'), # Puedes usar el mismo icono
)

# ==========================================
# RECOLECCIÓN FINAL (Une ambos en la misma carpeta)
# ==========================================
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    exe_migrador,             # <--- Añadimos el ejecutable del migrador
    a_migrador.binaries,      # <--- Añadimos sus binarios nativos
    a_migrador.zipfiles,
    a_migrador.datas,
    strip=False,
    upx=False,
    name='REDOCNIZER_V2.3.3'
)