# 🤝 Guía de Contribución - REDOCNIZER

## Antes de Empezar

Gracias por tu interés en contribuir a REDOCNIZER. Este documento te guiará sobre cómo participar en el desarrollo del proyecto.

### Tipos de Contribución

- 🐛 **Reportar bugs**
- ✨ **Sugerir mejoras**
- 📝 **Mejorar documentación**
- 🔧 **Enviar código**
- 🧪 **Crear pruebas**

---

## 1. Reportar Bugs

### Antes de reportar

- Verifica que el bug no haya sido reportado antes
- Actualiza a la última versión
- Intenta reproducir el error

### Cómo reportar

Abre un [Issue](https://github.com/Niuska0212/Redocnizer/issues) con:

```markdown
**Descripción**: 
[Descripción clara del problema]

**Pasos para reproducir**:
1. [Primer paso]
2. [Segundo paso]
3. ...

**Comportamiento esperado**:
[Qué debería pasar]

**Comportamiento actual**:
[Qué está pasando]

**Entorno**:
- OS: [Windows/macOS/Linux]
- Python: [versión]
- REDOCNIZER: [versión]

**Logs/Screenshots**:
[Adjuntar archivos relevantes]
```

---

## 2. Sugerir Mejoras

Abre un Issue con el título: **[FEATURE REQUEST]** seguido de tu idea.

```markdown
**Descripción**:
[Explicación clara de la mejora]

**Beneficios**:
[Por qué es útil]

**Módulo afectado**:
- [ ] Módulo 2 (Gestión TI)
- [ ] Módulo 3 (Distribuido)
- [ ] Módulo 4 (SoftComputing)

**Complejidad estimada**:
- [ ] Pequeña (1-2 horas)
- [ ] Media (1-2 días)
- [ ] Grande (> 1 semana)
```

---

## 3. Enviar Código

### Preparación

1. **Fork el repositorio**
   ```bash
   # En GitHub, click en "Fork"
   ```

2. **Clonar tu fork**
   ```bash
   git clone https://github.com/tu-usuario/redocnizer.git
   cd redocnizer
   ```

3. **Crear rama**
   ```bash
   git checkout -b feature/nombre-del-feature
   # o
   git checkout -b fix/nombre-del-bug
   ```

4. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # macOS/Linux
   # o
   venv\Scripts\activate  # Windows
   ```

5. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # Dev dependencies
   ```

### Desarrollo

#### Estructura de código

Sigue PEP 8 y estas convenciones:

```python
# Buen ejemplo:
def process_contract_document(file_path: str, calendar: str) -> Dict[str, Any]:
    """
    Procesa un documento de contrato.
    
    Args:
        file_path: Ruta al archivo (PDF, PNG o JPG)
        calendar: Período académico (ej: 2024A)
    
    Returns:
        Diccionario con datos extraídos y estado
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        ValueError: Si el formato no es soportado
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
    
    # Implementación...
    
    return {
        'success': True,
        'data': {...}
    }
```

#### Estilo

- **Máximo 120 caracteres por línea**
- **4 espacios de indentación**
- **Nombres descriptivos en inglés**
- **Type hints en funciones importantes**
- **Docstrings para funciones públicas**

```python
# Nombre de variables
archivo_procesado = True          # ✅ Claro
nombres_usuarios = ["Juan"]       # ✅ Plural para listas
TIMEOUT_SECONDS = 30              # ✅ Constantes en mayúsculas
temp = get_data()                 # ❌ Demasiado corto
```

#### Localización

El código es en **inglés**, la UI puede estar en **español**.

```python
# core/preprocessing.py (código - inglés)
def normalize_image(image: np.ndarray) -> np.ndarray:
    """Normalize pixel values to [0, 1] range."""
    return image / 255.0

# ui/main_window.py (UI - español)
self.btn_process.setText("🚀 Procesar Contratos")
```

### Testing

```python
# tests/test_preprocessing.py
import pytest
from core.preprocessing import normalize_image

def test_normalize_image():
    """Test que normaliza imagen correctamente."""
    img = np.random.randint(0, 255, (10, 10, 3), dtype=np.uint8)
    result = normalize_image(img)
    
    assert result.min() >= 0.0
    assert result.max() <= 1.0
    assert result.dtype == np.float32

def test_normalize_image_empty():
    """Test con imagen vacía."""
    with pytest.raises(ValueError):
        normalize_image(np.array([]))
```

**Requisitos:**
- Mínimo 70% de cobertura de código
- Todas las pruebas deben pasar
- Nombra tests así: `test_<función>_<caso>`

### Commits

```bash
# Escribir commits claros y descriptivos
git commit -m "feat: add CRNN inference optimization

- Reduced inference time by 30%
- Added batch processing support
- Includes GPU acceleration

Closes #123"
```

**Formato:**
```
<tipo>: <descripción corta>

<descripción larga opcional>

<referencias a issues>
```

**Tipos de commit:**
- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato/estilo
- `refactor`: Refactorización sin cambios funcionales
- `test`: Agregar o actualizar tests
- `chore`: Cambios en build, dependencias, etc.

### Push y Pull Request

1. **Push tu rama**
   ```bash
   git push origin feature/nombre-del-feature
   ```

2. **Crear Pull Request**
   - Ir a GitHub y crear PR
   - Completar el template

3. **Template de PR**

```markdown
## Descripción
[Descripción clara de los cambios]

## Tipo de cambio
- [ ] Corrección de bug
- [ ] Nueva funcionalidad
- [ ] Breaking change
- [ ] Actualización de documentación

## Cambios
- [x] Cambio 1
- [x] Cambio 2

## Pruebas
- [x] Test unitario agregado
- [x] Test de integración pasado
- [x] Probado manualmente en Windows

## Checklist
- [x] Mi código sigue el estilo del proyecto
- [x] Actualicé la documentación relevante
- [x] Agregué tests para nuevas funcionalidades
- [x] Todos los tests pasan localmente
- [x] Mi cambio no genera warnings

## Screenshots (si aplica)
[Adjuntar imágenes]

## Relacionado con
Fixes #123
```

---

## 4. Mejorar Documentación

### Ubicaciones de documentación

```
redocnizer/
├── README.md                      # Documentación principal
├── REQUERIMIENTOS.md              # Especificaciones técnicas
├── docs/
│   ├── GUIA_USO.md                # Guía para usuarios
│   ├── MODULOS.md                 # Cumplimiento académico
│   ├── ARQUITECTURA.md            # Arquitectura del sistema
│   └── CONTRIBUYENDO.md           # Este archivo
```

### Guías para documentación

- **Claro y conciso**: Usa términos simples
- **Ejemplos**: Incluye código cuando sea relevante
- **Estructura**: Usa headings y listas
- **Actualizado**: Sincroniza con cambios de código

---

## 5. Estándares de Calidad

### Cobertura de Pruebas

```bash
# Ejecutar pruebas con cobertura
pytest --cov=core --cov=services --cov-report=html

# Ver reporte en htmlcov/index.html
```

### Linting y Formatting

```bash
# Format automático
black --line-length 120 src/

# Linting
flake8 src/ --max-line-length 120

# Type checking
mypy src/
```

### Pre-commit Hooks

```bash
# Instalar
pip install pre-commit
pre-commit install

# Ejecutar manualmente
pre-commit run --all-files
```

---

## 6. Proceso de Revisión

### Revisores

Un PR será revisado por al menos 2 miembros del equipo.

### Checklist de revisión

- ✅ Código sigue convenciones
- ✅ Tests incluidos y passing
- ✅ Documentación actualizada
- ✅ No hay conflictos con main
- ✅ Commits son claros
- ✅ No introduce deuda técnica

### Cambios solicitados

Si hay cambios solicitados:
1. Haz los cambios
2. Commit con mensaje claro
3. Push nuevamente
4. NO hagas force push (a menos que se indique)

---

## 7. Acuerdos de la Comunidad

### Código de Conducta

Todos los contribuyentes deben seguir nuestro [Código de Conducta](CODE_OF_CONDUCT.md):

- Sé respetuoso
- Acepta crítica constructiva
- Enfócate en lo que es mejor para la comunidad
- Reporta comportamiento inadecuado

### Licencia

Al contribuir, aceptas que tu código está bajo licencia MIT.

---

## 8. Preguntas Frecuentes

### P: ¿Cómo consigo permisos de escribir?
R: Contribuye con varios PRs exitosos, y se considerará agregarte como colaborador.

### P: ¿Cuánto tiempo toma revisar mi PR?
R: Típicamente 1-3 días, dependiendo de complejidad.

### P: ¿Necesito crear issue antes de PR?
R: Para cambios pequeños, no. Para features grandes, es recomendado.

### P: ¿Cómo reporto una vulnerabilidad de seguridad?
R: NO abras un issue. Email a: niuska.gonzalez5462@alumnos.udg.mx o luis.uribe0840@alumnos.udg.mx

---

## 9. Recursos Útiles

- [Git Flow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow)
- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Tipos de commits](https://www.conventionalcommits.org/)

---

## 10. Contacto y Soporte

- **Issues**: https://github.com/Niuska0212/Redocnizer/issues
- **Discussions**: https://github.com/Niuska0212/Redocnizer.git/discussions
- **Email**: niuska.gonzalez5462@alumnos.udg.mx o luis.uribe0840@alumnos.udg.mx

---

**Gracias por contribuir a REDOCNIZER** 🙌

Versión: 2.2.1
Última actualización: 24 de febrero de 2026

