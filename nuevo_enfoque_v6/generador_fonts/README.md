# Generador y Gestor de Fuentes

Este directorio contiene herramientas para gestionar las fuentes utilizadas en el entrenamiento del modelo OCR.

## `gestor_fuentes.py`

Script automatizado para enriquecer el dataset de fuentes.

### Funciones:
1.  **Auditoría de Fuentes:** Verifica la existencia de fuentes propietarias críticas (Arial, Times, Calibri) y sus variantes (Bold, Italic) en el directorio `../fonts`. Emite advertencias si faltan.
2.  **Descarga de Fuentes Open Source:** Descarga automáticamente desde Google Fonts alternativas libres de alta calidad para mejorar la robustez del modelo:
    *   **Monoespaciadas:** Courier Prime, Roboto Mono.
    *   **Serif:** Tinos (alt. Times), EB Garamond.
    *   **Sans-Serif:** Arimo (alt. Arial), Open Sans.
3.  **Instalación:** Descomprime y organiza los archivos `.ttf` descargados en el directorio de fuentes del proyecto.

### Uso:
```bash
python3 gestor_fuentes.py
```
