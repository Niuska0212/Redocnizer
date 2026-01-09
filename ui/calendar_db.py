"""Gestión de configuración de calendarios en SQLite."""
import sqlite3
import os
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class Calendar:
    """Representa la configuración de un calendario."""
    id: Optional[int] = None
    nombre: str = ""  # ej: "2024A"
    tipo: str = "actual"  # "actual" o "pasado"
    fecha_inicio: str = ""  # formato DD/MM/YYYY
    fecha_fin: str = ""    # formato DD/MM/YYYY
    ruta_base: str = ""    # ruta donde se guardan contratos
    fecha_creacion: str = ""  # timestamp


class CalendarDB:
    """Gestor de base de datos SQLite para calendarios."""
    
    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.path.join(os.getcwd(), "calendarios.db")
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Crea la tabla si no existe."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS calendarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                tipo TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_fin TEXT NOT NULL,
                ruta_base TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.commit()
        conn.close()
    
    def add_calendar(self, calendar: Calendar) -> int:
        """Agrega un nuevo calendario y retorna el ID."""
        calendar.fecha_creacion = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO calendarios (nombre, tipo, fecha_inicio, fecha_fin, ruta_base, fecha_creacion)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (calendar.nombre, calendar.tipo, calendar.fecha_inicio, calendar.fecha_fin, 
                  calendar.ruta_base, calendar.fecha_creacion))
            conn.commit()
            cal_id = cursor.lastrowid
            print(f"Calendario '{calendar.nombre}' creado con ID {cal_id}")
            return cal_id
        except sqlite3.IntegrityError as e:
            print(f"Error: Calendario '{calendar.nombre}' ya existe.")
            return -1
        finally:
            conn.close()
    
    def get_calendar(self, nombre: str) -> Optional[Calendar]:
        """Obtiene un calendario por nombre."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, tipo, fecha_inicio, fecha_fin, ruta_base, fecha_creacion
            FROM calendarios WHERE nombre = ?
        """, (nombre,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Calendar(
                id=row[0], nombre=row[1], tipo=row[2],
                fecha_inicio=row[3], fecha_fin=row[4], ruta_base=row[5],
                fecha_creacion=row[6]
            )
        return None
    
    def get_all_calendars(self) -> List[Calendar]:
        """Obtiene todos los calendarios."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, nombre, tipo, fecha_inicio, fecha_fin, ruta_base, fecha_creacion
            FROM calendarios ORDER BY fecha_creacion DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        
        return [
            Calendar(
                id=row[0], nombre=row[1], tipo=row[2],
                fecha_inicio=row[3], fecha_fin=row[4], ruta_base=row[5],
                fecha_creacion=row[6]
            )
            for row in rows
        ]
    
    def update_calendar(self, calendar: Calendar) -> bool:
        """Actualiza un calendario existente."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE calendarios 
                SET tipo = ?, fecha_inicio = ?, fecha_fin = ?, ruta_base = ?
                WHERE id = ?
            """, (calendar.tipo, calendar.fecha_inicio, calendar.fecha_fin, 
                  calendar.ruta_base, calendar.id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def delete_calendar(self, nombre: str) -> bool:
        """Elimina un calendario por nombre."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM calendarios WHERE nombre = ?", (nombre,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
    
    def calendar_exists(self, nombre: str) -> bool:
        """Verifica si un calendario existe."""
        return self.get_calendar(nombre) is not None
