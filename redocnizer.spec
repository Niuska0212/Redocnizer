# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Rutas base
root = SPECPATH

# 1. Recopilar archivos de datos de PySide6 y EasyOCR
# EasyOCR a veces necesita sus archivos de configuración internos
pyside6_datas = collect_data_files('PySide6')
easyocr_datas = collect_data_files('easyocr')

# 2. Definir archivos de datos locales
datas = [
    (os.path.join(root, 'ui', 'assets'), 'ui/assets'),
    (os.path.join(root, 'models'), 'models'), # Carpeta con los .pth de EasyOCR
] + pyside6_datas + easyocr_datas

# --- ARCHIVOS DE RAÍZ Y CONFIGURACIÓN ---
for extra_file in ['README.md', 'LICENSE', 'calendarios.db', 'credentials.json', 'credentials_supa.env']:
    file_path = os.path.join(root, extra_file)
    if os.path.exists(file_path):
        datas.append((file_path, '.'))

# Agregar carpeta de documentación
if os.path.exists(os.path.join(root, 'docs')):
    datas.append((os.path.join(root, 'docs'), 'docs'))

block_cipher = None

a = Analysis(
    [os.path.join(root, 'app.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'dotenv',
        #'supabase',  # DESHABILITADO: Versión sin nube
        #'postgrest',
        #'gotrue',
        'PySide6',
        'cv2',
        'easyocr',
        'torch',          # REQUERIDO: EasyOCR depende de torch
        'torchvision',    # REQUERIDO: EasyOCR depende de torchvision
        'pdf2image',
        'PIL.ImageResampling', # A veces Pillow pierde este import en el EXE
        #'google.auth',  # DESHABILITADO: Versión sin nube
        #'google.oauth2',  # DESHABILITADO: Versión sin nube
        #'firebase_admin',  # DESHABILITADO: Versión sin nube
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
    # EXCLUIMOS TENSORFLOW y otras librerías pesadas que ya no usas
    excludedimports=['tensorflow', 'tensorboard', 'keras', 'matplotlib', 'scipy', 'tkinter'],
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
    name='REDOCNIZER',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,     # Activamos strip para reducir tamaño
    upx=True,       # Comprime el EXE final
    console=False, 
    icon=os.path.join(root, 'ui', 'assets', 'logo_redocnizer.ico'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='REDOCNIZER_V2.2.2'
)