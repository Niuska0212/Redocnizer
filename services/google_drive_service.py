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
from typing import Optional, Dict

# Configuración de Scopes para Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']

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

    def upload_file(self, file_path: str, folder_id: Optional[str] = None) -> str:
        """Sube un archivo a Google Drive."""
        file_metadata = {'name': os.path.basename(file_path)}
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        media = MediaFileUpload(file_path, resumable=True)
        file = self.service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')

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