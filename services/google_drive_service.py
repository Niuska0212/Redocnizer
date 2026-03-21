# services/google_drive_service.py
"""
Servicio de respaldo en Google Drive (Módulo 3: Distribución).
Permite almacenar copias de seguridad de los contratos procesados en la nube.
"""
import os
import json
import logging
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from typing import Dict

# Configuración de Scopes para Google Drive
# Añadimos metadata.readonly para poder consultar cuotas de almacenamiento
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',
    'https://www.googleapis.com/auth/drive.metadata.readonly'
]

class GoogleDriveService:
    """Servicio simplificado para respaldo de contratos en la nube."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        self.token_path = 'token.json'
        self.client_secrets_path = 'credentials.json' # Archivo que descargas de Google Console
        self.authenticate()

    def authenticate(self):
        """Maneja el flujo de autenticación OAuth 2.0."""
        if os.path.exists(self.token_path):
            self.creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secrets_path):
                    raise FileNotFoundError("No se encontró credentials.json para Google Drive")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.client_secrets_path, SCOPES)
                self.creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('drive', 'v3', credentials=self.creds)

    def upload_file(self, file_path: str, folder_id: str | None = None) -> str:
        """Sube un archivo a Google Drive."""
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id'
        ).execute()
        return file.get('id')

    # helpers para gestión más avanzada ------------------------------------------------
    def _find_file(self, name: str, folder_id: str | None = None) -> dict | None:
        """Busca un fichero por nombre (y opcionalmente por carpeta) y devuelve su metadata.

        Retorna el primer archivo que coincida (no se manejan duplicados entre carpetas).
        """
        query = f"name = '{name}' and trashed = false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        try:
            response = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id,name)'
            ).execute()
            files = response.get('files', [])
            if files:
                return files[0]
        except Exception:
            pass
        return None

    def _ensure_folder(self, name: str, parent_id: str | None = None) -> str | None:
        """Busca o crea una carpeta con el nombre dado y devuelve su id.

        Si `parent_id` es None, busca/crea en la raíz del Drive.
        """
        try:
            if parent_id:
                q = f"mimeType = 'application/vnd.google-apps.folder' and name = '{name}' and '{parent_id}' in parents and trashed = false"
            else:
                q = f"mimeType = 'application/vnd.google-apps.folder' and name = '{name}' and 'root' in parents and trashed = false"

            resp = self.service.files().list(q=q, spaces='drive', fields='files(id,name)').execute()
            files = resp.get('files', [])
            if files:
                return files[0]['id']

            # No existe -> crear
            metadata = {
                'name': name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                metadata['parents'] = [parent_id]
            else:
                metadata['parents'] = ['root']

            folder = self.service.files().create(body=metadata, fields='id').execute()
            return folder.get('id')
        except Exception:
            return None

    def upload_or_replace(self, file_path: str, folder_id: str | None = None, drive_root: str | None = 'Redocnizer', subfolder: str | None = None) -> str:
        """Sube un archivo; si ya existe un fichero con el mismo nombre lo reemplaza.

        La API de Drive no tiene 'overwrite' directo, por eso primero buscamos el id y
        usamos `update()` si lo encontramos.
        """
        # Si se especifica un root/carpeta lógica, resolver a folder_id real
        target_folder = folder_id
        if drive_root:
            root_id = self._ensure_folder(drive_root, parent_id=None)
            if root_id:
                if subfolder:
                    sub_id = self._ensure_folder(subfolder, parent_id=root_id)
                    target_folder = sub_id
                else:
                    target_folder = root_id

        basename = os.path.basename(file_path)
        existing = self._find_file(basename, target_folder)
        media = MediaFileUpload(file_path, resumable=True)
        if existing:
            updated = self.service.files().update(
                fileId=existing['id'],
                media_body=media
            ).execute()
            return updated.get('id')
        else:
            return self.upload_file(file_path, target_folder)

    def upload_if_not_exists(self, file_path: str, folder_id: str | None = None, drive_root: str | None = 'Redocnizer', subfolder: str | None = None) -> str | None:
        """Sube un archivo únicamente si no existe otro con el mismo nombre.

        Devuelve el id del archivo en Drive (nuevo o ya existente)."""
        target_folder = folder_id
        if drive_root:
            root_id = self._ensure_folder(drive_root, parent_id=None)
            if root_id:
                if subfolder:
                    sub_id = self._ensure_folder(subfolder, parent_id=root_id)
                    target_folder = sub_id
                else:
                    target_folder = root_id

        basename = os.path.basename(file_path)
        existing = self._find_file(basename, target_folder)
        if existing:
            return existing['id']
        return self.upload_file(file_path, target_folder)

    def upload_folder(self, local_folder: str, drive_root: str = 'Redocnizer', subfolder: str | None = None) -> Dict:
        """Sube una carpeta local completa recursivamente a Drive bajo `drive_root/subfolder`.

        Comportamiento Actualizado:
        - Si el archivo es un CSV (ej. 2024A.csv), usa `upload_or_replace` para no duplicar la base de datos.
        - Para otros archivos (PDFs, imágenes), usa `upload_if_not_exists`.
        """
        summary = {'uploaded': 0, 'skipped': 0, 'errors': 0}
        if not os.path.exists(local_folder) or not os.path.isdir(local_folder):
            return summary

        # Resolver carpeta objetivo en Drive
        root_id = None
        if drive_root:
            root_id = self._ensure_folder(drive_root, parent_id=None)
        
        target_parent = root_id
        if root_id and subfolder:
            target_parent = self._ensure_folder(subfolder, parent_id=root_id)

        def _recurse(local_dir: str, parent_drive_id: str | None):
            try:
                if parent_drive_id is None and drive_root:
                    parent_drive_id = self._ensure_folder(drive_root, parent_id=None)

                for entry in os.listdir(local_dir):
                    path = os.path.join(local_dir, entry)
                    if os.path.isdir(path):
                        # Crear subcarpeta en Drive
                        child_id = None
                        if parent_drive_id:
                            child_id = self._ensure_folder(entry, parent_id=parent_drive_id)
                        _recurse(path, child_id)
                    else:
                        # --- CAMBIO AQUÍ ---
                        # Antes buscaba 'contratos.csv'. 
                        # Ahora: si termina en .csv, asumimos que es una base de datos de calendario
                        try:
                            if entry.lower().endswith('.csv'):
                                # Usamos el método que reemplaza si ya existe
                                self.upload_or_replace(path, folder_id=parent_drive_id, drive_root=None)
                                summary['uploaded'] += 1
                            else:
                                # Para el resto (PDFs, etc), solo subir si no existe
                                fid = self.upload_if_not_exists(path, folder_id=parent_drive_id, drive_root=None)
                                if fid:
                                    summary['uploaded'] += 1
                                else:
                                    summary['skipped'] += 1
                        except Exception as e:
                            print(f"Error subiendo archivo {entry}: {e}")
                            summary['errors'] += 1
            except Exception as e:
                print(f"Error en recursión: {e}")
                summary['errors'] += 1

        # Lógica para determinar la carpeta base en Drive
        base_name = os.path.basename(os.path.normpath(local_folder))
        base_drive_id = None
        try:
            if target_parent:
                base_drive_id = self._ensure_folder(base_name, parent_id=target_parent)
            else:
                if drive_root:
                    root_id = self._ensure_folder(drive_root, parent_id=None)
                    base_drive_id = self._ensure_folder(base_name, parent_id=root_id)
                else:
                    base_drive_id = self._ensure_folder(base_name, parent_id=None)
        except Exception:
            base_drive_id = target_parent

        _recurse(local_folder, base_drive_id)
        summary['base_drive_id'] = base_drive_id
        return summary

    def get_user_info(self) -> Dict:
        """Obtiene información básica del perfil conectado."""
        try:
            about = self.service.about().get(fields="user").execute()
            user = about.get('user', {})
            return {
                'nombre': user.get('displayName', 'Usuario'),
                'email': user.get('emailAddress', 'N/A'),
                'foto': user.get('photoLink', '')
            }
        except Exception:
            return {'nombre': 'Desconectado', 'email': '', 'foto': ''}

    def get_storage_info(self) -> Dict:
        """Retorna el estado del almacenamiento en GB para el reporte de distribución."""
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            used = int(quota.get('usedBytes', 0)) / (1024**3)
            total = int(quota.get('quotaBytes', 0)) / (1024**3)
            return {
                'usado_gb': round(used, 2),
                'total_gb': round(total, 2),
                'porcentaje': round((used / total) * 100, 1) if total > 0 else 0
            }
        except Exception:
            return {'usado_gb': 0, 'total_gb': 0, 'porcentaje': 0}

    def upload_to_path(self, file_path: str, drive_root: str = 'REDOCNIZER', calendar: str = '', subfolder_path: str = '') -> str | None:
        """
        Sube el archivo directamente a la carpeta principal de REDOCNIZER 
        renombrándolo como <calendario>.csv.
        """
        try:
            subfolder_path = subfolder_path.replace("\\","/")

            if calendar and calendar in subfolder_path:
                subfolder_path = subfolder_path.split(calendar)[0].strip("/")

            # 1. Obtener el ID de la carpeta principal 'REDOCNIZER' (sin crear carpetas de calendario)
            root_id = self._ensure_folder(drive_root, parent_id=None)
            if not root_id:
                return None

            parent_id = root_id

            # 2. Si hay subfolder, crearlo
            if subfolder_path:
                partes = subfolder_path.split("/")

                for carpeta in partes:
                    if carpeta.strip():
                        parent_id = self._ensure_folder(carpeta.strip(), parent_id=parent_id)

            # 3. Nombre Final 
            nombre_local = os.path.basename(file_path)

            if nombre_local.lower().endswith('.csv') and calendar:
                nombre_en_drive = f"{calendar}.csv"
            else:
                nombre_en_drive = nombre_local

            # 4. Evitar duplicados: Buscar si ya existe un archivo con ESE nombre en Drive
            existing_file = self._find_file(nombre_en_drive, parent_id)
            
            media = MediaFileUpload(file_path, resumable=True)

            if existing_file:
                # Si existe, actualizamos su contenido (reemplazar)
                self.service.files().update(
                    fileId=existing_file['id'],
                    media_body=media
                ).execute()
                print(f"🔄 Archivo actualizado en Drive: {nombre_en_drive}")
                return existing_file['id']
            else:
                # Si no existe, lo creamos de cero con el nombre del calendario
                file_metadata = {
                    'name': nombre_en_drive,
                    'parents': [parent_id]
                }
                file = self.service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id'
                ).execute()
                print(f"📤 Archivo creado en Drive: {nombre_en_drive}")
                return file.get('id')

        except Exception as e:
            logging.error(f"Error crítico en upload_to_path: {e}")
            return None