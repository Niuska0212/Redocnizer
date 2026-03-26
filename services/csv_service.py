# services/csv_service.py
import pandas as pd
import os

def update_calendar_csv(calendar_root_dir, data, calendar_name):
    """
    Actualiza el CSV del calendario evitando duplicados por el número de contrato (NUM).
    """
    csv_path = os.path.join(calendar_root_dir, f"{calendar_name}.csv")

    if not os.path.exists(calendar_root_dir):
        os.makedirs(calendar_root_dir, exist_ok=True)

    if os.path.exists(csv_path):
        # 1. Leer el archivo existente
        df = pd.read_csv(csv_path, encoding='utf-8')
        
        # 2. LÓGICA ANTI-DUPLICADOS:
        # Si el número de contrato (NUM) ya está en el CSV, eliminamos esa fila vieja
        # para que la nueva versión (data) sea la que prevalezca.
        if 'NUM' in df.columns and 'NUM' in data:
            # Mantener solo las filas cuyo NUM sea diferente al que estamos procesando
            df = df[df['NUM'].astype(str) != str(data['NUM'])]
        
        # 3. Concatenar los datos nuevos
        df_nuevo = pd.DataFrame([data])
        df = pd.concat([df, df_nuevo], ignore_index=True)
    else:
        # Si el archivo no existe, lo creamos desde cero
        df = pd.DataFrame([data])

    # Guardar con UTF-8-sig para compatibilidad con Excel
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    return csv_path