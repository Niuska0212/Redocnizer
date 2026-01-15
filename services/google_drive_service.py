# services/google_drive_service.py
"""
Servicio de sincronización con Google Drive.
Permite guardar/descargar contratos y datos en la nube.
Implementa: Módulo 3.3, 3.4, 3.5, 3.6
"""

import os
import json
import pickle
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict

# SCOPES de Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive.file']

class GoogleDriveService:
    """
    Servicio distribuido para sincronización con Google Drive.
    
    Cumple:
    - 3.3: Datos en nube (no local)
    - 3.4: HTTPS + OAuth 2.0
    - 3.5: Arquitectura cliente-servidor
    - 3.6: Sincronización de recursos entre dispositivos
    """
    
    def __init__(self, credentials_path: str = "credentials.json"):
        """
        Inicializa el servicio de Google Drive.
        
        Args:
            credentials_path: Ruta al archivo credentials.json
        """
        self.credentials_path = credentials_path
        self.token_path = "token.json"
        self.service = None
        self.app_folder_id = None
        self._authenticate()
    
    def _authenticate(self):
        """
        Autentica con Google usando OAuth 2.0.
        Primera vez: abre navegador para login
        Posteriores: usa token almacenado
        """
        creds = None
        
        # Si existe token.json, usarlo
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token_file:
                creds = pickle.load(token_file)
        
        # Si no hay credenciales válidas, solicitar login
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Iniciar flujo OAuth 2.0
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Guardar token para próximas veces
            with open(self.token_path, 'wb') as token_file:
                pickle.dump(creds, token_file)
        
        # Crear cliente de Google Drive API
        self.service = build('drive', 'v3', credentials=creds)
        print("✅ Autenticación con Google Drive exitosa")
    
    def _get_or_create_app_folder(self) -> str:
        """
        Obtiene o crea la carpeta 'OCR-Modular' en Google Drive.
        
        Returns:
            ID de la carpeta
        """
        if self.app_folder_id:
            return self.app_folder_id
        
        # Buscar si existe
        results = self.service.files().list(
            q="name='OCR-Modular' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            pageSize=1,
            fields='files(id)'
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            self.app_folder_id = files[0]['id']
            print(f"📁 Carpeta OCR-Modular encontrada: {self.app_folder_id}")
        else:
            # Crear nueva carpeta
            file_metadata = {
                'name': 'OCR-Modular',
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            self.app_folder_id = folder.get('id')
            print(f"📁 Carpeta OCR-Modular creada: {self.app_folder_id}")
        
        return self.app_folder_id
    
    def get_user_info(self) -> Dict:
        """
        Obtiene información del usuario autenticado.
        
        Returns:
            Dict con nombre y email del usuario
        """
        about = self.service.about().get(fields='user').execute()
        user = about.get('user', {})
        return {
            'nombre': user.get('displayName', 'Usuario'),
            'email': user.get('emailAddress', 'Sin email'),
            'foto': user.get('photoLink', None)
        }
    
    def upload_contract(self, local_path: str, remote_name: str = None) -> str:
        """
        Sube un contrato a Google Drive.
        
        Args:
            local_path: Ruta local del archivo
            remote_name: Nombre en la nube (opcional)
        
        Returns:
            ID del archivo en Drive
        """
        if not os.path.exists(local_path):
            raise FileNotFoundError(f"Archivo no encontrado: {local_path}")
        
        folder_id = self._get_or_create_app_folder()
        remote_name = remote_name or os.path.basename(local_path)
        
        file_metadata = {
            'name': remote_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(local_path, resumable=True)
        
        file = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, createdTime'
        ).execute()
        
        file_id = file.get('id')
        print(f"📤 Contrato subido: {remote_name} (ID: {file_id})")
        
        return file_id
    
    def upload_csv_data(self, df: pd.DataFrame, filename: str = "datos_contratos.csv") -> str:
        """
        Sube datos CSV a Google Drive.
        
        Args:
            df: DataFrame de pandas
            filename: Nombre del archivo CSV
        
        Returns:
            ID del archivo en Drive
        """
        # Guardar CSV temporalmente
        temp_path = f"temp_{filename}"
        df.to_csv(temp_path, index=False, encoding='utf-8')
        
        try:
            file_id = self.upload_contract(temp_path, filename)
            return file_id
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    def list_files(self, limit: int = 20) -> List[Dict]:
        """
        Lista archivos en la carpeta OCR-Modular.
        
        Args:
            limit: Número máximo de archivos a listar
        
        Returns:
            Lista de dicts con metadatos de archivos
        """
        folder_id = self._get_or_create_app_folder()
        
        results = self.service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            pageSize=limit,
            fields='files(id, name, mimeType, createdTime, modifiedTime, size)'
        ).execute()
        
        files = results.get('files', [])
        return files
    
    def download_file(self, file_id: str, local_path: str) -> bool:
        """
        Descarga un archivo de Google Drive.
        
        Args:
            file_id: ID del archivo en Drive
            local_path: Ruta local donde guardar
        
        Returns:
            True si tuvo éxito
        """
        request = self.service.files().get_media(fileId=file_id)
        
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Guardar en disco
        with open(local_path, 'wb') as f:
            f.write(fh.getvalue())
        
        print(f"📥 Archivo descargado: {local_path}")
        return True
    
    def download_csv_data(self, file_id: str) -> pd.DataFrame:
        """
        Descarga datos CSV desde Google Drive.
        
        Args:
            file_id: ID del archivo en Drive
        
        Returns:
            DataFrame de pandas
        """
        request = self.service.files().get_media(fileId=file_id)
        
        fh = BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Cargar como DataFrame
        fh.seek(0)
        df = pd.read_csv(fh, encoding='utf-8')
        
        print(f"📥 Datos descargados: {len(df)} registros")
        return df
    
    def sync_local_to_drive(self, local_dir: str) -> List[str]:
        """
        Sincroniza archivos locales a Google Drive.
        
        Args:
            local_dir: Directorio local con archivos
        
        Returns:
            Lista de IDs de archivos subidos
        """
        if not os.path.exists(local_dir):
            raise FileNotFoundError(f"Directorio no encontrado: {local_dir}")
        
        uploaded_ids = []
        
        for filename in os.listdir(local_dir):
            local_path = os.path.join(local_dir, filename)
            if os.path.isfile(local_path):
                try:
                    file_id = self.upload_contract(local_path)
                    uploaded_ids.append(file_id)
                except Exception as e:
                    print(f"❌ Error al subir {filename}: {e}")
        
        print(f"🔄 Sincronización completada: {len(uploaded_ids)} archivos subidos")
        return uploaded_ids
    
    def sync_drive_to_local(self, local_dir: str) -> int:
        """
        Sincroniza archivos de Google Drive a carpeta local.
        
        Args:
            local_dir: Directorio local donde guardar
        
        Returns:
            Número de archivos descargados
        """
        os.makedirs(local_dir, exist_ok=True)
        
        files = self.list_files(limit=100)
        
        downloaded_count = 0
        for file in files:
            # No descargar carpetas
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                continue
            
            local_path = os.path.join(local_dir, file['name'])
            
            # No sobrescribir si ya existe (comparar fecha)
            if os.path.exists(local_path):
                continue
            
            try:
                self.download_file(file['id'], local_path)
                downloaded_count += 1
            except Exception as e:
                print(f"❌ Error al descargar {file['name']}: {e}")
        
        print(f"🔄 Sincronización completada: {downloaded_count} archivos descargados")
        return downloaded_count
    
    def get_storage_info(self) -> Dict:
        """
        Obtiene información de almacenamiento en Google Drive.
        
        Returns:
            Dict con espacio usado y disponible
        """
        about = self.service.about().get(
            fields='storageQuota'
        ).execute()
        
        quota = about.get('storageQuota', {})
        
        used = int(quota.get('usedBytes', 0)) / (1024**3)  # Convertir a GB
        total = int(quota.get('quotaBytes', 0)) / (1024**3)
        
        return {
            'usado_gb': round(used, 2),
            'total_gb': round(total, 2),
            'disponible_gb': round(total - used, 2),
            'porcentaje_uso': round((used / total) * 100, 1) if total > 0 else 0
        }


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
