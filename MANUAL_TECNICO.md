# Manual Técnico — SIAC ERP

> Guía de arquitectura, convenciones y desarrollo para el equipo técnico.
> **Versión:** 1.0.0 — **Última actualización:** Agosto 2026

---

## Índice

1. [Arquitectura del sistema](#1-arquitectura-del-sistema)
2. [Convenciones de código](#2-convenciones-de-código)
3. [Capa de base de datos](#3-capa-de-base-de-datos)
4. [Capa de modelos](#4-capa-de-modelos)
5. [Capa de controllers](#5-capa-de-controllers)
6. [Capa de vistas](#6-capa-de-vistas)
7. [Sistema de componentes](#7-sistema-de-componentes)
8. [Sistema de reportes](#8-sistema-de-reportes)
9. [Seguridad y permisos](#9-seguridad-y-permisos)
10. [Sistema de migraciones](#10-sistema-de-migraciones)
11. [Pruebas](#11-pruebas)
12. [CI/CD](#12-cicd)
13. [Despliegue y distribución](#13-despliegue-y-distribución)

---

## 1. Arquitectura del sistema

### 1.1 Visión general

SIAC ERP sigue un patrón **MVC (Model-View-Controller)** estricto con separación de responsabilidades por capas:

```
src/
├── database/      → Esquema SQL y conexión singleton
├── models/        → Acceso a datos (solo SQL)
├── controllers/   → Lógica de negocio (sin Qt)
├── views/         → Interfaz gráfica Qt (sin acceso directo a BD)
├── components/    → Controles reutilizables aprobados
└── utils/         → Helpers puros y widgets genéricos
```

### 1.2 Reglas de separación

| Capa | Puede hacer | NO puede hacer |
|---|---|---|
| **Models** | SQL, CRUD, consultas agregadas | Lógica de negocio, importar de `views/` |
| **Controllers** | Lógica de negocio, orquestar modelos | Importar Qt, tocar la BD directamente |
| **Views** | Construir UI, recibir controller | Toque la BD, importar modelos directamente |
| **Utils** | Helpers puros, widgets genéricos | Estado persistente, lógica de negocio |
| **Components** | Widgets reutilizables aprobados | Lógica de negocio específica de módulo |

### 1.3 Flujo de datos

```
Usuario → Vista → Controller → Modelo → DatabaseManager → SQLite/PostgreSQL
                ↑
                └── Respuesta del Controller a la Vista
```

### 1.4 Patrón de arranque

```python
# main.py
def main():
    app = QApplication(sys.argv)
    load_styles()                              # Cargar styles.qss
    DatabaseManager().initialize_schema()      # Crear esquema + migraciones
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
```

### 1.5 Singleton DatabaseManager

`DatabaseManager` es un **singleton** que mantiene una sola conexión a la base de datos:

```python
from src.database.db_manager import DatabaseManager

db = DatabaseManager()  # Siempre la misma instancia

# Métodos principales
db.fetch_all(sql, params)    # → list[dict]
db.fetch_one(sql, params)    # → dict | None
db.execute(sql, params)      # → cursor (INSERT/UPDATE/DELETE)
```

---

## 2. Convenciones de código

### 2.1 Nomenclatura

| Elemento | Convención | Ejemplo |
|---|---|---|
| **Archivos** | `snake_case` + sufijo de capa | `orden_compra_model.py` |
| **Clases** | `PascalCase` + sufijo de rol | `OrdenCompraModel`, `ProduccionController` |
| **Funciones** | `snake_case` + verbo al inicio | `listar_ordenes()`, `crear_orden()` |
| **Variables** | `snake_case` | `fecha_emision`, `total_pares` |
| **Constantes** | `snake_case` (proyecto lo usa) | `_MENTA`, `_SALVIA` |
| **Métodos privados** | Prefijo `_` | `_setup_ui()`, `_cargar_datos()` |
| **Slots Qt** | Prefijo `_on_` | `_on.modelo_seleccionado()` |
| **Idioma** | **Español** en todo | `listar_ordenes`, NO `get_orders` |

### 2.2 Contratos por capa

#### Modelos

```python
class MiModel:
    def __init__(self):
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        """Lista registros."""
        ...

    def obtener(self, id: int) -> dict | None:
        """Obtiene un registro por ID."""
        ...

    def crear(self, ...) -> int:
        """Crea un registro. Retorna cursor.lastrowid."""
        ...

    def actualizar(self, id: int, ...) -> None:
        """Actualiza un registro."""
        ...

    def desactivar(self, id: int) -> None:
        """Borrado lógico (activo = 0)."""
        ...

    def buscar(self, termino: str) -> list[dict]:
        """Búsqueda por texto."""
        ...
```

#### Controllers

```python
class MiController:
    def __init__(self):
        self.modelo_a = ModeloA()
        self.modelo_b = ModeloB()

    def metodo_publico(self, ...) -> ...:
        """Lógica de negocio que orquesta modelos."""
        ...
```

#### Vistas

```python
class MiVista(QWidget):
    def __init__(self, controller: MiController):
        self.controller = controller
        self._setup_ui()
        self._load_datos()

    def _setup_ui(self):
        """Construye la interfaz gráfica."""
        ...

    def _load_datos(self):
        """Carga datos desde el controller."""
        ...

    def _buscar(self, texto: str):
        """Búsqueda filtrada."""
        ...

    def _nuevo(self):
        """Diálogo de creación."""
        ...

    def _exportar(self):
        """Exportar a Excel/PDF."""
        ...
```

### 2.3 Type hints

Obligatorios en firmas públicas:

```python
def listar_ordenes(self, solo_activos: bool = True) -> list[dict]:
def obtener_orden(self, id: int) -> dict | None:
def crear_orden(self, proveedor_id: int, total: float) -> int:
def imprimir_reporte(self, datos: dict, parent: QWidget | None = None) -> None:
```

Usar `from __future__ import annotations` cuando sea necesario para compatibilidad.

### 2.4 SQL con placeholders

**PROHIBIDO** interpolar valores de usuario en SQL:

```python
# ❌ PROHIBIDO
db.fetch_all(f"SELECT * FROM insumos WHERE nombre = '{nombre}'")

# ✅ CORRECTO
db.fetch_all("SELECT * FROM insumos WHERE nombre = ?", (nombre,))
```

---

## 3. Capa de base de datos

### 3.1 Esquema

El esquema completo vive en `src/database/schema.sql` y es compatible con SQLite y PostgreSQL.

**Tabla de estatus por catálogo:**

| Catálogo | Columna | Estatus válidos |
|---|---|---|
| Orden de Compra | `estatus` | `pendiente`, `recibida`, `cancelada`, `recibida_con_diferencias` |
| Orden de Compra | `tipo` | `orden`, `factura` |
| Orden de Producción | `estatus` | `planeada`, `en_produccion`, `terminada` |
| Seguimiento | `estatus` | `pendiente`, `en_proceso`, `completado` |
| Movimientos | `tipo_movimiento` | `entrada`, `salida`, `ajuste` |
| Pedidos Cliente | `estatus` | `pendiente`, `programado`, `completado` |
| Programación | `estatus` | `programado`, `en_proceso`, `completado` |

### 3.2 Convenciones de tablas

| Tipo de tabla | Convención | Ejemplo |
|---|---|---|
| Entidades principales | Plural, `snake_case` | `ordenes_compra`, `insumos` |
| Tablas de detalle | Prefijo `detalle_` | `detalle_orden_compra` |
| Catálogos configurables | Sufijo `_catalogo` | `tallas_catalogo`, `colores_catalogo` |
| Junturas N:M | `tabla_a_tabla_b` | `proveedor_insumos`, `usuario_permisos` |
| Históricos | Sufijo `_historico` o `_log` | `historico_campos`, `logs_sistema` |

### 3.3 Convenciones de columnas

```sql
-- PK
id INTEGER PRIMARY KEY AUTOINCREMENT

-- FK
modelo_id INTEGER NOT NULL REFERENCES modelos(id)

-- Booleanos (borrado lógico)
activo INTEGER NOT NULL DEFAULT 1

-- Fechas
created_at TEXT NOT NULL DEFAULT (datetime('now'))
updated_at TEXT NOT NULL DEFAULT (datetime('now'))

-- Estatus (español, minúscula, snake_case)
estatus TEXT NOT NULL DEFAULT 'pendiente'
```

### 3.4 Folios secuenciales

Generados únicamente con `src/utils/folios.py`:

```python
from src.utils.folios import siguiente_folio

folio = siguiente_folio("ordenes_compra", "folio", "OC", digitos=4)
# → "OC-0001", "OC-0002", ...

folio = siguiente_folio("ordenes_produccion", "folio", "OP", digitos=4)
# → "OP-0001", "OP-0002", ...
```

**Excepción:** Las facturas capturan su folio manualmente (`FAC-...`).

### 3.5 Datos iniciales

Insertados con `INSERT OR IGNORE` en `schema.sql`:
- Tallas/puntos del catálogo (00-13, 15-31)
- Estaciones de producción (Corte, Pespunte, Montado, Ensuelado, Acabado, Empaque)
- Usuario admin inicial
- Permisos ACL por módulo y acción
- Unidades de medida
- Colores de variante

---

## 4. Capa de modelos

### 4.1 Archivos de modelos

| Archivo | Responsabilidad |
|---|---|
| `orden_compra_model.py` | Órdenes de compra, proveedores, detalle |
| `inventario_model.py` | Insumos, lista de materiales, movimientos |
| `produccion_model.py` | Modelos, variantes, OP, seguimiento, PT |
| `clientes_model.py` | Clientes, pedidos de cliente |
| `programacion_model.py` | Programación semanal |
| `dashboard_model.py` | Indicadores agregados del dashboard |
| `ficha_tecnica_model.py` | Fichas técnicas y fotos |
| `empresa_model.py` | Configuración de empresa |
| `accesos_model.py` | Usuarios, permisos, autenticación |
| `catalogos_model.py` | Tallas, colores, unidades de medida |
| `historico_campos_model.py` | Histórico de capturas en campos |
| `etiqueta_model.py` | Configuración de etiquetas |
| `impresiones_model.py` | Cola de impresión de etiquetas |
| `movimiento_inventario_model.py` | Movimientos de inventario detallados |

### 4.2 Patrón de consulta

```python
class InsumoModel:
    def __init__(self):
        self.db = DatabaseManager()

    def listar(self, solo_activos: bool = True) -> list[dict]:
        sql = "SELECT * FROM insumos"
        if solo_activos:
            sql += " WHERE activo = 1"
        sql += " ORDER BY codigo"
        return self.db.fetch_all(sql)

    def obtener(self, id: int) -> dict | None:
        return self.db.fetch_one(
            "SELECT * FROM insumos WHERE id = ?", (id,))

    def crear(self, codigo: str, nombre: str, categoria: str,
              unidad_medida: str, stock_minimo: float = 0) -> int:
        cursor = self.db.execute(
            "INSERT INTO insumos (codigo, nombre, categoria, "
            "unidad_medida, stock_minimo) VALUES (?, ?, ?, ?, ?)",
            (codigo, nombre, categoria, unidad_medida, stock_minimo))
        return cursor.lastrowid
```

---

## 5. Capa de controllers

### 5.1 Archivos de controllers

| Archivo | Responsabilidad |
|---|---|
| `ordenes_compra_controller.py` | Gestión de OC, proveedores, recepción |
| `inventario_controller.py` | Gestión de insumos, BOM, movimientos |
| `produccion_controller.py` | Modelos, variantes, OP, seguimiento |
| `clientes_controller.py` | Clientes y pedidos |
| `programacion_controller.py` | Programación semanal |
| `dashboard_controller.py` | Indicadores del dashboard |
| `accesos_controller.py` | Autenticación y permisos |
| `impresiones_controller.py` | Cola de impresión |
| `logs_controller.py` | Logs del sistema |
| `respaldo_controller.py` | Respaldo y restauración |

### 5.2 Patrón de controller

```python
class InventarioController:
    def __init__(self):
        self.insumo_model = InsumoModel()
        self.lista_materiales_model = ListaMaterialesModel()
        self.movimiento_model = MovimientoInventarioModel()

    def listar_insumos(self) -> list[dict]:
        return self.insumo_model.listar()

    def crear_insumo(self, codigo: str, nombre: str, ...) -> int:
        # Validación de negocio
        if self.insumo_model.existe_codigo(codigo):
            raise ValueError(f"Ya existe un insumo con código {codigo}")
        return self.insumo_model.crear(codigo, nombre, ...)

    def registrar_movimiento(self, insumo_id: int, tipo: str,
                            cantidad: float) -> None:
        # Lógica compuesta: actualizar stock + registrar movimiento
        self.movimiento_model.crear(insumo_id, tipo, cantidad)
        self.insumo_model.actualizar_stock(insumo_id, tipo, cantidad)
```

---

## 6. Capa de vistas

### 6.1 Archivos de vistas

| Archivo | Responsabilidad |
|---|---|
| `main_window.py` | Ventana principal, toolbar, navegación |
| `login_view.py` | Pantalla de login |
| `dashboard_view.py` | Dashboard con KPIs y gráficas |
| `ordenes_compra_view.py` | Módulo de órdenes de compra |
| `produccion_view.py` | Módulo de producción |
| `stock_view.py` | Módulo de inventario |
| `clientes_view.py` | Módulo de clientes y pedidos |
| `programacion_view.py` | Programación semanal |
| `configuracion_view.py` | Configuración del sistema |
| `sandbox_view.py` | Sandbox de pruebas |
| `dialogs.py` | Todos los diálogos del sistema |
| `kanban_view.py` | Tablero Kanban de producción |
| `search_dialog.py` | Buscador global (Ctrl+K) |
| `logs_view.py` | Visor de logs del sistema |

### 6.2 Patrón de vista principal

```python
class StockView(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = InventarioController()
        self._setup_ui()
        self._load_insumos()

    def set_permisos(self, permisos: set) -> None:
        """Aplica permisos a botones y acciones."""
        self.vista.establecer_boton_modulo(
            "nuevo", tiene(permisos, "inventario", "crear"))

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        # Header con título y subtítulo
        # Toolbar con botones de acción
        # GridHibrido con columnas y renderers

    def _load_insumos(self) -> None:
        """Carga datos desde el controller."""
        insumos = self.controller.listar_insumos()
        self.vista.set_datos(insumos)

    def _nuevo_insumo(self) -> None:
        """Abre diálogo de creación."""
        dlg = DialogInsumo(self.controller)
        if dlg.exec():
            self._load_insumos()
```

### 6.3 Patrón de diálogos

```python
class DialogInsumo(QDialog):
    def __init__(self, controller: InventarioController,
                 insumo_id: int | None = None):
        super().__init__()
        self.controller = controller
        self.insumo_id = insumo_id
        self.setWindowTitle("Nuevo Insumo" if not insumo_id else "Editar Insumo")
        self.setModal(True)
        self._setup_ui()
        if insumo_id:
            self._load_data()

    def _setup_ui(self) -> None:
        """Construye el formulario."""
        ...

    def _load_data(self) -> None:
        """Carga datos existentes para edición."""
        datos = self.controller.obtener_insumo(self.insumo_id)
        if datos:
            self.txt_codigo.setText(datos.get("codigo", ""))

    def _guardar(self) -> None:
        """Valida y guarda los datos."""
        codigo = self.txt_codigo.text().strip()
        if not codigo:
            QMessageBox.warning(self, "Error", "El código es obligatorio.")
            return
        # Guardar...
        self.accept()
```

### 6.4 Estilos y temas

Los estilos globales viven en `src/utils/styles.qss` y se cargan con `load_styles()`. El estilizado se hace por `objectName`:

```python
# Asignar objectName
boton.setObjectName("btnPrimary")
tarjeta.setObjectName("card")
titulo.setObjectName("sectionTitle")
```

Colores del tema:
- **Menta:** `#D4EDEA` (fondos suaves)
- **Salvia:** `#A9C5C1` (bordes, acentos)
- **Verde oscuro:** `#2f4f3a` (texto principal)
- **Verde medio:** `#5b6b60` (texto secundario)

---

## 7. Sistema de componentes

### 7.1 Ciclo de vida

1. **Prototipo en Sandbox:** Desarrollar en `src/views/sandbox_view.py`
2. **Aprobación:** Cuando el usuario diga "aprobar X control"
3. **Componente reutilizable:** Mover a `src/components/` con API pública
4. **Registro:** Agregar en `src/components/__init__.py` con `registrar_componente()`
5. **Prueba:** Incluir prueba `pytest` en `tests/`
6. **Uso:** Importar desde `src.components.obtener_componente("nombre")`

### 7.2 Registro de componentes

```python
# src/components/__init__.py

def registrar_componente(nombre: str, clase: type, descripcion: str) -> None:
    """Registra un componente reutilizable en el catálogo."""
    _COMPONENTES[nombre] = {"clase": clase, "descripcion": descripcion}

def listar_componentes() -> list[dict]:
    """Devuelve la lista de componentes disponibles."""
    return [{"nombre": n, "descripcion": d["descripcion"]}
            for n, d in sorted(_COMPONENTES.items())]

def obtener_componente(nombre: str) -> type:
    """Devuelve la clase registrada o lanza KeyError."""
    return _COMPONENTES[nombre]["clase"]
```

### 7.3 Ejemplo: creación de componente

```python
# src/components/mi_componente.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class MiComponente(QWidget):
    """Descripción del componente para el catálogo.

    API pública:
    - __init__(datos: list[dict], parent=None)
    - obtener_seleccion() -> dict | None
    - establecer_datos(datos: list[dict]) -> None

    Señales:
    - seleccion_cambiada(dict)
    """

    def __init__(self, datos: list[dict],
                 parent: QWidget | None = None):
        super().__init__(parent)
        self._datos = datos
        self._setup_ui()

    def _setup_ui(self) -> None:
        ...

    def obtener_seleccion(self) -> dict | None:
        """Retorna el registro seleccionado."""
        ...

    def establecer_datos(self, datos: list[dict]) -> None:
        """Reemplaza los datos mostrados."""
        ...
```

```python
# Registro en __init__.py
from src.components.mi_componente import MiComponente  # noqa: E402

registrar_componente(
    "mi_componente",
    MiComponente,
    "Descripción del componente para el catálogo.",
)
```

---

## 8. Sistema de reportes

### 8.1 Plantilla base

`src/utils/print_template.py` proporciona bloques HTML reutilizables:

```python
from src.utils.print_template import (
    esc,                         # Escapar HTML
    fmt_fecha,                   # Formatear fecha
    logo_base64,                 # Logo en base64
    nombre_empresa,              # Nombre de la empresa
    html_cabecera,               # Encabezado institucional
    html_ondas_superiores,       # Decoración de ondas
    html_pie,                    # Pie de página
    html_obs_bloque,             # Bloque de observaciones
    wrap_hoja,                   # Envolver en hoja Carta
)
```

### 8.2 Generación de reportes

```python
def generar_html_reporte(datos: dict, detalle: list[dict]) -> str:
    """Genera el HTML del reporte."""
    cabecera = html_cabecera(
        "TÍTULO DEL REPORTE",
        folio=datos.get("folio", ""),
        fecha=datos.get("fecha", ""))

    contenido = f"""
    {cabecera}
    {html_ondas_superiores()}
    <div style="padding: 0 14mm;">
        <!-- Contenido del reporte -->
    </div>
    {html_pie("Mensaje del pie")}
    """
    return wrap_hoja(contenido)
```

### 8.3 Visualización e impresión

```python
from src.components.preview_impresion import previsualizar_html

# Mostrar vista previa
previsualizar_html(html, titulo="Reporte", parent=ventana)

# Desde un módulo específico
from src.utils.ficha_tecnica_print import imprimir_ficha_tecnica
imprimir_ficha_tecnica(modelo, ficha, fotos, parent=ventana)
```

### 8.4 Exportación a Excel

```python
from src.utils.export_utils import export_table_to_excel

# Exportar tabla genérica
path = export_table_to_excel(tabla, "Nombre_Reporte", parent)

# Exportar orden de compra específica
from src.utils.export_utils import export_orden_compra_excel
path = export_orden_compra_excel(datos, detalle, parent)
```

---

## 9. Seguridad y permisos

### 9.1 Autenticación

- Contraseñas hasheadas con **bcrypt** (`src/utils/security.py`)
- Login obligatorio antes de acceder al sistema
- Credenciales iniciales: `admin` / `admin123`

```python
from src.utils.security import hash_contrasena, verificar_contrasena

# Hash
hash_ = hash_contrasena("mi_contraseña")

# Verificar
es_valida = verificar_contrasena("mi_contraseña", hash_)
```

### 9.2 Permisos ACL

Los permisos se organizan por **módulo × acción**:

| Módulo | Acciones disponibles |
|---|---|
| `ordenes_compra` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `produccion` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `inventario` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `configuracion` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `usuarios` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `clientes` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |
| `programacion` | `ver`, `crear`, `editar`, `eliminar`, `exportar` |

### 9.3 Verificación de permisos

```python
from src.models.accesos_model import tiene

# En la vista
def set_permisos(self, permisos: set) -> None:
    self.btn_nuevo.setVisible(
        tiene(permisos, "inventario", "crear"))
    self.btn_exportar.setVisible(
        tiene(permisos, "inventario", "exportar"))

# En el controller
if not tiene(self._permisos, "ordenes_compra", "eliminar"):
    QMessageBox.warning(self, "Acceso denegado",
                       "No tiene permisos para cancelar órdenes.")
    return
```

### 9.4 Roles

| Rol | Permisos |
|---|---|
| `admin` | Acceso total + Sandbox + Logs |
| `operador` | Permisos asignados individualmente |

---

## 10. Sistema de migraciones

### 10.1 Mecanismo

Las migraciones viven en `DatabaseManager._migrar()` y se ejecutan automáticamente en cada arranque después de `initialize_schema()`.

### 10.2 Tipos de migración

#### Columna nueva (aditiva)

```python
# Verificar si la columna existe
columnas = [row[1] for row in db.execute("PRAGMA table_info(tabla)")]
if "nueva_columna" not in columnas:
    db.execute("ALTER TABLE tabla ADD COLUMN nueva_columna TEXT DEFAULT ''")
```

#### Tabla nueva

```python
db.execute("""
    CREATE TABLE IF NOT EXISTS nueva_tabla (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ...
    )
""")
```

### 10.3 Reglas

- **Aditivas y no destructivas:** Nunca borrar columnas o tablas
- **Cada bloque en try/except:** Para no abortar el arranque
- **Sin pérdida de datos:** Usar renombrar → crear → copiar → borrar si es necesario

---

## 11. Pruebas

### 11.1 Configuración

```bash
# Instalar dependencias
pip install -r requirements-dev.txt

# Ejecutar todas las pruebas
QT_QPA_PLATFORM=offscreen pytest

# Ejecutar pruebas de un módulo
QT_QPA_PLATFORM=offscreen pytest tests/test_matriz_tallas.py -v

# Ejecutar con cobertura
QT_QPA_PLATFORM=offscreen pytest --cov=src tests/
```

### 11.2 Fixtures

`tests/conftest.py` proporciona:

- `qapp` — Fixture de sesión para QApplication
- Teardown automático para evitar segfault de PySide6

### 11.3 Convenciones de pruebas

- Archivos: `tests/test_{nombre}.py`
- Funciones: `def test_{descripción}():`
- Un componente aprobado **DEBE** incluir su prueba `pytest`
- No crear timers/animaciones sin detenerlos

### 11.4 Ejemplo de prueba

```python
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtWidgets import QApplication
from src.components.matriz_tallas import MatrizTallasDialog

def test_matriz_tallas_obtener_valores(qtbot):
    puntos = [{"id": 1, "punto": "22"}, {"id": 2, "punto": "23"}]
    dlg = MatrizTallasDialog(puntos)
    dlg.show()
    qtbot.addWidget(dlg)

    # Verificar que se crearon las celdas
    assert "22" in dlg.celdas
    assert "23" in dlg.celdas

    # Establecer valores
    dlg.establecer_valores({"22": 10, "23": 20})
    valores = dlg.obtener_valores()
    assert valores["22"] == 10
    assert valores["23"] == 20
```

---

## 12. CI/CD

### 12.1 GitHub Actions

El workflow `.github/workflows/siaci.yml` ejecuta:

1. **Flake8** — Errores bloqueantes (`E9,F63,F7,F82`)
2. **Pytest** — Pruebas unitarias
3. **Plataforma:** Ubuntu + Python 3.12
4. **Variables de entorno:** `QT_QPA_PLATFORM=offscreen`, `LIBGL_ALWAYS_SOFTWARE=1`

### 12.2 Ramas

| Rama | Propósito |
|---|---|
| `main` | Versión oficial (post-release) |
| `productivo1` | Rama de desarrollo activo |
| `feature/nombre` | Ramas por tarea |

### 12.3 Flujo de trabajo

1. Crear rama `feature/nombre` desde `productivo1`
2. Desarrollar y pasar pruebas localmente
3. Crear PR hacia `productivo1`
4. CI debe pasar sin errores
5. Merge a `productivo1`
6. Post-release: merge a `main`

---

## 13. Despliegue y distribución

### 13.1 PyInstaller

El proyecto usa PyInstaller para generar ejecutable:

```bash
pyinstaller --onefile --windowed --name "SIAC_ERP" main.py
```

### 13.2 Inno Setup

`installer.iss` configura el instalador de Windows con:
- Instalación en `Program Files`
- Acceso directo en escritorio
- Desinstalador

### 13.3 Archivos excluidos de git

| Archivo | Razón |
|---|---|
| `config.ini` | Contiene credenciales |
| `goretti_erp.db` | Datos de producción |
| `opencode.json` | API keys |
| `*.pyc` / `__pycache__` | Archivos compilados |
| `.venv/` | Entorno virtual |

---

<div align="center">

**SIAC ERP** — Manual Técnico v1.0.0

*Para preguntas o soporte, contactar al equipo de desarrollo.*

</div>
