# DOCUMENTO DE LEVANTAMIENTO — SIAC ERP
## Sistema Integral de Administración y Control

**Empresa:** GORETTI — Fábrica de Calzado
**Sistema:** SIAC ERP v1.0
**Fecha de levantamiento:** 17 de agosto de 2026
**Elaboró:** Area de Sistemas / Desarrollo
**Revisa:** _________________________
**Aprueba:** _________________________

---

## ÍNDICE

1. [Proceso 1: Inventario / Stock](#proceso-1-inventario--stock)
2. [Proceso 2: Órdenes de Compra](#proceso-2-órdenes-de-compra)
3. [Proceso 3: Producción](#proceso-3-producción)
4. [Proceso 4: Programación Semanal](#proceso-4-programación-semanal)
5. [Proceso 5: Clientes y Pedidos](#proceso-5-clientes-y-pedidos)
6. [Proceso 6: Configuración del Sistema](#proceso-6-configuración-del-sistema)
7. [Proceso 7: Seguridad y Accesos](#proceso-7-seguridad-y-accesos)
8. [Reglas de Negocio Transversales](#reglas-de-negocio-transversales)

---

# PROCESO 1: INVENTARIO / STOCK

**Módulo:** `inventario`
**Pantalla principal:** `StockView`
**Permisos:** `inventario.ver`, `inventario.crear`, `inventario.editar`, `inventario.eliminar`, `inventario.exportar`

---

## 1.1 Pantalla de Insumos

### Descripción
Pantalla principal del módulo de inventario. Muestra el catálogo de insumos (materias primas: piel, suela, forro, etc.) en una tabla con vista de filas, lista o iconos. Permite crear, editar, desactivar insumos y registrar movimientos de inventario.

### Componentes de la pantalla

| Elemento | Tipo | Descripción |
|---|---|---|
| Barra de herramientas | Toolbar | Botones: Nuevo Insumo, Editar, Desactivar, Movimiento, Buscar |
| Tabla de insumos | GorettiTable | Vista de filas/lista/iconos con columnas: Código, Nombre, Categoría, Unidad, Stock Actual, Stock Mínimo, Estatus |
| Barra de búsqueda | QLineEdit | Búsqueda por nombre, código o categoría |
| Pestaña "Movimientos" | ComplexGrid (MovimientosGrid) | Historial de movimientos de inventario con filtros |

### Botones de acción

| Botón | Acción | Permiso requerido | Descripción |
|---|---|---|---|
| Nuevo Insumo | Abre `DialogInsumo` | `inventario.crear` | Crea un nuevo insumo con código auto (INS-XXXX), nombre, categoría, unidad, stock mínimo e imagen |
| Editar | Abre `DialogInsumo` con datos existentes | `inventario.editar` | Modifica los datos de un insumo seleccionado |
| Desactivar | `controller.desactivar_insumo()` | `inventario.eliminar` | Borrado lógico (activo=0) |
| Movimiento | Abre `DialogMovimientoMultiPartida` | `inventario.crear` | Registra salidas o cambios de ubicación multi-partida |
| Buscar | Filtra la tabla | `inventario.ver` | Búsqueda en tiempo real por nombre, código o categoría |
| Imprimir | Vista previa PDF | `inventario.exportar` | Genera PDF de la tabla visible |
| Exportar Excel | Guarda archivo .xlsx | `inventario.exportar` | Exporta la tabla visible a Excel |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| INV-01 | Código automático | El código se genera automáticamente como `INS-XXXX` (siguiente_folio) |
| INV-02 | Código único | No se pueden crear dos insumos con el mismo código |
| INV-03 | Stock mínimo | Campo informativo para alertas; no bloquea movimientos |
| INV-04 | Categoría libre | Se autocompleta con categorías existentes pero permite nuevas |
| INV-05 | Borrado lógico | Los insumos se desactivan (activo=0), no se eliminan físicamente |
| INV-06 | Búsqueda | Búsqueda LIKE en código, nombre y categoría; prioriza coincidencia exacta |
| INV-07 | Stock actual | Se actualiza automáticamente con cada movimiento (entrada/salida/ajuste) |

---

## 1.2 Pantalla de Movimientos de Inventario

### Descripción
Pestaña dentro de StockView que muestra el historial de todos los movimientos de inventario (entradas por OC, salidas, ajustes, cambios de ubicación) en un grid con filtros. Cada fila muestra: Fecha, Tipo, Insumo, Cantidad, Referencia, Observaciones.

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| INV-08 | Tipos de movimiento | `entrada` (recepción de OC), `salida` (baja de material), `ajuste` (corrección manual) |
| INV-09 | Referencia | Cada movimiento puede vincularse a una OC (`referencia_tipo='orden_compra'`) o una OP |
| INV-10 | Kardex | El grid muestra el saldo acumulado por insumo en orden cronológico |
| INV-11 | Impresión de documento | Al imprimir un movimiento MVI se abre vista previa del documento PDF (folio, fecha, tipo, tabla de partidas) |

---

## 1.3 Diálogo de Nuevo Insumo (`DialogInsumo`)

### Descripción
Formulario modal para crear o editar un insumo. Incluye campo de imagen con selección/pegado de imagen.

### Campos

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| Código | QLineEdit (auto) | Sí | Auto-generado `INS-XXXX`; editable solo en creación |
| Nombre | QLineEdit | Sí | Histórico de capturas (autocompletado) |
| Categoría | SearchableComboBox | Sí | Autocompleta con categorías existentes |
| Unidad de Medida | QComboBox | Sí | Opciones: Pieza, dm2, metro, kilogramo, litro, par, rollo, caja |
| Stock Mínimo | QDoubleSpinBox | No | Valor para alertas de stock bajo |
| Imagen | WidgetImagen | No | Selección o pegado de imagen del insumo |
| Variantes por talla | Checkbox + rango | No | Genera variantes automáticamente desde/hasta talla |
| Variantes de color | Checkbox + grid | No | Genera variantes por cada color del catálogo |

---

## 1.4 Diálogo de Movimiento Multi-Partida (`DialogMovimientoMultiPartida`)

### Descripción
Formulario para registrar un movimiento de inventario que agrupa 1 a N partidas (insumos diferentes) en un solo documento. Genera folio `MVI-XXXX`.

### Campos

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| Tipo de movimiento | QComboBox | Sí | Opciones: `Salida de Inventario`, `Cambio de Ubicación` |
| Observaciones | QLineEdit | No | Observaciones generales del movimiento |
| Tabla de partidas | QTableWidget | Sí | Filas dinámicas: Insumo (combo), Cantidad (spin), Observaciones (texto) |
| Botón + | QPushButton | — | Agrega una nueva fila de partida |
| Botón - | QPushButton | — | Elimina la última fila |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| INV-12 | Al menos una partida | No permite registrar movimientos vacíos |
| INV-13 | Cantidad > 0 | Cada partida debe tener cantidad mayor a cero |
| INV-14 | Stock insuficiente | Para salidas: valida que `stock_actual >= cantidad` por cada insumo. Si no alcanza, muestra error con nombre del insumo, disponible y solicitado |
| INV-15 | Folio automático | Se genera `MVI-0001`, `MVI-0002`, etc. |
| INV-16 | Kardex | Por cada partida se inserta un registro en `movimiento_inventario` |
| INV-17 | Descuento de stock | Por cada partida se decrementa `stock_actual` del insumo |
| INV-18 | Cambio de ubicación | Se trata igual que una salida: descuenta stock |
| INV-19 | Impresión | Después de registrar, pregunta si desea imprimir. Genera PDF estilo orden de compra con logo, marca GORETTI, folio, fecha, tipo, tabla de partidas y pie de página |

---

## 1.5 Documento de Movimiento (PDF)

### Descripción
Documento PDF generado al imprimir un movimiento de inventario. Estilo similar a las órdenes de compra: encabezado con logo, marca GORETTI, folio, fecha, tipo de movimiento, tabla de partidas numeradas y pie de página.

### Contenido del documento

| Sección | Contenido |
|---|---|
| Encabezado izquierdo | Logo + marca "GORETTI" + "Sistema Integral de Administración y Control" |
| Encabezado centro | "DOCUMENTO DE MOVIMIENTO" + tipo (Salida/Cambio de Ubicación) |
| Encabezado derecho | Folio `MVI-XXXX` + Fecha |
| Observaciones | Bloque destacado si hay observaciones generales |
| Tabla de partidas | #, Código, Nombre, Cantidad, Unidad, Observaciones |
| Total | Total de partidas |
| Pie de página | Marca GORETTI + "Generado por SIAC ERP el [fecha]" |

---

# PROCESO 2: ÓRDENES DE COMPRA

**Módulo:** `ordenes_compra`
**Pantalla principal:** `OrdenesCompraView`
**Permisos:** `ordenes_compra.ver`, `ordenes_compra.crear`, `ordenes_compra.editar`, `ordenes_compra.eliminar`, `ordenes_compra.exportar`

---

## 2.1 Pantalla de Órdenes de Compra

### Descripción
Pantalla con dos pestañas: "Órdenes de Compra" (listado de OCs, facturas y remisiones) y "Proveedores" (catálogo de proveedores).

### Pestaña: Órdenes de Compra

| Elemento | Tipo | Descripción |
|---|---|---|
| Tabla de OCs | GorettiTable | Columnas: Folio, Tipo, Proveedor, Fecha, Estatus, Total, Observaciones |
| Botones | Toolbar | Nueva Orden, Nueva Factura, Nueva Remisión, Ver, Recibir, Cancelar OC, Imprimir, Exportar |
| Búsqueda | QLineEdit | Búsqueda por folio, nombre/RFC proveedor, nombre/código insumo |
| Color de fila | Estilo | Filas tipo "factura" o estatus "recibida" se muestran en verde claro `#daf2d0` |

### Botones de acción

| Botón | Acción | Descripción |
|---|---|---|
| Nueva Orden | Abre `DialogOrdenCompra(tipo='orden')` | Crea una nueva orden de compra con proveedor, detalle de insumos, tallas y precios |
| Nueva Factura | Abre `DialogOrdenCompra(tipo='factura')` | Documento tipo factura: folio manual (FAC-...), no recibe inventario |
| Nueva Remisión | Abre `DialogOrdenCompra(tipo='remision')` | Remisión de compra |
| Ver | Abre `DialogVerOrden` | Visualización de solo lectura de la OC con todas sus partidas y tallas |
| Recibir | Abre `DialogRecibirOrden` | Recepción de mercancía: confirma cantidades recibidas y actualiza stock |
| Cancelar | `controller.cancelar_orden()` | Cancela OC solo si está en estatus `pendiente` |
| Imprimir | Vista previa PDF | Genera PDF del recibo de compra con tabla de tallas, subtotales, IVA |
| Exportar Excel | Guarda archivo .xlsx | Exporta detalle de OC a Excel |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| OC-01 | Folio automático | OC: `OC-0001`, Factura: folio manual (`FAC-...`), Remisión: `REM-0001` |
| OC-02 | Estatus | Solo puede ser `pendiente`, `recibida`, `cancelada` o `recibida_con_diferencias` |
| OC-03 | Cancelación | Solo se puede cancelar OC en estatus `pendiente` |
| OC-04 | Recepción | Al recibir: incrementa `stock_actual` de cada insumo y registra entrada en kardex |
| OC-05 | Total | Se calcula automáticamente: SUMA(pares × precio) por talla, o SUMA(cantidad × precio_unitario) |
| OC-06 | Tipo factura | Las facturas no generan movimiento de inventario al registrarse |
| OC-07 | Solo remisión | Checkbox que genera documento de remisión (sin precio) |

---

## 2.2 Pantalla de Proveedores

### Descripción
Pestaña dentro de Órdenes de Compra que muestra el catálogo de proveedores con sus productos asociados.

### Campos del proveedor

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| RFC | QLineEdit | Sí | Único en el sistema |
| Nombre | QLineEdit | Sí | Nombre comercial o razón social |
| Nombre Comercial | QLineEdit | No | Nombre para mostrar |
| Teléfono | QLineEdit | No | — |
| Email | QLineEdit | No | — |
| Dirección | QLineEdit | No | — |
| Productos | GorettiTable | No | Lista de insumos que provee: Material, Color, Unidad, Precio, Comentario |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| PROV-01 | RFC único | No se pueden crear dos proveedores con el mismo RFC |
| PROV-02 | Productos del proveedor | Se gestionan en el mismo diálogo: cada fila = un insumo con precio unitario |
| PROV-03 | Borrado lógico | Los proveedores se desactivan, no se eliminan |

---

## 2.3 Diálogo de Orden de Compra (`DialogOrdenCompra`)

### Descripción
Formulario modal para crear una OC. Incluye selección de proveedor, observaciones, método de pago y una tabla de detalle con insumos y matrix de tallas por cada línea.

### Campos

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| Proveedor | SearchableComboBox | No (nullable para OC) | Autocompleta con proveedores activos |
| Tipo | Determinado por botón | — | `orden`, `factura` o `remision` |
| Folio | QLineEdit (auto) | Sí | Auto-generado según tipo |
| Método de pago | QComboBox editable | Sí | Transferencia bancaria, Efectivo, Cheque, Crédito |
| Observaciones | QLineEdit | No | — |
| Solo remisión | Checkbox | No | Genera remisión sin precios |
| Detalle | GorettiTable + Matrix | Sí | Cada fila: Insumo, Botón Tallas, Cantidad, Precio Unit., Subtotal |

### Matrix de tallas (`DialogMatrizTallas`)

| Elemento | Tipo | Descripción |
|---|---|---|
| Tabla de tallas | MatrizTallasWidget | Por cada talla: pares (QSpinBox) + precio (QDoubleSpinBox) |
| Corrida rápida | Rango desde/hasta/con | Genera pares iguales en todas las tallas del rango |
| Total pares | QLabel | Suma de todos los pares |
| Importe total | QLabel | SUMA(pares × precio) por talla |

---

## 2.4 Diálogo de Recepción (`DialogRecibirOrden`)

### Descripción
Formulario para recibir una OC. Muestra el detalle de la orden con columnas de cantidad solicitada vs. cantidad recibida (editable).

### Campos

| Campo | Tipo | Descripción |
|---|---|---|
| Folio | QLabel | Folio de la OC |
| Tipo | QLabel | Tipo de documento |
| Proveedor | QLabel | Nombre del proveedor |
| Fecha | QLabel | Fecha de emisión |
| Tabla de detalle | GorettiTable | Columnas: Insumo, Proveedor, Cant. Solicitada, Cant. Recibida (editable), Precio, Subtotal |
| Aviso de diferencias | QLabel | Se muestra en rojo si hay diferencias entre solicitado y recibido |
| Confirmar Recepción | QPushButton | Procesa la recepción |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| REC-01 | Stock | Al confirmar: `stock_actual += cantidad_recibida` por cada insumo |
| REC-02 | Kardex | Se registra una entrada en `movimiento_inventario` por cada línea |
| REC-03 | Estatus | La OC cambia a `recibida` |
| REC-04 | Fecha recibido | Se registra la fecha/hora de recepción |
| REC-05 | Diferencias | El usuario puede recibir cantidades diferentes a las solicitadas |

---

# PROCESO 3: PRODUCCIÓN

**Módulo:** `produccion`
**Pantalla principal:** `ProduccionView`
**Permisos:** `produccion.ver`, `produccion.crear`, `produccion.editar`, `produccion.eliminar`, `produccion.exportar`

---

## 3.1 Pantalla de Órdenes de Producción

### Descripción
Pantalla con cuatro pestañas: "Órdenes de Producción" (listado de OPs + Kanban), "Modelos" (catálogo de modelos de zapato), "BOMs" (lista de materiales por modelo), "Fichas Técnicas" (ficha técnica por modelo).

### Pestaña: Órdenes de Producción

| Elemento | Tipo | Descripción |
|---|---|---|
| Tabla de OPs | GorettiTable | Columnas: Folio, Modelo, Variante, Total Pares, Fecha Inicio, Fecha Entrega, Prioridad, Estatus |
| Kanban toggle | QPushButton | Alterna entre vista tabla y vista Kanban |
| Botones | Toolbar | Nueva OP, Ver/Avanzar, Kanban, Imprimir, Exportar |

### Botones de acción

| Botón | Acción | Descripción |
|---|---|---|
| Nueva OP | Abre `DialogOrdenProduccion` | Crea OP con variante, fechas, prioridad y matrix de tallas |
| Ver/Avanzar | Abre `DialogSeguimientoOP` | Muestra avance por estación y permite avanzar |
| Kanban | Alterna `KanbanView` | Vista drag-and-drop de OPs por estación |
| Imprimir | Vista previa PDF | Genera PDF de la OP |
| Exportar Excel | Guarda archivo .xlsx | Exporta OP a Excel |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| OP-01 | Folio automático | `OP-0001`, `OP-0002`, etc. |
| OP-02 | Estatus | `planeada` → `en_produccion` → `terminada` |
| OP-03 | Prioridad | `baja`, `normal`, `alta`, `urgente` |
| OP-04 | Total pares | Se calcula automáticamente de la matrix de tallas |
| OP-05 | Seguimiento | Al crear OP, se generan automáticamente filas de seguimiento para cada estación activa |
| OP-06 | Consumo de material | Al avanzar la primera estación, se descuenta automáticamente los insumos del BOM |
| OP-07 | Producto terminado | Al completar la última estación, se genera registro en `inventario_pt` |

---

## 3.2 Kanban de Producción

### Descripción
Vista drag-and-drop que muestra las OPs organizadas por estación de producción. Las columnas representan las estaciones: Planeada → Corte → Pespunte → Montado → Ensuelado → Acabado → Empaque → Terminada.

### Elementos

| Elemento | Tipo | Descripción |
|---|---|---|
| Columnas | _KanbanColumn | Una por estación + "Planeada" y "Terminada" |
| Tarjetas | _KanbanCard | Cada OP: folio, modelo, total pares, estatus, color por prioridad |
| Drag-and-drop | Qt Drag | Mover tarjeta = avanzar OP a esa estación |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| KAN-01 | Solo avance | No se puede mover una OP a una estación anterior |
| KAN-02 | Movimiento completo | Arrastrar a una estación intermedia avanza todas las estaciones anteriores |
| KAN-03 | Consumo | Si se arrastra desde "Planeada", se consumen los materiales al pasar por la primera estación |
| KAN-04 | Finalización | Si se arrastra hasta "Terminada", se completa toda la cadena y se genera producto terminado |
| KAN-05 | Terminada | Una OP terminada no se puede mover |

---

## 3.3 Diálogo de Seguimiento OP (`DialogSeguimientoOP`)

### Descripción
Muestra el avance de una OP a través de las estaciones de producción. Tabla con: Estación, Entrada, Salida, Procesados, Estatus (color-coded).

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| SEG-01 | Avance secuencial | Solo se puede avanzar a la siguiente estación |
| SEG-02 | Pares procesados | Se registra la cantidad de pares procesados en cada estación |
| SEG-03 | Pares defectuosos | Se registran pares defectuosos (no descuentan del total) |
| SEG-04 | Consumo automático | Primera estación → descuenta material del BOM |
| SEG-05 | Finalización | Última estación → OP cambia a `terminada` + se genera PT |

---

## 3.4 Diálogo de Ficha Técnica (`DialogFichaTecnica`)

### Descripción
Formulario completo para la ficha técnica de un modelo de zapato. Incluye campos de encabezado, características agrupadas por sección (Corte, Bordados, Accesorios, Suela y estructura, Empaque, Otros) y 5 fotos (Producto, Tubo, Chinela, Talón, Suela).

### Secciones y campos

| Sección | Campos principales |
|---|---|
| Encabezado | Proyecto, Etapa, ID, Ref. Cliente, Color |
| Corte | Cintilla, Carnuza Chinela, Forro, Piel Corte 1-4, Entretela Tubo/Chinela/Talón, Rebajado Tubo/Chinela/Talón |
| Bordados | Bordado Tubo/Chinela/Calzador/Oreja/Logo, Hilo Bordado Tubo/Chinela/Calzador/Oreja/Logo/Armado/Sobrecostura |
| Accesorios | Vivo, Ribete, Estoperol, Herraje, Acc 1-4 |
| Suela y Estructura | Puntera, Planta, Contrafuerte, Casco, Suela, Cambrellón, Cerco, Herradura, Landis, Espinazo, Firme, Tacon, Stein, Acabado, Cierre, Cantos |
| Empaque | Plantilla, Transfer, Caja, Serigrafía, Bolsa, Soporte, Asadera, Papel Relleno, Colgante |
| Otros | Grabado Suela, Barranca, Comentarios, Realizó, Recibió |
| Fotos | Producto Terminado, Tubo, Chinela, Talón, Suela (cada una con WidgetImagen) |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| FT-01 | Una ficha por modelo | Relación 1:1 con `modelos` (modelo_id es PK) |
| FT-02 | Fotos | Cada foto se almacena como BLOB; se pueden pegar o seleccionar imagen |
| FT-03 | Impresión | Genera PDF en paisaje con logo, secciones de campos y fotos embebidas |
| FT-04 | Autocompletado | Todos los campos usan histórico de capturas para autocompletar |

---

## 3.5 Diálogo de BOM (`DialogBOM`)

### Descripción
Formulario para editar la Lista de Materiales (BOM) de un modelo. Tabla editable con: Insumo, Cantidad por Par, Unidad.

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| BOM-01 | Reemplazo total | Al guardar, se eliminan todas las filas existentes y se reinsertan las nuevas |
| BOM-02 | Relación con OP | El BOM se usa al crear OPs para verificar disponibilidad de materiales |
| BOM-03 | Consumo | Al avanzar la primera estación de una OP, se descuenta `cantidad_por_par × total_pares` de cada insumo |

---

# PROCESO 4: PROGRAMACIÓN SEMANAL

**Módulo:** `produccion` (usa tabla `programacion_lineas`)
**Pantalla principal:** `ProgramacionView`
**Permisos:** `produccion.ver`, `produccion.crear`, `produccion.editar`

---

## 4.1 Pantalla de Programación

### Descripción
Pantalla para planificar la producción semanal. Muestra las líneas de programación agrupadas por factor (cliente, modelo, piel, color). Semanas auto-generadas desde la semana actual hasta fin de año.

### Elementos

| Elemento | Tipo | Descripción |
|---|---|---|
| Selector de agrupación | QRadioButton | Opciones: Cliente, Modelo, Piel, Color |
| Tabla de programación | GorettiTable | Líneas agrupadas por el factor seleccionado |
| Semanas | QComboBox | Selector de semana |
| Botones | Toolbar | Programar Pedido, Buscar |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| PROG-01 | Semanas | Se auto-generan desde la semana actual hasta fin de año |
| PROG-02 | Folio_prog | Numérico secuencial: 1001, 1002, etc. |
| PROG-03 | Estatus | `programacion_incompleta` o `programado` (según cobertura del pedido) |
| PROG-04 | Sincronización | Si el total programado ≥ total del pedido, las líneas cambian a `programado` |
| PROG-05 | Eliminación | Las líneas se eliminan físicamente (hard delete) |

---

## 4.2 Diálogo de Programar Pedido (`ProgramarPedidoDialog`)

### Descripción
Formulario para asignar un pedido de cliente a una semana de programación. Selecciona cliente, modelo, semana y captura pares por talla.

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| PROG-06 | Corrida por modelo | Cada modelo dentro de un pedido se programa como una línea separada |
| PROG-07 | Pares por talla | Se capturan pares por cada talla; solo se guardan las tallas con pares > 0 |
| PROG-08 | Total | Se calcula automáticamente como suma de pares por talla |

---

# PROCESO 5: CLIENTES Y PEDIDOS

**Módulo:** `clientes`
**Pantalla principal:** `ClientesView`
**Permisos:** `clientes.ver`, `clientes.crear`, `clientes.editar`, `clientes.eliminar`, `clientes.exportar`

---

## 5.1 Pantalla de Pedidos

### Descripción
Pantalla con dos pestañas: "Pedidos" (listado de pedidos de clientes) y "Clientes" (catálogo de clientes).

### Pestaña: Pedidos

| Elemento | Tipo | Descripción |
|---|---|---|
| Tabla de pedidos | GorettiTable | Columnas: Folio, Cliente, Fecha, Total Pares, Estatus, Observaciones |
| Botones | Toolbar | Nuevo Pedido, Buscar |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| PED-01 | Folio automático | `PED-0001`, `PED-0002`, etc. |
| PED-02 | Estatus | `pendiente` → `programado` → `surtido` o `cancelado` |
| PED-03 | Cancelación | No se puede cancelar un pedido en estatus `surtido` |
| PED-04 | Total pares | Se calcula automáticamente de la suma de pares por talla en todos los detalles |
| PED-05 | Detalle | Cada línea: modelo, piel, color + matrix de tallas (pares por talla) |

---

## 5.2 Pantalla de Clientes

### Descripción
Catálogo de clientes con CRUD básico.

### Campos del cliente

| Campo | Tipo | Obligatorio | Regla |
|---|---|---|---|
| RFC | QLineEdit | No | Nullable para clientes (a diferencia de proveedores) |
| Nombre | QLineEdit | Sí | Nombre o razón social |
| Nombre Comercial | QLineEdit | No | Nombre para mostrar |
| Teléfono | QLineEdit | No | — |
| Email | QLineEdit | No | — |
| Dirección | QLineEdit | No | — |

---

# PROCESO 6: CONFIGURACIÓN DEL SISTEMA

**Módulo:** `configuracion`
**Pantalla principal:** `ConfiguracionView`
**Permisos:** `configuracion.ver`, `configuracion.crear`, `configuracion.editar`, `configuracion.eliminar`

---

## 6.1 Pantalla de Configuración

### Descripción
Pantalla con secciones de configuración, cada una con su propia tabla y toolbar de CRUD. Secciones: Unidades de Medida, Áreas de Trabajo, Tallas, Colores, Usuarios, Impresión.

### Secciones

| Sección | Tabla | Campos | Reglas especiales |
|---|---|---|---|
| Unidades de Medida | `unidades_medida` | Nombre, Abreviatura | Ambos únicos; 8 precargadas |
| Áreas de Trabajo | `areas_trabajo` | Nombre, Descripción | — |
| Tallas | `tallas_catalogo` | Valor de talla | RD-1: unificado puntos/tallas; sin campo `orden`; valor numérico |
| Colores | `colores_catalogo` | Nombre, Código (hex), Orden | Nombre y código únicos; 5 precargados |
| Usuarios | `usuarios` | Username, Nombre, Rol, Permisos | Ver sección 7 |
| Impresión | `etiqueta_config` | Configuración de etiquetas | Formato de etiqueta térmica |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| CFG-01 | Tallas corrida | Se generan en incrementos de medio punto (ej: 00, 00.5, 01, 01.5, ...) |
| CFG-02 | Tallas reactivación | Si una talla ya existe al generar, se reactiva (activo=1) en vez de duplicar |
| CFG-03 | Borrado lógico | Todas las entidades de configuración usan borrado lógico (activo=0) |

---

# PROCESO 7: SEGURIDAD Y ACCESOS

**Módulo:** `usuarios`
**Controlador:** `AccesosController`

---

## 7.1 Autenticación (Login)

### Descripción
Pantalla de inicio de sesión con campos de usuario y contraseña. Logo de la empresa en la parte superior.

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| SEG-01 | Usuario inicial | `admin` / `admin123` (debe cambiarse en producción) |
| SEG-02 | Contraseña | Almacenada con bcrypt; si está en texto plano (legacy), se auto-upgradea a bcrypt en el primer login exitoso |
| SEG-03 | Usuario inactivo | Los usuarios desactivados no pueden iniciar sesión |
| SEG-04 | Auditoría | Login exitoso y fallido se registran en `logs_sistema` |

---

## 7.2 Gestión de Usuarios

### Descripción
Sección dentro de Configuración para crear, editar y gestionar usuarios del sistema.

### Campos

| Campo | Tipo | Regla |
|---|---|---|
| Username | QLineEdit | Único en el sistema |
| Nombre Completo | QLineEdit | Nombre para mostrar |
| Rol | QComboBox | `admin`, `operador`, etc. |
| Contraseña | QLineEdit (password) | Almacena hash bcrypt |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| SEG-05 | Username único | No se pueden crear dos usuarios con el mismo username |
| SEG-06 | Borrado lógico | Los usuarios se desactivan, no se eliminan |
| SEG-07 | Cambio de contraseña | Se puede cambiar sin conocer la anterior (solo admin) |

---

## 7.3 Matriz de Permisos

### Descripción
Editor de permisos por usuario. Matriz de módulos × acciones.

### Módulos del sistema

| Módulo | Acciones disponibles |
|---|---|
| `ordenes_compra` | ver, crear, editar, eliminar, exportar |
| `produccion` | ver, crear, editar, eliminar, exportar |
| `inventario` | ver, crear, editar, eliminar, exportar |
| `configuracion` | ver, crear, editar, eliminar, exportar |
| `usuarios` | ver, crear, editar, eliminar, exportar |
| `clientes` | ver, crear, editar, eliminar, exportar |

### Reglas de negocio

| # | Regla | Detalle |
|---|---|---|
| SEG-08 | Admin bypass | El rol `admin` tiene TODOS los permisos automáticamente |
| SEG-09 | Reemplazo total | Al guardar permisos, se eliminan los anteriores y se insertan los nuevos |
| SEG-10 | Sandbox | El Sandbox solo es visible para el rol `admin` |

---

# REGLAS DE NEGOCIO TRANSVERSALES

---

## Folios

| Entidad | Formato | Función de generación |
|---|---|---|
| Órdenes de Compra | `OC-0001` | `siguiente_folio('ordenes_compra', 'folio', 'OC')` |
| Facturas | `FAC-...` | Captura manual |
| Remisiones | `REM-0001` | `siguiente_folio(...)` |
| Órdenes de Producción | `OP-0001` | `siguiente_folio('ordenes_produccion', 'folio', 'OP')` |
| Pedidos de Cliente | `PED-0001` | `siguiente_folio('pedidos_cliente', 'folio', 'PED')` |
| Movimientos Inventario | `MVI-0001` | `siguiente_folio('movimientos_inventario', 'folio', 'MVI')` |
| Insumos | `INS-0001` | `siguiente_folio(...)` |
| Modelos | `MOD-0001` | `siguiente_folio(...)` |
| Variantes | `VAR-0001` | `siguiente_folio(...)` |
| Programación | `1001`, `1002` | Contador numérico secuencial |

---

## Flujo de Stock

```
                    ┌─────────────────────────┐
                    │   ENTRADA DE MERCANCÍA   │
                    │   (Recepción de OC)      │
                    └────────────┬────────────┘
                                 │ stock += cantidad
                                 ▼
┌─────────────────────────────────────────────────────────┐
│                    STOCK ACTUAL                         │
│               (insumos.stock_actual)                    │
└─────────────────────────────────────────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
     ┌────────────┐    ┌────────────┐    ┌────────────┐
     │  SALIDA    │    │  AJUSTE    │    │  CONSUMO   │
     │  (Manual)  │    │  (Manual)  │    │  (Producc.)│
     │ stock -= x │    │ stock -= x │    │ stock -= x │
     └────────────┘    └────────────┘    └────────────┘
```

### Reglas de stock

| # | Regla | Detalle |
|---|---|---|
| STK-01 | Entradas | Solo se generan al recibir OC (tipo `entrada` en kardex) |
| STK-02 | Salidas | Se registran manualmente (movimiento multi-partida) o al consumir material en producción |
| STK-03 | Ajustes | Correcciones manuales de inventario |
| STK-04 | Stock negativo | El sistema permite stock en cero pero no lo valida globalmente; `consumir_insumos` usa `max(0, disponible - requerido)` |
| STK-05 | Kardex | Todo movimiento se registra en `movimiento_inventario` con tipo, cantidad, referencia y timestamp |

---

## Flujo de Producción

```
    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
    │  CORTE   │ --> │PESPUNTE  │ --> │ MONTADO  │ --> │ENSUELADO │
    └──────────┘     └──────────┘     └──────────┘     └──────────┘
                                                                    │
    ┌──────────┐     ┌──────────┐                                   │
    │ EMPAQUE  │ <-- │ ACABADO  │ <─────────────────────────────────┘
    └──────────┘     └──────────┘
         │
         ▼
    ┌──────────┐
    │TERMINADA │ → Se genera Producto Terminado (inventario_pt)
    └──────────┘
```

### Flujo completo de una OP

1. **Creación**: Se crea OP con estatus `planeada` + matrix de tallas + filas de seguimiento por estación
2. **Avance**: Al avanzar la primera estación, se descuenta materiales del BOM
3. **Producción**: Cada estación registra pares procesados y defectuosos
4. **Finalización**: Al completar la última estación, OP → `terminada` + se genera registro en `inventario_pt`

---

## Impresión y PDFs

### Regla general
**Toda función de impresión en el sistema pasa por la vista previa (`PreviewImpresion`)** antes de imprimir o exportar PDF. El usuario puede:
- Ver cómo se verá el documento
- Cambiar tamaño de página (Carta/Oficio/A4) y orientación
- Hacer zoom (50% a 200%)
- Imprimir directo a impresora
- Exportar a PDF

### Documentos que se generan

| Documento | Generador | Formato |
|---|---|---|
| Recibo de OC | `export_utils.print_orden_compra()` | Portrait/Landscape según nº de tallas |
| Pedido de Cliente | `export_utils.print_pedido_cliente()` | Portrait/Landscape según nº de puntos |
| Kardex de Insumo | `kardex_print.imprimir_kardex()` | Landscape |
| Documento de Movimiento | `movimiento_print.imprimir_movimiento_documento()` | Portrait |
| Ficha Técnica | `ficha_tecnica_print.imprimir_ficha_tecnica()` | Landscape |
| Tabla genérica | `export_utils.print_table()` | Landscape |

---

## Borrado Lógico

Todas las entidades del sistema usan borrado lógico (`activo = 0`) en vez de eliminación física:

| Entidad | Campo | Valor activo | Valor inactivo |
|---|---|---|---|
| Insumos | `activo` | 1 | 0 |
| Proveedores | `activo` | 1 | 0 |
| Modelos | `activo` | 1 | 0 |
| Variantes | `activo` | 1 | 0 |
| Usuarios | `activo` | 1 | 0 |
| Tallas | `activo` | 1 | 0 |
| Colores | `activo` | 1 | 0 |
| Estaciones | `activo` | 1 | 0 |
| Clientes | `activo` | 1 | 0 |

**Excepciones (hard delete):**
- Líneas de programación (`programacion_lineas`)
- Estaciones de producción (`estaciones_produccion`) — método `eliminar_estacion()`

---

## Auditoría

Todas las operaciones de创建, edición, eliminación y recepción se registran en la tabla `logs_sistema`:

| Campo | Descripción |
|---|---|
| `fecha` | Timestamp de la operación |
| `usuario` | Nombre del usuario que realizó la acción |
| `modulo` | Módulo afectado (inventario, ordenes_compra, produccion, etc.) |
| `accion` | Tipo de acción (crear, editar, eliminar, recibir, etc.) |
| `entidad` | Tabla afectada |
| `entidad_id` | ID del registro afectado |
| `nivel` | info, advertencia, error |
| `detalle` | Descripción legible de la acción |
| `datos` | JSON con los datos originales y nuevos |

---

# FIRMAS DE APROBACIÓN

| Rol | Nombre | Firma | Fecha |
|---|---|---|---|
| Gerente General | | | |
| Gerente de Producción | | | |
| Gerente de Compras | | | |
| Encargado de Inventario | | | |
| Area de Sistemas | | | |

---

*Documento generado por SIAC ERP — Desarrollado por Mario Felipe Luevano*
*Fecha: 17 de agosto de 2026 — Todos los derechos reservados*
