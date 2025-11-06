¡Excelente\! Aquí tienes la versión final, **completa y con formato profesional (incluyendo tabla de contenidos y un ejemplo de uso)**, lista para copiar y pegar en tu archivo `README.md`.

He añadido secciones clave que faltaban y pulido la estructura para que sea fácil de leer y muy profesional.

## 📄 README.md Final (Completo y Profesional)

```markdown
# 🤖 OCR Híbrido: Detección y Automatización de Contratos UDG

## 🎯 Resumen del Proyecto y Objetivo

Este repositorio alberga la implementación de un **Modelo Híbrido OCR (CRNN + Tesseract)** diseñado para la **detección, reconocimiento y extracción automatizada de datos** en contratos y documentos de la **Universidad de Guadalajara (UDG)**.

El sistema busca optimizar la gestión documental al:
1.  **Reconocer texto** incluso en regiones de interés (ROIs) complejas usando una Red Neuronal Convolucional Recurrente (**CRNN**).
2.  **Segmentar dinámicamente** los documentos y aplicar lógica de extracción precisa con **Tesseract OCR** y **Pandas**.
3.  **Mejorar la precisión** a través de una pipeline de preprocesamiento robusta y el uso combinado de modelos.

---

## 🧭 Tabla de Contenidos

1.  [🎯 Resumen del Proyecto y Objetivo](#🎯-resumen-del-proyecto-y-objetivo)
2.  [✨ Arquitectura y Componentes Clave](#✨-arquitectura-y-componentes-clave)
3.  [🛠️ Instalación y Requisitos](#🛠️-instalación-y-requisitos)
4.  [▶️ Guía de Uso y Extracción de Datos](#▶️-guía-de-uso-y-extracción-de-datos)
5.  [💡 Consejos y Troubleshooting](#💡-consejos-y-troubleshooting)
6.  [👤 Autor y Contacto](#👤-autor-y-contacto)
7.  [📜 Licencia](#📜-licencia)

---

## ✨ Arquitectura y Componentes Clave

El proyecto se basa en la combinación de modelos de Deep Learning con lógica de extracción tradicional para un rendimiento óptimo.

| Componente | Tecnología | Rol Principal |
| :--- | :--- | :--- |
| **Reconocimiento Avanzado** | **CRNN (CNN + BiLSTM + CTC)** | Entrenamiento e inferencia para el reconocimiento de texto a nivel de palabra en regiones segmentadas. |
| **Segmentación y Extracción** | **Tesseract OCR + Pandas** | Detección de las Regiones de Interés (ROIs), extracción de texto en el documento completo y estructuración de los datos. |
| **Pipeline Final** | `document_extractor.py` | Orquesta el preprocesamiento, la inferencia CRNN y la segmentación Tesseract para generar la salida final. |

### Estructura Principal del Repositorio

```

.
├── models/
│   ├── keras\_cnn\_lstm\_v3\_ctc.h5  \# Modelo Keras entrenado
│   └── vocabulario\_v3.pkl        \# Vocabulario de inferencia
├── data/
│   ├── contratos/
│   └── dataset\_palabras/
└── SRC\_FINAL/
├── document\_extractor.py   \# ⬅️ **Punto de ejecución principal**
├── crnn\_inference.py       \# Lógica para cargar y usar el modelo CRNN
├── segmentacion\_dinamica.py \# Lógica de detección de ROIs con pytesseract
└── preprocessing.py        \# Funciones de limpieza de imágenes/ROIs

````

---

## 🛠️ Instalación y Requisitos

### Requisitos de Sistema

* **Sistema Operativo:** Windows 10/11
* **Lenguaje:** **Python 3.9.13** (Recomendado para compatibilidad con TensorFlow 2.14)

### 1. Instalación de Dependencias

Se recomienda encarecidamente usar un **Entorno Virtual** (`.venv`).

1.  **Clonar el repositorio:**
    ```powershell
    git clone [TU ENLACE DE REPOSITORIO]
    cd Proyecto-modular
    ```

