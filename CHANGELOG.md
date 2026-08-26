# Changelog — SIAC ERP

> Registro de cambios notables de cada versión.
> Formato basado en [Keep a Changelog](https://keepachangelog.com/es/1.1.0/).
> El proyecto sigue [CalVersioning](https://calver.org/) con formato `YYYY.M.DD`.

---

## [Unreleased] — 2026-08-26

### Added
- **Dashboard del sistema:** Pantalla de resumen con 6 tarjetas KPI clicables que navegan a cada módulo del sistema
  - OC pendientes, compras del mes, producción en curso, insumos stock bajo, pares en PT, movimientos del día
  - Gráfica de barras de compras por mes (QPainter, sin dependencias externas)
  - Tablas de detalle: últimas OC, OPs en curso, stock bajo, movimientos recientes
- **Ficha técnica rediseñada:** Layout split con paneles izquierdo/derecho
  - Panel izquierdo: datos generales, comentarios/firmas, fotos de piezas (rejilla 2 columnas)
  - Panel derecho superior: características por sección con buscador en tiempo real
  - Panel derecho inferior: materiales del modelo con cantidad por par editable y costo calculado en vivo
- **Costos BOM en ficha técnica:** Costo unitario por insumo (último precio de compra o menor precio de proveedor activo)
- **Impresión de ficha técnica profesional:** Formato "Hoja de especificación de diseño" con identidad visual mint/salvia, secciones de datos generales, fotos, especificaciones, materiales y firmas
- **Carga de HTML grande en preview_impresion:** Archivos temporales para documentos >1.5MB (límite de IPC Chromium en WebEngine)
- **Estilos QSS para tarjetas KPI clicable:** Borde teal resaltado al pasar el cursor
- **Ícono "dashboard"** en `src/utils/icons.py`

### Changed
- **DialogFichaTecnica:** Reestructurado completamente con `QSplitter` horizontal y vertical, mínimo 1024×700, maximización automática
- **Producción - Lista de Materiales:** Refresca automáticamente al entrar a la pestaña o cerrar ficha técnica
- **preview_impresion:** Corrige carrera de condiciones al imprimir PDF desde WebEngine (guardia de carga)

### Fixed
- Impresión de ficha técnica mostraba página en blanco con HTML grande
- `loadFinished` tardío podía disparar PDF sin datos

---

## [v1.0.0] — 2026-08-20

> **Primer release oficial del sistema.**

### Added
- **Onboarding wizard:** Asistente de primera configuración para nuevos usuarios
- **Empaquetado PyInstaller:** Generación de ejecutable `onedir` con datos en `%APPDATA%\SIAC`
- **GridHibrido:** Componente wrapper de ComplexGrid con toolbar de 2 filas (módulo + grid) y barra de estado
- **Plantilla compartida de impresión** (`print_template.py`): Bloques HTML reutilizables (cabecera, ondas, pie, wrap_hoja) con tema mint/salvia
- **Refactorización de impresión:** Todos los reportes usan la plantilla compartida

### Changed
- **Toolbar superior:** Módulos al lado izquierdo, Sandbox/Salir al lado derecho
- **ComplexGrid → GridHibrido:** Se reemplaza ComplexGrid directo por el wrapper con toolbar unificada

---

## [Histórico] — 2026-08-04 al 2026-08-19

### 2026-08-19

#### Changed
- Refactoriza impresión con plantilla compartida `print_template` (WYSIWYG)
- Mejora dialogos de stock y movimientos

### 2026-08-18

#### Fixed
- Alineación de toolbar: módulos a la izquierda, Sandbox/Salir a la derecha

### 2026-08-17

#### Added
- **Vista de Logs del Sistema:** Diálogo con filtros, detalle, limpieza y exportación (solo admin en Ayuda)
- **Buscador global (Ctrl+K):** Búsqueda de registros en cualquier módulo con navegación directa
- **Atajos de teclado:** Ctrl+1 a Ctrl+6 para módulos, Ctrl+K buscador, Ctrl+, configuración
- **Prototipo GridHibridoDemo en Sandbox:** Prueba del grid híbrido antes de aprobar
- **Toolbar con colores por módulo:** Ícono arriba/abajo estilo prototipo
- **Estilo oscuro del toolbar:** Gradiente `#1e293b`, botones indigo, status bar oscura
- **Manual de Usuario SIAC ERP en PDF (v1.0):** Script generador con reportlab
- **Cola de impresión de etiquetas:** Gestión de solicitudes desde app móvil (vía Supabase)

#### Changed
- Sincronización productivo1: variantes, toolbar, impresión, mobile, docs

### 2026-08-14

#### Added
- **Rediseño de impresión de etiquetas:** Modos Flejes (Cajas) y Partidas con matriz de tallas
- Botones extra al ComplexGrid
- Exportación de programación con formato de reporte

#### Fixed
- Imports en Configuración
- Catálogo de componentes del Sandbox

### 2026-08-13

#### Added
- **Impresora virtual SIAC:** Opción de simulación en pantalla desde Configuración
- **Notificaciones flotantes (toasts):** Tarjetas animadas con tipos info/success/warning/error
- **Toolbar superior de navegación:** Reemplaza sidebar colapsable
- **Botón "Programar" por fila** en programación de pedidos
- **Historial de campos:** Campo de texto con histórico de capturas y autocompletado
- **Date Picker:** Selector de fecha con calendario emergente
- **Etiquetas y preview** de impresión
- **Empaquetado PyInstaller (onedir):** Datos en `%APPDATA%\SIAC`

#### Changed
- Aplica tema clásico Windows Forms en todo el sistema
- Ajusta tamaños de ventana y matrices de tallas para mostrar contenido completo
- Captura de tallas integrada en "Agregar Línea" de pedidos

### 2026-08-12

#### Added
- **Migración RD-1:** Unifica puntos y tallas en catálogo único `tallas_catalogo`
- **Precio por talla** en órdenes de compra
- Puntos 15-21 agregados al catálogo
- Selectores de proveedor por razón social/nombre comercial
- Filas más altas en detalle de OC
- **Preview de impresión como componente aprobado**
- **AGENTS.md:** Documenta reglas del proyecto (RD-1..RD-7) y protege opencode.json
- **CI/CD:** GitHub Actions escucha `productivo1` y `main`

### 2026-08-10

#### Added
- **Programación semanal** con etiquetas, programar pedido y navegación
- **Workflow CI** (`siaci.yml`) con flake8 y pytest
- **pytest.ini** con pythonpath para encontrar el paquete `src`
- **Pruebas unitarias** de NotificacionesFlotantes

#### Fixed
- Segfault de PySide6 al cerrar pytest (teardown Qt de sesión)
- Segfault en notificaciones: timer propio por tarjeta, detener animaciones antes de borrar
- `E999` en `complex_grid` (`_reporte_html`)
- Limpieza defensiva: detener timers/animaciones al cerrar o destruir

#### Removed
- Workflow `python-app.yml` obsoleto (duplicado, sin deps Qt)

### 2026-08-09

#### Added
- **Catálogo de componentes propios:** `src/components/__init__.py` con `registrar_componente()`, `listar_componentes()`, `obtener_componente()`
- **Componente aprobado: MatrizTallasDialog** — Matriz de tallas por bloques con navegación Enter/Tab
- **Componente aprobado: ComplexGrid** — Tabla de datos con búsqueda, filtros, agrupación, vistas y exportación
- **Componente aprobado: OdooListView** — Vista de listado con alternador tabla/lista/iconos
- **Sandbox:** Área de pruebas de controles (solo admin)
- **Iconos SVG embebidos** (`src/utils/icons.py`)
- **Estilos QSS globales** (`src/utils/styles.qss`)
- **Notificaciones flotantes** (prototipo en Sandbox)
- **Importador de directorio** con colores en consola

### 2026-08-06

#### Added
- **Módulo Clientes y Pedidos:** Catálogo de clientes con pedidos de cliente
- Captura por tallas en pedidos
- Importación masiva de proveedores e insumos desde `DIRECTORIO.xlsx`
- Logo jpeg en la interfaz

### 2026-08-05

#### Added
- **Facturas en órdenes de compra:** Folio manual (`FAC-...`), tipo `factura`, color verde claro `#daf2d0`
- **Nombre comercial de proveedores** en catálogo
- **Tablas estilo Excel:** Ajuste de columnas por arrastre o doble clic
- **Autenticación con bcrypt** (`src/utils/security.py`)
- **Video splash de bienvenida** en MainWindow
- **Folios de solo lectura** en campos generados
- **Imágenes en insumos y modelos**

---

## Decisiones de diseño (RD) aplicadas

| ID | Decisión | Fecha de aplicación |
|---|---|---|
| **RD-1** | Unificar puntos y tallas en `tallas_catalogo` | 2026-08-12 |
| **RD-4** | Flujo git: `productivo1` → `main`, CI escucha ambas | 2026-08-12 |
| **RD-5** | Motor BD: PostgreSQL producción, SQLite desarrollo | Vigente |
| **RD-6** | Todo componente aprobado debe incluir prueba `pytest` | Vigente |
| **RD-7** | Archivos de raíz documentados; `opencode.json` protegido | 2026-08-12 |

---

## Componentes aprobados (fecha de registro)

| Componente | Fecha | Descripción |
|---|---|---|
| `odoo_list` | 2026-08-09 | Vista de listado con alternador tabla/lista/iconos |
| `matriz_tallas` | 2026-08-09 | Matriz de tallas por bloques con navegación Enter/Tab |
| `complexGrid` | 2026-08-09 | Tabla de datos con búsqueda, filtros y exportación |
| `preview_impresion` | 2026-08-12 | Vista previa WYSIWYG con zoom e impresión a PDF |
| `grid_hibrido` | 2026-08-17 | Wrapper de ComplexGrid con toolbar de 2 filas |
| `date_picker` | 2026-08-13 | Selector de fecha con calendario emergente |
| `campo_historico` | 2026-08-13 | Campo de texto con histórico de capturas |
| `notificacion_flotante` | 2026-08-09 | Toasts animados con tipos info/success/warning/error |
| `label_canvas` | 2026-08-14 | Lienzo interactivo de diseño de etiqueta |
| `editor_etiqueta` | 2026-08-14 | Creador/editor de etiquetas con guardado en BD |
| `matriz_preview` | 2026-08-14 | Widget flotante de vista previa de matriz al hover |

---

## Estadísticas del proyecto

| Métrica | Valor |
|---|---|
| **Commits totales** | 90+ |
| **Primera actividad** | 2026-08-04 |
| **Última actividad** | 2026-08-26 |
| **Contribuyentes** | 3 |
| **Pull requests mergeados** | 10+ |
| **Componentes aprobados** | 11 |
| **Archivos de código fuente** | 60+ |
| **Pruebas pytest** | 17 |

---

<div align="center">

**SIAC ERP** — Changelog

*Mantenido por el equipo de desarrollo*

</div>
