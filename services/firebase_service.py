"""
firebase_service.py - Servicio de conexión a Firebase Firestore (BD Distribuida en Nube)

Cumple criterio 3.3: Distribución real usando BD en nube (no local)
Cumple criterio 2.3: Usa BD distribuida (NoSQL)
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from datetime import datetime
import os
import json

class FirebaseService:
    """Servicio para interactuar con Firestore (BD distribuida en Google Cloud)"""
    
    _instance = None  # Singleton pattern para reutilizar conexión
    
    def __new__(cls):
        """Garantiza una única conexión a Firebase"""
        if cls._instance is None:
            cls._instance = super(FirebaseService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize_firebase()
            self._initialized = True
    
    def _initialize_firebase(self):
        """
        Inicializa conexión a Firebase Firestore
        Requiere archivo de credenciales: firebase_credentials.json
        """
        try:
            # Buscar archivo de credenciales
            cred_path = os.path.join(
                os.path.dirname(__file__), 
                "..", 
                "firebase_credentials.json"
            )
            
            if not os.path.exists(cred_path):
                print(f"⚠️  Archivo de credenciales no encontrado: {cred_path}")
                print("Para configurar Firebase:")
                print("1. Ve a https://console.firebase.google.com")
                print("2. Crea un proyecto")
                print("3. Descarga JSON de credenciales")
                print("4. Guarda en firebase_credentials.json")
                self.db = None
                return
            
            # Inicializar app si no está ya inicializada
            if not firebase_admin.get_app(None):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print("✅ Conectado a Firebase Firestore (BD Distribuida)")
            
        except Exception as e:
            print(f"❌ Error conectando a Firebase: {e}")
            self.db = None
    
    def add_contract_record(self, record_data: dict) -> str:
        """
        Agrega un nuevo registro de contrato a Firestore
        
        Args:
            record_data: Diccionario con datos del contrato
        
        Returns:
            ID del documento creado
        """
        if self.db is None:
            raise ConnectionError("Firebase no está configurado")
        
        try:
            # Agregar timestamp automático
            record_data['Fecha_Procesamiento'] = datetime.now().isoformat()
            record_data['sincronizado'] = True
            
            # Añadir a colección "contratos"
            doc_ref = self.db.collection('contratos').document()
            doc_ref.set(record_data)
            
            print(f"✅ Contrato guardado en Firestore con ID: {doc_ref.id}")
            return doc_ref.id
            
        except Exception as e:
            print(f"❌ Error guardando contrato: {e}")
            raise
    
    def get_all_contracts(self) -> list:
        """
        Recupera todos los contratos de Firestore
        
        Returns:
            Lista de diccionarios con datos de contratos
        """
        if self.db is None:
            raise ConnectionError("Firebase no está configurado")
        
        try:
            docs = self.db.collection('contratos').stream()
            contracts = []
            
            for doc in docs:
                contract = doc.to_dict()
                contract['id'] = doc.id  # Incluir ID de documento
                contracts.append(contract)
            
            return contracts
            
        except Exception as e:
            print(f"❌ Error recuperando contratos: {e}")
            return []
    
    def update_contract(self, doc_id: str, updates: dict) -> bool:
        """
        Actualiza un contrato existente
        
        Args:
            doc_id: ID del documento
            updates: Diccionario con campos a actualizar
        
        Returns:
            True si fue exitoso
        """
        if self.db is None:
            raise ConnectionError("Firebase no está configurado")
        
        try:
            self.db.collection('contratos').document(doc_id).update(updates)
            print(f"✅ Contrato {doc_id} actualizado")
            return True
            
        except Exception as e:
            print(f"❌ Error actualizando contrato: {e}")
            return False
    
    def delete_contract(self, doc_id: str) -> bool:
        """
        Elimina un contrato
        
        Args:
            doc_id: ID del documento
        
        Returns:
            True si fue exitoso
        """
        if self.db is None:
            raise ConnectionError("Firebase no está configurado")
        
        try:
            self.db.collection('contratos').document(doc_id).delete()
            print(f"✅ Contrato {doc_id} eliminado")
            return True
            
        except Exception as e:
            print(f"❌ Error eliminando contrato: {e}")
            return False
    
    def query_contracts_by_field(self, field: str, value: str) -> list:
        """
        Busca contratos por un campo específico
        
        Args:
            field: Nombre del campo (ej: 'RFC')
            value: Valor a buscar
        
        Returns:
            Lista de contratos que coinciden
        """
        if self.db is None:
            raise ConnectionError("Firebase no está configurado")
        
        try:
            query = self.db.collection('contratos').where(field, '==', value)
            docs = query.stream()
            
            results = []
            for doc in docs:
                contract = doc.to_dict()
                contract['id'] = doc.id
                results.append(contract)
            
            return results
            
        except Exception as e:
            print(f"❌ Error en búsqueda: {e}")
            return []


# Uso global - singleton
firebase_service = FirebaseService()
