# ejemplo_sincronizacion.py
"""
Ejemplo de uso del servicio Google Drive para sincronización.
Demuestra los puntos 3.3, 3.4, 3.5, 3.6 del Módulo 3
"""

import os
import sys
import pandas as pd
from datetime import datetime

# Agregar ruta del proyecto
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.google_drive_service import GoogleDriveService


def ejemplo_1_autenticacion():
    """
    EJEMPLO 1: Autenticación OAuth 2.0
    Demuestra: 3.4 (Protocolos) + 3.5 (Cliente-servidor)
    """
    print("\n" + "="*60)
    print("EJEMPLO 1: AUTENTICACIÓN CON GOOGLE (OAuth 2.0)")
    print("="*60)
    
    try:
        # Esto abrirá el navegador para login la PRIMERA VEZ
        drive = GoogleDriveService()
        
        # Obtener información del usuario
        user_info = drive.get_user_info()
        print(f"\n✅ Usuario autenticado:")
        print(f"   Nombre: {user_info['nombre']}")
        print(f"   Email: {user_info['email']}")
        
        # Obtener info de almacenamiento
        storage = drive.get_storage_info()
        print(f"\n💾 Almacenamiento Google Drive:")
        print(f"   Usado: {storage['usado_gb']} GB")
        print(f"   Total: {storage['total_gb']} GB")
        print(f"   Disponible: {storage['disponible_gb']} GB")
        print(f"   Porcentaje: {storage['porcentaje_uso']}%")
        
        return drive
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def ejemplo_2_subir_archivo(drive):
    """
    EJEMPLO 2: Subir archivo a Google Drive
    Demuestra: 3.3 (BD nube) + 3.5 (Distribución)
    """
    print("\n" + "="*60)
    print("EJEMPLO 2: SUBIR ARCHIVO A GOOGLE DRIVE")
    print("="*60)
    
    try:
        # Crear archivo de prueba
        test_file = "contrato_ejemplo.txt"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("Este es un contrato de ejemplo\n")
            f.write(f"Creado: {datetime.now()}\n")
        
        # Subir a Drive
        file_id = drive.upload_contract(test_file, "contrato_OCR_ejemplo.txt")
        print(f"\n✅ Archivo subido exitosamente")
        print(f"   ID en Drive: {file_id}")
        
        # Limpiar archivo local
        os.remove(test_file)
        
        return file_id
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def ejemplo_3_listar_archivos(drive):
    """
    EJEMPLO 3: Listar archivos en la nube
    Demuestra: 3.3 (BD distribuida)
    """
    print("\n" + "="*60)
    print("EJEMPLO 3: LISTAR ARCHIVOS EN GOOGLE DRIVE")
    print("="*60)
    
    try:
        files = drive.list_files(limit=10)
        
        print(f"\n📁 Archivos en OCR-Modular (primeros 10):")
        print(f"   Total: {len(files)}\n")
        
        for i, file in enumerate(files, 1):
            size_mb = int(file.get('size', 0)) / (1024**2)
            print(f"   {i}. {file['name']}")
            print(f"      ID: {file['id']}")
            print(f"      Tamaño: {size_mb:.2f} MB")
            print(f"      Creado: {file.get('createdTime', 'N/A')[:10]}")
            print()
    
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_4_subir_csv(drive):
    """
    EJEMPLO 4: Subir datos CSV (base de datos)
    Demuestra: 3.3 (BD distribuida) + 3.6 (Compartir recursos)
    """
    print("\n" + "="*60)
    print("EJEMPLO 4: SUBIR DATOS CSV A GOOGLE DRIVE")
    print("="*60)
    
    try:
        # Crear DataFrame con datos de ejemplo
        datos = {
            'ID': ['001', '002', '003'],
            'RFC': ['ABC123XYZ', 'DEF456UVW', 'GHI789RST'],
            'NOMBRE': ['Juan Pérez', 'María García', 'Carlos López'],
            'FECHA_PROCESAMIENTO': [
                datetime.now(),
                datetime.now(),
                datetime.now()
            ]
        }
        
        df = pd.DataFrame(datos)
        
        print(f"\nDatos a subir:")
        print(df.to_string(index=False))
        
        # Subir CSV
        file_id = drive.upload_csv_data(df, "datos_contratos_procesados.csv")
        print(f"\n✅ CSV subido a Drive")
        print(f"   ID: {file_id}")
        print(f"   Registros: {len(df)}")
        
        return file_id
    
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def ejemplo_5_descargar_csv(drive, file_id):
    """
    EJEMPLO 5: Descargar datos CSV desde la nube
    Demuestra: 3.3 (Recuperación de BD distribuida)
    """
    print("\n" + "="*60)
    print("EJEMPLO 5: DESCARGAR CSV DESDE GOOGLE DRIVE")
    print("="*60)
    
    try:
        # Descargar CSV
        df_descargado = drive.download_csv_data(file_id)
        
        print(f"\n✅ CSV descargado desde Drive")
        print(f"   Registros: {len(df_descargado)}\n")
        print(df_descargado.to_string(index=False))
    
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_6_sincronizar_carpeta(drive):
    """
    EJEMPLO 6: Sincronizar carpeta completa
    Demuestra: 3.5 (Distribución) + 3.6 (Multi-dispositivo)
    """
    print("\n" + "="*60)
    print("EJEMPLO 6: SINCRONIZAR CARPETA LOCAL")
    print("="*60)
    
    try:
        # Crear carpeta de ejemplo
        test_dir = "ejemplos_contratos"
        os.makedirs(test_dir, exist_ok=True)
        
        # Crear algunos archivos
        for i in range(3):
            with open(f"{test_dir}/contrato_{i}.txt", "w") as f:
                f.write(f"Contrato ejemplo {i}\nFecha: {datetime.now()}\n")
        
        print(f"\n📁 Sincronizando carpeta: {test_dir}")
        
        # Sincronizar a Drive
        uploaded = drive.sync_local_to_drive(test_dir)
        
        print(f"\n✅ Sincronización completada")
        print(f"   Archivos subidos: {len(uploaded)}")
        
        # Limpiar
        for i in range(3):
            os.remove(f"{test_dir}/contrato_{i}.txt")
        os.rmdir(test_dir)
    
    except Exception as e:
        print(f"❌ Error: {e}")


