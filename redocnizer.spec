# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Rutas base
root = SPECPATH

# 1. Recopilar archivos de datos de las dependencias pesadas
tensorflow_datas = collect_data_files('tensorflow')
keras_datas = collect_data_files('keras')
pyside6_datas = collect_data_files('PySide6')

# 2. Definir archivos de datos locales a incluir
datas = [
    (os.path.join(root, 'ui', 'assets'), 'ui/assets'),
] + tensorflow_datas + keras_datas + pyside6_datas

# --- NUEVOS ARCHIVOS DE DOCUMENTACIÓN Y RAÍZ ---

# Agregar README y LICENSE si existen en la raíz
for extra_file in ['README.md', 'LICENSE', 'README.txt']:
    file_path = os.path.join(root, extra_file)
    if os.path.exists(file_path):
        datas.append((file_path, '.')) # El '.' significa que se copia a la raíz del EXE

# Agregar carpeta de documentación completa (docs/)
docs_path = os.path.join(root, 'docs')
if os.path.exists(docs_path):
    # (Ruta_Origen, Nombre_Carpeta_Destino)
    datas.append((docs_path, 'docs'))

# --- ARCHIVOS DE CONFIGURACIÓN Y BASES DE DATOS ---

if os.path.exists(os.path.join(root, 'calendarios.db')):
    datas.append((os.path.join(root, 'calendarios.db'), '.'))

if os.path.exists(os.path.join(root, 'credentials.json')):
    datas.append((os.path.join(root, 'credentials.json'), '.'))

if os.path.exists(os.path.join(root, 'firebase_credentials.json')):
    datas.append((os.path.join(root, 'firebase_credentials.json'), '.'))

block_cipher = None

a = Analysis(
    [os.path.join(root, 'app.py')],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[
        'PySide6',
        'tensorflow',
        'keras',
        'cv2',
        'easyocr',
        'pdf2image',
        'google.auth',
        'google.oauth2',
        'firebase_admin',
        'googleapiclient.discovery',
        'googleapiclient.http',
        'google_auth_oauthlib.flow',
        'controllers.contract_controller',
        'core.document_extractor',
        'core.CRNN_inference',
        'services.ocr_service',
        'services.pdf_service',
        'services.firebase_service',
        'services.google_drive_service',
        'ui.main_window',
        'ui.app_menu',
        'ui.data_tab',
        'ui.data_manager',
        'ui.calendar_db',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=['matplotlib', 'scipy', 'numpy.random._utils'],
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
    strip=False,
    upx=True,
    console=False, 
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(root, 'ui', 'assets', 'logo_redocnizer.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='REDOCNIZER_DIST'
)