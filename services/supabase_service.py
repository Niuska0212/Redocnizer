import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class SupabaseManager:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    # UPDATE PK (Cambia las PK y propagar los cambios)
    def actualizar_pk(self, tabla, pk_columna, valor_viejo, valor_nuevo):
        """
        Cambia el PK dependiendo de:
        1. automatico si no existe el nuevo valor (Con CASCADE)
        2. manual si ya existe el nuevo valor (MERGE)
        """
        # Verifica si el valor ya existe (para no chocar)
        existe = self.supabase.table(tabla).select(pk_columna).eq(pk_columna, valor_nuevo).execute()
        
        if existe.data:
            # Caso de MERGE
            if tabla == "maestro":
                self.supabase.table("contrato").update({"codigo_maestro": valor_nuevo}).eq("codigo_maestro", valor_viejo).execute()

            elif tabla == "materia":
                self.supabase.table("contrato").update({"crn_materia": valor_nuevo}).eq("crn_materia", valor_viejo).execute()
            
            elif tabla == "contrato":
                self.supabase.table("contrato_dependencia").update({"num_contrato": valor_nuevo}).eq("num_contrato", valor_viejo).execute()

            elif tabla == "dependencia":
                self.supabase.table("contrato_dependencia").update({"id_dependencia": valor_nuevo}).eq("id_dependencia", valor_viejo).execute()
            
            return self.supabase.table(tabla).delete().eq(pk_columna, valor_viejo).execute()

        else:
            # Solo cambia la PK (CASCADE)
            return self.supabase.table(tabla).update({pk_columna: valor_nuevo}).eq(pk_columna, valor_viejo).execute()
        
    def merge_maestro_codigo(self, old_codigo, new_codigo):
        try:
            # 1. Verificar si ya existe el nuevo código
            existing = self.supabase.table("maestro").select("*").eq("codigo", new_codigo).execute()

            if existing.data:
                # 🔥 MERGE

                # Actualizar contratos para que apunten al nuevo código
                self.supabase.table("contrato")\
                    .update({"codigo_maestro": new_codigo})\
                    .eq("codigo_maestro", old_codigo)\
                    .execute()

                # Eliminar el maestro viejo
                self.supabase.table("maestro")\
                    .delete()\
                    .eq("codigo", old_codigo)\
                    .execute()

            else:
                # 🔥 UPDATE NORMAL (CASCADE automática si tienes FK bien configurada)
                self.supabase.table("maestro")\
                    .update({"codigo": new_codigo})\
                    .eq("codigo", old_codigo)\
                    .execute()

        except Exception as e:
            print(f"Error en merge_maestro_codigo: {e}")

    def upsert_full_record(self, row):
        try:
            codigo = row["CODIGO"]
            crn = row["CRN"]
            num = row["NUM"]

            # ======================
            # 1. MAESTRO
            # ======================
            self.supabase.table("maestro").upsert({
                "codigo": codigo,
                "nombre": row.get("NOMBRE_S", ""),
                "paterno": row.get("PATERNO", ""),
                "materno": row.get("MATERNO", ""),
                "telefono": row.get("TELEFONO", ""),
                "rfc": row.get("RFC", ""),
                "imss": row.get("IMSS", ""),
                "curp": row.get("CURP", "")
            }).execute()

            # ======================
            # 2. MATERIA
            # ======================
            self.supabase.table("materia").upsert({
                "crn": crn,
                "nombre": row.get("MATERIA", "")
            }).execute()

            # ======================
            # 3. CONTRATO
            # ======================
            self.supabase.table("contrato").upsert({
                "num": num,
                "codigo_maestro": codigo,
                "crn_materia": crn,
                "desde": row.get("DESDE"),
                "hasta": row.get("HASTA"),
                "hrs_totales": row.get("HRS_TOTALES", 0)
            }).execute()

            # ======================
            # 4. DEPENDENCIAS
            # ======================
            deps = [
                row.get("DEPENDENCIA_1"),
                row.get("DEPENDENCIA_2"),
                row.get("DEPENDENCIA_3")
            ]

            for dep in deps:
                if not dep:
                    continue

                # Insertar dependencia si no existe
                dep_query = self.supabase.table("dependencia").select("id_dependencia").eq("nombre", dep).execute()

                if dep_query.data:
                    dep_id = dep_query.data[0]["id_dependencia"]
                else:
                    insert_res = self.supabase.table("dependencia").insert({"nombre": dep}).execute()


                # Obtener ID
                dep_id = insert_res.data[0]["id_dependencia"]

                # Relación contrato_dependencias
                self.supabase.table("contrato_dependencias").upsert({
                    "num_contrato": num,
                    "id_dependencia": dep_id
                }).execute()

        except Exception as e:
            print(f"Error en upsert_full_record: {e}")
            raise