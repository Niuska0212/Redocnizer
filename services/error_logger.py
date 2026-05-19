# !/usr/bin/env python3
# -*- coding: utf-8 -*-
# services/error_logger.py

import os
import json
from datetime import datetime
from pathlib import Path


class ErrorLogger:
    """
    Sistema de logging para registrar errores de procesamiento de archivos.
    Crea archivos log con información detallada de errores.
    """
    
    def __init__(self, project_root=None):
        """
        Inicializa el logger con la ruta del proyecto.
        
        Args:
            project_root: Ruta raíz del proyecto. Si es None, usa el directorio actual.
        """
        if project_root is None:
            project_root = os.getcwd()
        
        self.project_root = project_root
        self.logs_dir = os.path.join(project_root, "logs")
        self._create_logs_directory()
    
    def _create_logs_directory(self):
        """Crea la carpeta logs si no existe."""
        if not os.path.exists(self.logs_dir):
            os.makedirs(self.logs_dir, exist_ok=True)
    
    def log_file_error(self, file_name, error_type, error_message, additional_data=None):
        """
        Registra un error de procesamiento de archivo en un archivo log.
        
        Args:
            file_name: Nombre del archivo que causó el error
            error_type: Tipo de excepción (ej: ValueError, FileNotFoundError)
            error_message: Mensaje de error detallado
            additional_data: Diccionario con datos adicionales (opcional)
        
        Returns:
            Ruta del archivo log creado
        """
        timestamp = datetime.now()
        log_filename = f"error_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        log_path = os.path.join(self.logs_dir, log_filename)
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "file_name": file_name,
            "error_type": error_type,
            "error_message": error_message,
            "additional_data": additional_data or {}
        }
        
        # Escribir en formato JSON para facilitar parsing posterior
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        return log_path
    
    def log_batch_errors(self, errors_list):
        """
        Registra múltiples errores en un único archivo log.
        
        Args:
            errors_list: Lista de diccionarios con estructura:
                        [{
                            "file_name": str,
                            "error_type": str,
                            "error_message": str,
                            "additional_data": dict (opcional)
                        }, ...]
        
        Returns:
            Ruta del archivo log creado
        """
        timestamp = datetime.now()
        log_filename = f"batch_errors_{timestamp.strftime('%Y%m%d_%H%M%S')}.log"
        log_path = os.path.join(self.logs_dir, log_filename)
        
        log_entry = {
            "timestamp": timestamp.isoformat(),
            "total_errors": len(errors_list),
            "errors": errors_list
        }
        
        with open(log_path, 'w', encoding='utf-8') as f:
            json.dump(log_entry, f, indent=2, ensure_ascii=False)
        
        return log_path


# Instancia global para uso fácil
_error_logger = None

def get_error_logger(project_root=None):
    """Obtiene la instancia global del logger."""
    global _error_logger
    if _error_logger is None:
        _error_logger = ErrorLogger(project_root)
    return _error_logger
