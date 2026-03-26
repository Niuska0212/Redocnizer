#services/supabase_service.py

import os
import socket
from dotenv import load_dotenv
from supabase import create_client, Client
import math
import pandas as pd

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
            # 1. Extraer y limpiar datos básicos
            codigo = clean_int(row.get("CODIGO"))
            num = clean_int(row.get("NUM"))
            nombre_materia = clean_str(row.get("MATERIA"))
            crn = clean_int(row.get("CRN"))

            if not codigo or not num:
                print(f"⚠️ Registro omitido: Falta CODIGO ({codigo}) o NUM ({num})")
                return

            # ======================
            # 1. MAESTRO (Conflicto en 'codigo')
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
            }, on_conflict="codigo").execute()

            # Si no devolvió datos (porque ya existía), lo buscamos por su código UNIQUE
            if not maestro_res.data:
                maestro_res = self.supabase.table("maestro").select("id_maestro").eq("codigo", codigo).execute()
            
            id_maestro = maestro_res.data[0]["id_maestro"]

            # ======================
            # 2. MATERIA (Conflicto en 'crn')
            # ======================
            id_materia = None
            if crn:
                mat_res = self.supabase.table("materia").upsert({
                    "crn": crn,
                    "nombre": nombre_materia
                }, on_conflict="crn").execute()

                if not mat_res.data:
                    mat_res = self.supabase.table("materia").select("id_materia").eq("crn", crn).execute()
                
                if mat_res.data:
                    id_materia = mat_res.data[0]["id_materia"]

            # ======================
            # 3. CONTRATO (Conflicto en 'num')
            # ======================
            contrato_res = self.supabase.table("contrato").upsert({
                "num": num,
                "id_maestro": id_maestro,
                "id_materia": id_materia,
                "desde": str(row.get("DESDE", "")),
                "hasta": str(row.get("HASTA", "")),
                "hrs_totales": str(row.get("HRS_TOTALES", "0"))
            }, on_conflict="num").execute()

            if not contrato_res.data:
                contrato_res = self.supabase.table("contrato").select("id_contrato").eq("num", num).execute()
            
            id_contrato = contrato_res.data[0]["id_contrato"]

            # ======================
            # 4. DEPENDENCIAS
            # ======================
            deps = [row.get("DEPENDENCIA_1"), row.get("DEPENDENCIA_2"), row.get("DEPENDENCIA_3")]
            
            # Borrar relaciones previas para evitar duplicados en la tabla intermedia
            self.supabase.table("contrato_dependencia").delete().eq("id_contrato", id_contrato).execute()

            for dep_nombre in deps:
                name_clean = clean_str(dep_nombre)
                if not name_clean or name_clean.lower() in ["none", "nan", ""]:
                    continue
                
                # Upsert en tabla dependencia (Conflicto en 'nombre' según tu SQL)
                dep_res = self.supabase.table("dependencia").upsert(
                    {"nombre": name_clean}, 
                    on_conflict="nombre"
                ).execute()
                
                if not dep_res.data:
                    dep_res = self.supabase.table("dependencia").select("id_dependencia").eq("nombre", name_clean).execute()

                if dep_res.data:
                    dep_id = dep_res.data[0]["id_dependencia"]
                    # Insertar en tabla intermedia contrato_dependencia
                    self.supabase.table("contrato_dependencia").insert({
                        "id_contrato": id_contrato,
                        "id_dependencia": dep_id
                    }).execute()

            #print(f"✅ Sincronizado correctamente: Num {num}")

        except Exception as e:
            print(f"❌ Error en upsert_full_record (Num {row.get('NUM')}): {e}")
            # No bloqueamos el bucle completo, permitimos que siga con el siguiente
        
    def sync_calendar_dataframe(self, df):
        """Sincroniza el DataFrame de forma robusta sin bloquear la App."""
        # 1. Verificación rápida de conexión
        if not self.check_connection():
            print("☁️ Supabase: Sin internet. Sincronización omitida.")
            return False

        try:
            # 2. Limpieza de datos (NaN a None para compatibilidad JSON)
            # Usamos infer_objects para evitar warnings de versiones nuevas de Pandas
            df_sync = df.where(pd.notnull(df), None)

            # 3. Sincronización con "Escudo"
            print(f"☁️ Iniciando sincronización de {len(df_sync)} registros...")
            
            for _, row in df_sync.iterrows():
                try:
                    # Intentamos el upsert de cada fila
                    # Nota: Asegúrate de que upsert_full_record tenga su propio try/except
                    self.upsert_full_record(row)
                except Exception as e_row:
                    # Si una fila falla, saltamos a la siguiente sin cerrar la app
                    print(f"⚠️ Error en fila específica: {e_row}")
                    continue 

            print("✅ Sincronización completada exitosamente.")
            return True

        except Exception as e:
            # 4. Error silencioso: El programa principal NO se entera del fallo de red
            # Esto evita que la ventana de la app se cierre sola
            print(f"📡 Aviso de Red: Supabase no disponible temporalmente ({e})")
            return False
        finally:
            # Liberar memoria después de procesar el DataFrame
            import gc
            gc.collect()
        

    def fetch_all_data(self):
        """Recupera todos los registros de Supabase reconstruyendo la estructura del CSV."""
        if not self.check_connection():
            return None

        try:
            # Consulta con joins para traer info de maestro, materia y dependencias
            # Nota: Ajusta los nombres de las columnas según tu esquema exacto
            res = self.supabase.table("contrato").select(
                "*, maestro(*), materia(*), contrato_dependencia(dependencia(nombre))"
            ).execute()
            
            raw_data = res.data
            if not raw_data:
                return []

            formatted_list = []
            for item in raw_data:
                maestro = item.get("maestro", {})
                materia = item.get("materia", {})
                
                # Extraer nombres de dependencias
                deps = [d["dependencia"]["nombre"] for d in item.get("contrato_dependencia", [])]
                
                # Reconstruir el diccionario con las llaves que espera DataManager
                row = {
                    "NUM": item.get("num"),
                    "CODIGO": maestro.get("codigo"),
                    "NOMBRE_S": maestro.get("nombre"),
                    "PATERNO": maestro.get("paterno"),
                    "MATERNO": maestro.get("materno"),
                    "CURP": maestro.get("curp"),
                    "RFC": maestro.get("rfc"),
                    "IMSS": maestro.get("imss"),
                    "TELEFONO": maestro.get("telefono"),
                    "CRN": materia.get("crn"),
                    "MATERIA": materia.get("nombre"),
                    "DESDE": item.get("desde"),
                    "HASTA": item.get("hasta"),
                    "HRS_TOTALES": item.get("hrs_totales"),
                    "DEPENDENCIA_1": deps[0] if len(deps) > 0 else "",
                    "DEPENDENCIA_2": deps[1] if len(deps) > 1 else "",
                    "DEPENDENCIA_3": deps[2] if len(deps) > 2 else ""
                }
                formatted_list.append(row)
                
            return formatted_list
        except Exception as e:
            print(f"❌ Error al recuperar de la nube: {e}")
            return None