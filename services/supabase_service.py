#services/supabase_service.py

import os
import socket
from dotenv import load_dotenv
from supabase import create_client, Client
import math

load_dotenv()


# --- SOLUCIÓN AL ERROR DE CARGA ---
# Buscamos la ruta absoluta de la raíz del proyecto para encontrar el archivo
basedir = os.path.abspath(os.path.dirname(__file__)) 
# Asumiendo que este archivo está en 'services/', subimos un nivel para llegar a la raíz
dotenv_path = os.path.join(basedir, "..", "credentials_supa.env")

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
    print(f"✅ Archivo de credenciales cargado: {dotenv_path}")
else:
    # Si no existe en la raíz, intentamos cargarlo de forma genérica
    load_dotenv("credentials_supa.env")
# ----------------------------------

def clean_int(value):
        if value is None:
            return None
        if isinstance(value, float):
            if math.isnan(value):
                return None
            return int(value)
        if isinstance(value, str):
            if value.lower() == "nan" or value.strip() == "":
                return None
            return int(float(value))
        return int(value)

def clean_str(value):
        if value is None:
            return None
        if isinstance(value, float) and math.isnan(value):
            return None
        return str(value).strip()

class SupabaseManager:
    def __init__(self):
        # Cargamos directo. Si no existen, el error se capturará en el bloque try.
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        
        try:
            self.supabase: Client = create_client(self.url, self.key)
            # Mantenemos enabled solo para que MainWindow sepa si puede llamar a los métodos
            self.enabled = True 
            print("✅ Supabase: Cliente inicializado.")
        except Exception as e:
            self.enabled = False
            print(f"❌ Supabase: Error crítico al conectar: {e}")

    def check_connection(self):
        """Verifica si hay internet."""
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def upsert_full_record(self, row):
        try:
            codigo = clean_int(row.get("CODIGO"))
            num = clean_int(row.get("NUM"))
            nombre_materia = clean_str(row.get("NOMBRE_MATERIA"))
            crn = clean_int(row.get("CRN"))

            if not codigo or not num:
                print(f"Registro omitido por falta de CODIGO o NUM")
                return

            # ======================
            # 1. MAESTRO
            # ======================
            maestro_res = self.supabase.table("maestro").upsert({
                "codigo": codigo,
                "nombre": clean_str(row.get("NOMBRE_S")),
                "paterno": clean_str(row.get("PATERNO")),
                "materno": clean_str(row.get("MATERNO")),
                "telefono": clean_str(row.get("TELEFONO")),
                "rfc": clean_str(row.get("RFC")),
                "imss": clean_str(row.get("IMSS")),
                "curp": clean_str(row.get("CURP"))
            }, on_conflict="codigo", returning="representation").execute()

            maestro_data = getattr(maestro_res, "data", [])
            if not maestro_data:
                raise Exception("Error insertando maestro")
            
            id_maestro = maestro_data[0]["id_maestro"]

            # ======================
            # 2. MATERIA
            # ======================
            id_materia = None
            if nombre_materia:
                mat_res = self.supabase.table("materia").upsert({
                    "nombre": nombre_materia,
                    "crn": crn
                }, on_conflict="nombre").execute()

                mat_data = getattr(mat_res, "data", [])
                if mat_data:
                    id_materia = mat_data[0]["id_materia"]

            # ======================
            # 3. CONTRATO
            # ======================
            contrato_res = self.supabase.table("contrato").upsert({
                "num": num,
                "id_maestro": id_maestro,
                "id_materia": id_materia,
                "desde": row.get("DESDE"),
                "hasta": row.get("HASTA"),
                "hrs_totales": row.get("HRS_TOTALES", 0)
            }, on_conflict="num", returning="representation").execute()

            contrato_data = getattr(contrato_res, "data", [])

            if not contrato_data:
                raise Exception("Error insertando contrato")
            
            id_contrato = contrato_data[0]["id_contrato"]

            # ======================
            # 4. DEPENDENCIAS
            # ======================
            deps = [
                row.get("DEPENDENCIA_1"),
                row.get("DEPENDENCIA_2"),
                row.get("DEPENDENCIA_3")
            ]

            self.supabase.table("contrato_dependencia").delete().eq("id_contrato", id_contrato).execute() 

            for dep_nombre in deps:
                if not dep_nombre or str(dep_nombre).strip() == "":
                    continue
                
                # Insertar dependencia si no existe
                dep_nombre = str(dep_nombre).strip()
                
                dep_res = self.supabase.table("dependencia").upsert(
                    {"nombre": dep_nombre},
                    on_conflict="nombre"
                ).execute()
                
                dep_data = getattr(dep_res, "data", [])
                if dep_data:
                    dep_id = dep_data[0]["id_dependencia"]

                    self.supabase.table("contrato_dependencia").insert({
                        "id_contrato": id_contrato,
                        "id_dependencia": dep_id
                    }).execute()

        except Exception as e:
            print(f"Error en upsert_full_record: {e}")
            raise
        
    def sync_calendar_dataframe(self, df):
        """Sincroniza el DataFrame si hay internet."""
        if not self.check_connection():
            return False

        try:
            for _, row in df.iterrows():
                self.upsert_full_record(row)
            return True
        except Exception as e:
            print(f"❌ Error en sincronización: {e}")
            return False
        
    