2.  **Crear y Activar el Entorno Virtual (Ejemplo de ruta de Python 3.9):**
    ```powershell
    # Comando Powershell
    & "C:/.../Python39/python.exe" -m venv .venv
    & ".venv\Scripts\Activate.ps1"
    ```

3.  **Instalar Paquetes Python (Ejemplo de paquetes mínimos):**
    ```powershell
    # Actualizar pip
    & "C:/.../Python39/python.exe" -m pip install --upgrade pip

    # Instalar librerías
    & "C:/.../Python39/python.exe" -m pip install tensorflow==2.14.* tensorflow-intel==2.14.* tensorflow-io-gcs-filesystem==0.31.0 numpy opencv-python scikit-learn joblib pandas pillow pytesseract
    ```

### 2. Instalación de Tesseract OCR (Ejecutable)

El motor OCR de Tesseract **debe instalarse por separado**.

1.  Descargar e instalar el ejecutable desde: [Tesseract Installer (GitHub Wiki)](https://github.com/UB-Mannheim/tesseract/wiki)
2.  **Configurar la ruta en el código:** Verifica que la ruta de Tesseract en el script `SRC_FINAL/document_extractor.py` sea correcta (la ruta por defecto es la siguiente):
    ```python
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    ```

---

## ▶️ Guía de Uso y Extracción de Datos

Todos los scripts deben ejecutarse **desde la raíz del proyecto** (`n:/Proyecto-modular`) para asegurar la consistencia de las rutas.

### A. Ejecutar la Extracción/Inferencia (Producción)

El script `document_extractor.py` toma como entrada las imágenes ubicadas en `data/contratos/imagenes_jpg/`.

**Comando de Ejecución:**

```powershell
& "C:/.../Python39/python.exe" SRC_FINAL/document_extractor.py
````

**Flujo de Entrada y Salida:**

| Etapa | Descripción |
| :--- | :--- |
| **Entrada** | Imágenes de contratos en formato `.jpg` (o especificado en el script) que residen en la carpeta `data/contratos/imagenes_jpg/`. |
| **Proceso** | El pipeline aplica preprocesamiento, segmentación dinámica (Tesseract), reconocimiento (CRNN) y extracción de entidades (Pandas/RegEx). |
| **Salida** | El resultado de la extracción (datos estructurados como fechas, montos, partes involucradas, etc.) se imprime en la **consola** y se guarda como un archivo **`.csv` o `.json`** en la carpeta de salida designada (revisar `document_extractor.py` para la ruta exacta). |

### B. Entrenamiento de Modelos (Desarrollo)

Para retrain o experimentar con nuevas épocas y datasets:

```powershell
& "C:/.../Python39/python.exe" src/entrenamientoV4.py
```

-----

## 💡 Consejos y Troubleshooting

  * **Pylance / VSCode muestra "reportMissingImports":** Selecciona el intérprete correcto en VSCode: `Ctrl+Shift+P` → **"Python: Select Interpreter"** y asegúrate de elegir la versión `.venv`.
  * **Error `TesseractNotFoundError`:** Instala el ejecutable de Tesseract y verifica que la ruta `pytesseract.pytesseract.tesseract_cmd` sea la correcta en el script principal.
  * **Buenas Prácticas:** Siempre ejecuta los scripts desde la raíz del proyecto para mantener las rutas relativas consistentes.

-----

## 👤 Autor y Contacto

**Autor:** Niuska Isabel Gonzalez Rangel y Luis Diego Uribe Sandoval

  * **GitHub:** 
  * **Correo Electrónico:** 

Para reportar errores o sugerir mejoras, por favor abrir un **Issue** detallado en este repositorio.

-----

## 📜 Licencia

Este proyecto se encuentra bajo la Licencia ** MIT, Apache 2.0**

```

---

**¡Listo!** Tienes un README profesional, estructurado, con índice, y que destaca el valor técnico de tu proyecto.

Si deseas que te ayude a generar el archivo **`requirements.txt`** exacto a partir de la lista de paquetes que mencionaste, para que solo tengan que usar `pip install -r requirements.txt`, ¡solo dímelo!
```