def ejemplo_7_flujo_distribuido():
    """
    EJEMPLO 7: Flujo distribuido completo
    Simula: Usuario trabajando desde múltiples ubicaciones
    Demuestra: 3.5 (Cliente-servidor) + 3.6 (Multi-dispositivo)
    """
    print("\n" + "="*60)
    print("EJEMPLO 7: FLUJO DISTRIBUIDO (MULTI-DISPOSITIVO)")
    print("="*60)
    
    print("""
ESCENARIO: Usuario trabajando desde Oficina y Casa
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

LUNES - OFICINA
1. Usuario abre app en Oficina-PC
2. Se autentica con Google (OAuth 2.0)
3. Descarga archivos de Drive a local
4. Procesa contrato: contrato_lunes.pdf
5. Genera datos: datos_lunes.csv
6. Sube resultados a Drive
   └─ contratos/contrato_lunes.pdf ✓
   └─ datos/datos_lunes.csv ✓

    [Datos Persistentes en Google Drive]
           ↓ HTTPS Sync

MARTES - CASA
1. Usuario abre app en Casa-PC
2. Se autentica con MISMA cuenta Google
3. Descarga archivos actualizados de Drive
   └─ Ve contrato_lunes.pdf (del día anterior)
   └─ Ve datos_lunes.csv (del día anterior)
4. Continúa procesamiento: contrato_martes.pdf
5. Sube nuevos resultados
   └─ contratos/contrato_martes.pdf ✓
   └─ datos/datos_martes.csv ✓

JUSTIFICACIÓN DEL DISEÑO:
─────────────────────────
✅ 3.3: Datos en Google Drive (nube), NO servidor local
✅ 3.4: Comunicación HTTPS + OAuth 2.0
✅ 3.5: Arquitectura cliente-servidor distribuida
✅ 3.6: BD compartida entre múltiples dispositivos

VENTAJAS:
─────────
• Usuario puede cambiar de PC sin perder datos
• Backup automático en Google Drive
• Sincronización en tiempo real
• Sin conflictos de sobrescritura (timestamps)
• Escalable a múltiples usuarios
• No requiere servidor local
    """)


def main():
    """
    MAIN: Ejecuta todos los ejemplos
    """
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║  EJEMPLOS DE USO: SINCRONIZACIÓN CON GOOGLE DRIVE     ║")
    print("║  Módulo 3: Sistemas Robustos, Paralelos y Distribuidos║")
    print("╚" + "="*58 + "╝")
    
    # Ejemplo 1: Autenticación
    drive = ejemplo_1_autenticacion()
    if not drive:
        print("\n❌ No se pudo autenticar. Verifica SETUP_GOOGLE_DRIVE.md")
        return
    
    # Ejemplo 2: Subir archivo
    file_id = ejemplo_2_subir_archivo(drive)
    
    # Ejemplo 3: Listar archivos
    ejemplo_3_listar_archivos(drive)
    
    # Ejemplo 4: Subir CSV
    csv_id = ejemplo_4_subir_csv(drive)
    
    # Ejemplo 5: Descargar CSV
    if csv_id:
        ejemplo_5_descargar_csv(drive, csv_id)
    
    # Ejemplo 6: Sincronizar carpeta
    ejemplo_6_sincronizar_carpeta(drive)
    
    # Ejemplo 7: Flujo distribuido
    ejemplo_7_flujo_distribuido()
    
    print("\n" + "="*60)
    print("✅ EJEMPLOS COMPLETADOS")
    print("="*60)
    print("\nPróximos pasos:")
    print("1. Ejecutar: python app.py")
    print("2. Ir a pestaña '☁️ Sincronización Nube'")
    print("3. Hacer click en '🔐 Conectar con Google'")
    print("4. Probar subida/descarga de archivos")
    print("\n")


if __name__ == "__main__":
    main()
