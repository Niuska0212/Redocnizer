# services/csv_service.py
import pandas as pd
import os

def update_calendar_csv(calendar_dir, data):
    csv_path = os.path.join(calendar_dir, "contratos.csv")

    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])

    df.to_csv(csv_path, index=False, encoding="utf-8")
