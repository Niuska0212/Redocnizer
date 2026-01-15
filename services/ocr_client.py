"""
ocr_client.py - Cliente distribuido que se conecta al API REST

Cumple criterio 3.5: Cliente-servidor distribuido
Cumple criterio 3.6: Sincronización con servidor remoto
"""

import requests
import base64
import json
from typing import Dict, Optional
from datetime import datetime
import io
from PIL import Image
import numpy as np

class OCRClient:
    """Cliente para conectarse al API REST distribuido"""
    
    def __init__(self, server_url: str = "http://localhost:5000"):
        """
        Inicializa el cliente
        
        Args:
            server_url: URL del servidor distribuido (puede ser IP remota)
        """
        self.server_url = server_url
        self.timeout = 30  # segundos
        
        # Verificar conexión
        if not self.check_connection():
            print(f"⚠️  Servidor no disponible en {server_url}")
            print("Asegúrate de que api_server.py está corriendo")
    
    def check_connection(self) -> bool:
        """Verifica si el servidor está disponible"""
        try:
            response = requests.get(
                f"{self.server_url}/api/health",
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    def process_contract_from_image(
        self,
        image_path: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Envía una imagen al servidor para procesamiento OCR
        
        Args:
            image_path: Ruta a la imagen del contrato
            metadata: Datos adicionales (departamento, año, etc)
        
        Returns:
            Respuesta del servidor con datos extraídos
        
        Ejemplo:
            client = OCRClient()
            result = client.process_contract_from_image(
                "contrato.jpg",
                metadata={"departamento": "RH", "ano": 2024}
            )
            print(result['data'])  # Datos extraídos
        """
        try:
            # Leer y codificar imagen en base64
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # Preparar request
            payload = {
                'image_base64': image_base64,
                'file_name': image_path.split('\\')[-1],  # Nombre del archivo
                'metadata': metadata or {}
            }
            
            # Enviar al servidor
            print(f"📤 Enviando imagen al servidor {self.server_url}...")
            response = requests.post(
                f"{self.server_url}/api/process-contract",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Procesado en {result['processing_time_ms']}ms")
                print(f"💾 Almacenado en BD distribuida: {result['document_id']}")
                return result
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                return {'success': False, 'error': response.text}
        
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': f'No se pudo conectar a {self.server_url}'
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_all_contracts(self) -> Dict:
        """
        Obtiene todos los contratos procesados desde la BD distribuida
        
        Returns:
            Lista de contratos almacenados en el servidor
        """
        try:
            print("📥 Recuperando contratos del servidor...")
            response = requests.get(
                f"{self.server_url}/api/get-contracts",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ {result['count']} contratos encontrados")
                return result
            else:
                return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def search_contracts(self, field: str, value: str) -> Dict:
        """
        Busca contratos en la BD distribuida
        
        Args:
            field: Campo a buscar (ej: 'RFC', 'NOMBRE_S')
            value: Valor a buscar
        
        Returns:
            Contratos que coinciden
        
        Ejemplo:
            result = client.search_contracts('RFC', 'ABC123456')
        """
        try:
            payload = {'field': field, 'value': value}
            response = requests.post(
                f"{self.server_url}/api/search-contracts",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def delete_contract(self, doc_id: str) -> Dict:
        """Elimina un contrato de la BD distribuida"""
        try:
            response = requests.delete(
                f"{self.server_url}/api/delete-contract/{doc_id}",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                print(f"✅ Contrato {doc_id} eliminado")
                return response.json()
            else:
                return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas del sistema distribuido"""
        try:
            response = requests.get(
                f"{self.server_url}/api/stats",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {'success': False, 'error': response.text}
        
        except Exception as e:
            return {'success': False, 'error': str(e)}


# Ejemplo de uso
if __name__ == "__main__":
    print("=" * 60)
    print("🔗 CLIENTE OCR DISTRIBUIDO")
    print("=" * 60)
    
    # Crear cliente (conecta a servidor remoto)
    client = OCRClient(server_url="http://localhost:5000")
    
    if client.check_connection():
        print("✅ Conectado al servidor distribuido\n")
        
        # Obtener estadísticas
        stats = client.get_stats()
        if stats.get('success'):
            print("📊 Estadísticas del sistema:")
            print(json.dumps(stats['stats'], indent=2))
    else:
        print("❌ No hay conexión al servidor")
        print("Inicia api_server.py primero:\n")
        print("  python services/api_server.py")
