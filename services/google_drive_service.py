# services/google_drive_service.py
"""
Servicio de sincronización con Google Drive mejorado para producción.
Implementa seguridad OAuth 2.0, logs rotativos y validación de integridad de datos.
"""
import os
import json
import logging
import re
from logging.handlers import RotatingFileHandler
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO
import pandas as pd
from typing import List, Optional, Dict

# =========================================================
# CONFIGURACIÓN DE LOGS (PASO 2)
# =========================================================
def setup_logging():
    """Configura logs para consola y archivo con rotación automática."""
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "drive_service.log")
    
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # El archivo se crea automáticamente si no existe dentro de la carpeta logs
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
    )
    file_handler.setFormatter(log_format)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    logger = logging.getLogger("GoogleDriveService")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# SCOPES: drive.file permite acceso solo a archivos creados por esta app
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Args:
            credentials_path: Ruta al archivo credentials.json de Google Cloud.
        """
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = credentials_path
        self.token_path = "token.json" 
        
        self.service = None
        self.app_folder_id = None
        self._authenticate()
    
    def _authenticate(self):
        """Autentica y gestiona tokens de acceso en formato JSON."""
        creds = None
        if os.path.exists(self.token_path):
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
            except Exception as e:
                logger.error(f"Error al cargar token: {e}")
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refrescando token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    logger.critical("Archivo credentials.json no encontrado.")
                    raise FileNotFoundError("credentials.json es requerido.")
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(self.token_path, 'w') as token_file:
                token_file.write(creds.to_json())
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Autenticación exitosa.")

    def _get_or_create_app_folder(self) -> str:
        """Obtiene el ID de la carpeta principal en Drive."""
        if self.app_folder_id:
            return self.app_folder_id
        
        try:
            query = "name='OCR-Modular' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            results = self.service.files().list(q=query, spaces='drive', pageSize=1).execute()
            files = results.get('files', [])
            
            if files:
                self.app_folder_id = files[0]['id']
            else:
                metadata = {'name': 'OCR-Modular', 'mimeType': 'application/vnd.google-apps.folder'}
                folder = self.service.files().create(body=metadata, fields='id').execute()
                self.app_folder_id = folder.get('id')
            
            return self.app_folder_id
        except Exception as e:
            logger.error(f"Error gestionando carpeta: {e}")
            raise

    # =========================================================
    # VALIDACIÓN Y LIMPIEZA DE DATOS (PASO 3)
    # =========================================================
    def _sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Limpia y estandariza los datos antes de la sincronización.
        """
        if df.empty:
            return df
        
        logger.info(f"Iniciando saneamiento de {len(df)} registros...")
        
        # 1. Copia para no alterar el original durante el proceso
        clean_df = df.copy()

        # 2. Limpiar espacios en blanco en strings y normalizar vacíos
        for col in clean_df.columns:
            if clean_df[col].dtype == 'object':
                # Limpiamos espacios y evitamos que los nulos rompan el script
                clean_df[col] = clean_df[col].apply(lambda x: str(x).strip() if pd.notnull(x) else "N/A")
                # Eliminar saltos de línea internos que rompen la estructura del CSV
                clean_df[col] = clean_df[col].replace(r'[\r\n]+', ' ', regex=True)

        # 3. Intentar estandarizar fechas si existen columnas probables (ej: "Fecha Inicio")
        date_cols = [c for c in clean_df.columns if 'fecha' in c.lower()]
        for col in date_cols:
            try:
                # dayfirst=True es vital para formatos latinos (DD/MM/YYYY)
                temp_dates = pd.to_datetime(clean_df[col], errors='coerce', dayfirst=True)
                mask = temp_dates.notnull()
                clean_df.loc[mask, col] = temp_dates[mask].dt.strftime('%d/%m/%Y')
                logger.debug(f"Columna de fecha '{col}' estandarizada correctamente.")
            except Exception as e:
                logger.warning(f"No se pudo estandarizar la columna de fecha {col}: {e}")

        logger.info("✅ Saneamiento de datos completado.")
        return clean_df

    def get_user_info(self) -> Dict:
        """Info del usuario autenticado."""
        try:
            about = self.service.about().get(fields='user').execute()
            user = about.get('user', {})
            return {
                'nombre': user.get('displayName', 'Usuario'),
                'email': user.get('emailAddress', 'Sin email'),
                'foto': user.get('photoLink', None)
            }
        except Exception as e:
            logger.error(f"Error obteniendo info usuario: {e}")
            return {'nombre': 'Error', 'email': 'Desconectado', 'foto': None}

    def upload_contract(self, local_path: str, remote_name: str = None) -> str:
        """Sube un archivo individual (PDF, Imagen, etc)."""
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Local path no existe: {local_path}")
        
        try:
            folder_id = self._get_or_create_app_folder()
            remote_name = remote_name or os.path.basename(local_path)
            
            metadata = {'name': remote_name, 'parents': [folder_id]}
            media = MediaFileUpload(local_path, resumable=True)
            file = self.service.files().create(body=metadata, media_body=media, fields='id').execute()
            
            logger.info(f"📤 Archivo subido: {remote_name}")
            return file.get('id')
        except Exception as e:
            logger.error(f"Fallo al subir {local_path}: {e}")
            raise

    def upload_csv_data(self, df: pd.DataFrame, filename: str = "datos_contratos.csv") -> str:
        """Sanitiza los datos y los sube a Drive como CSV."""
        import tempfile
        
        # Aplicar limpieza antes de generar el archivo para subir
        sanitized_df = self._sanitize_dataframe(df)
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            # utf-8-sig permite que Excel reconozca tildes al abrir el archivo
            sanitized_df.to_csv(tmp.name, index=False, encoding='utf-8-sig')
            temp_path = tmp.name
        
        try:
            file_id = self.upload_contract(temp_path, filename)
            return file_id
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def list_files(self, limit: int = 50) -> List[Dict]:
        """Lista archivos en la carpeta de la app."""
        try:
            folder_id = self._get_or_create_app_folder()
            q = f"'{folder_id}' in parents and trashed=false"
            results = self.service.files().list(q=q, fields='files(id, name, mimeType, createdTime, size)').execute()
            return results.get('files', [])
        except Exception as e:
            logger.error(f"Error listando Drive: {e}")
            return []

    def download_file(self, file_id: str, local_path: str) -> bool:
        """Descarga un archivo binario."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            with open(local_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"📥 Descargado: {local_path}")
            return True
        except Exception as e:
            logger.error(f"Error descargando {file_id}: {e}")
            return False

    def download_csv_data(self, file_id: str) -> Optional[pd.DataFrame]:
        """Descarga CSV y lo retorna como DataFrame."""
        try:
            request = self.service.files().get_media(fileId=file_id)
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while not done:
                _, done = downloader.next_chunk()
            
            fh.seek(0)
            df = pd.read_csv(fh, encoding='utf-8')
            return df
        except Exception as e:
            logger.error(f"Error procesando CSV de Drive: {e}")
            return None

    def sync_local_to_drive(self, local_dir: str) -> List[str]:
        """Sincroniza masivamente local -> nube."""
        if not os.path.exists(local_dir):
            return []
        
        ids = []
        for f in os.listdir(local_dir):
            p = os.path.join(local_dir, f)
            if os.path.isfile(p):
                try:
                    ids.append(self.upload_contract(p))
                except:
                    continue
        logger.info(f"🔄 Sync Local a Drive terminada. Total: {len(ids)}")
        return ids

    def sync_drive_to_local(self, local_dir: str) -> int:
        """Sincroniza masivamente nube -> local."""
        try:
            os.makedirs(local_dir, exist_ok=True)
            files = self.list_files()
            count = 0
            for f in files:
                if f['mimeType'] == 'application/vnd.google-apps.folder': continue
                target = os.path.join(local_dir, f['name'])
                if os.path.exists(target): continue
                if self.download_file(f['id'], target): count += 1
            logger.info(f"🔄 Sync Drive a Local terminada. Total: {count}")
            return count
        except Exception as e:
            logger.error(f"Error en sync: {e}")
            return 0

    def get_storage_info(self) -> Dict:
        """Retorna estado de la cuota en GB."""
        try:
            about = self.service.about().get(fields='storageQuota').execute()
            quota = about.get('storageQuota', {})
            used = int(quota.get('usedBytes', 0)) / (1024**3)
            total = int(quota.get('quotaBytes', 0)) / (1024**3)
            return {
                'usado_gb': round(used, 2),
                'total_gb': round(total, 2),
                'porcentaje_uso': round((used / total) * 100, 1) if total > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error cuota: {e}")
            return {'usado_gb': 0, 'total_gb': 0, 'porcentaje_uso': 0}


# Ejemplo de uso
if __name__ == "__main__":
    try:
        drive = GoogleDriveService()
        
        # Obtener información del usuario
        user_info = drive.get_user_info()
        print(f"👤 Usuario: {user_info['nombre']} ({user_info['email']})")
        
        # Obtener información de almacenamiento
        storage = drive.get_storage_info()
        print(f"💾 Almacenamiento: {storage['usado_gb']}GB / {storage['total_gb']}GB ({storage['porcentaje_uso']}%)")
        
        # Listar archivos
        print("\n📁 Archivos en OCR-Modular:")
        files = drive.list_files(limit=10)
        for file in files:
            print(f"  - {file['name']} ({file['id']})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
