# services/csv_service.py
import pandas as pd
import os

def update_calendar_csv(calendar_root_dir, data, calendar_name):
    """
    Actualiza el CSV del calendario. 
    Ahora el archivo vive directamente en la carpeta raíz de calendarios.
    """
    # 1. La ruta ahora es CALENDARIOS/2024A.csv en lugar de CALENDARIOS/2024A/contratos.csv
    csv_path = os.path.join(calendar_root_dir, f"{calendar_name}.csv")

    # 2. Solo nos aseguramos que la carpeta raíz exista (ej. CALENDARIOS)
    if not os.path.exists(calendar_root_dir):
        os.makedirs(calendar_root_dir, exist_ok=True)

    if os.path.exists(csv_path):
        # Leer con encoding UTF-8 explícitamente
        df = pd.read_csv(csv_path, encoding='utf-8')
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        # Si no existe, creamos el DataFrame nuevo
        df = pd.DataFrame([data])

    # Guardar con UTF-8-sig para que Excel lo abra sin problemas de acentos
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path