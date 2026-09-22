# Índice de Documentación - REDOCNIZER

REDOCNIZER es una aplicación de escritorio para procesar y organizar contratos académicos de forma local. El flujo activo utiliza PySide6, EasyOCR, OpenCV, PyMuPDF, pandas y archivos CSV. La sincronización con servicios en la nube no forma parte de la versión actual.

## Documentos principales

| Documento | Contenido |
|---|---|
| [README.md](../README.md) | Descripción general, instalación y alcance |
| [GUIA_USO.md](GUIA_USO.md) | Instalación y operación del programa |
| [ARQUITECTURA.md](ARQUITECTURA.md) | Componentes y flujo técnico |
| [REQUERIMIENTOS.md](REQUERIMIENTOS.md) | Requisitos funcionales y técnicos |
| [MODULOS.md](MODULOS.md) | Relación del proyecto con los módulos académicos |
| [CONTRIBUYENDO.md](CONTRIBUYENDO.md) | Criterios para mantenimiento del código |
| [CHANGELOG.md](CHANGELOG.md) | Historial de cambios |

## Lectura recomendada

### Usuario final

1. [README.md](../README.md)
2. [GUIA_USO.md](GUIA_USO.md)
3. [REQUERIMIENTOS.md](REQUERIMIENTOS.md), para conocer formatos y limitaciones

### Desarrollador

1. [ARQUITECTURA.md](ARQUITECTURA.md)
2. [REQUERIMIENTOS.md](REQUERIMIENTOS.md)
3. [CONTRIBUYENDO.md](CONTRIBUYENDO.md)

### Evaluación académica

1. [MODULOS.md](MODULOS.md)
2. [ARQUITECTURA.md](ARQUITECTURA.md)
3. [README.md](../README.md), especialmente la sección de alcance

## Temas rápidos

- Instalación: [GUIA_USO.md](GUIA_USO.md#1-instalacion)
- Procesamiento de contratos: [GUIA_USO.md](GUIA_USO.md#3-procesamiento-de-contratos)
- Almacenamiento CSV: [ARQUITECTURA.md](ARQUITECTURA.md#4-persistencia-local)
- Rutas de red: [GUIA_USO.md](GUIA_USO.md#6-rutas-de-red-compartida)
- Requisitos: [REQUERIMIENTOS.md](REQUERIMIENTOS.md)
- Componentes no activos: [README.md](../README.md#-notas-de-alcance-y-componentes-no-activos)

## Alcance tecnológico

El flujo principal es local y no requiere una cuenta externa, servidor web ni conexión a internet durante el uso normal. EasyOCR puede descargar sus modelos durante la instalación inicial; después, los documentos se procesan en el equipo del usuario.

El repositorio conserva módulos históricos de Google Drive, Supabase y CRNN, pero están deshabilitados o fuera del flujo productivo actual.
