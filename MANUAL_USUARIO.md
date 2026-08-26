# Manual de Usuario — SIAC ERP

> Guía de uso completa para operadores y administradores del sistema.
> **Versión:** 1.0.0 — **Última actualización:** Agosto 2026

---

## Índice

1. [Bienvenida](#1-bienvenida)
2. [Instalación](#2-instalación)
3. [Inicio de sesión](#3-inicio-de-sesión)
4. [Navegación general](#4-navegación-general)
5. [Dashboard](#5-dashboard)
6. [Órdenes de Compra](#6-órdenes-de-compra)
7. [Producción](#7-producción)
8. [Inventario](#8-inventario)
9. [Clientes y Pedidos](#9-clientes-y-pedidos)
10. [Programación Semanal](#10-programación-semanal)
11. [Configuración](#11-configuración)
12. [Reportes e impresión](#12-reportes-e-impresión)
13. [Atajos de teclado](#13-atajos-de-teclado)
14. [Respaldo y restauración](#14-respaldo-y-restauración)
15. [Solución de problemas](#15-solución-de-problemas)

---

## 1. Bienvenida

**SIAC ERP** (Sistema Integral de Administración y Control) es su herramienta de gestión integral para la fábrica de calzado. Con este sistema podrá:

- ✅ Gestionar órdenes de compra y proveedores
- ✅ Controlar el inventario de materia prima
- ✅ Planificar y dar seguimiento a la producción
- ✅ Registrar clientes y pedidos
- ✅ Organizar la programación semanal
- ✅ Generar reportes en PDF y Excel
- ✅ Monitorear indicadores clave desde el Dashboard

---

## 2. Instalación

### Requisitos previos

- Windows 10 o 11 (64 bits)
- Python 3.11 o superior

### Pasos de instalación

1. **Clonar o descargar** el repositorio del sistema
2. **Abrir una terminal** en la carpeta del proyecto
3. **Crear entorno virtual:**
   ```
   py -3.11 -m venv .venv
   ```
4. **Activar entorno virtual:**
   ```
   .\.venv\Scripts\Activate.ps1
   ```
5. **Instalar dependencias:**
   ```
   pip install -r requirements.txt
   ```
6. **Copiar archivo de configuración:**
   ```
   copy config.example.ini config.ini
   ```
7. **Ejecutar el sistema:**
   ```
   python main.py
   ```

### Acceso rápido

El archivo `run.bat` lanza la aplicación directamente sin ventana de consola.

---

## 3. Inicio de sesión

Al abrir el sistema, se muestra la pantalla de login.

### Credenciales iniciales

| Campo | Valor |
|---|---|
| **Usuario** | `admin` |
| **Contraseña** | `admin123` |

### Primeros pasos después del login

1. **Cambiar la contraseña** inmediatamente:
   - Ir a **Archivo → Configuración → Usuarios y Accesos**
   - Seleccionar el usuario `admin`
   - Editar y guardar con una contraseña segura

2. **Configurar datos de empresa:**
   - Ir a **Archivo → Configuración**
   - Pestaña **Empresa**
   - Completar: nombre, RFC, dirección, teléfono, email
   - Subir logo de la empresa

---

## 4. Navegación general

### Barra de herramientas superior

La barra superior contiene los botones de navegación por módulo:

| Botón | Atajo | Módulo |
|---|---|---|
| 🏠 **Dashboard** | `Ctrl+6` | Resumen del sistema |
| 🛒 **OC** | `Ctrl+1` | Órdenes de Compra |
| 🏭 **Producción** | `Ctrl+2` | Producción y Kanban |
| 📦 **Inventario** | `Ctrl+3` | Control de insumos |
| 👥 **Clientes** | `Ctrl+4` | Clientes y Pedidos |
| 📅 **Programación** | `Ctrl+5` | Programación Semanal |
| 🧪 **Sandbox** | — | Pruebas (solo admin) |
| 🚪 **Cerrar Sesión** | — | Salir del sistema |

### Elementos comunes de la interfaz

- **Toolbar de módulo:** Botones de acción específicos del módulo actual
- **Buscador:** Filtro de búsqueda en tiempo real
- **Tabla de datos:** Lista de registros con columnas ordenables
- **Vistas:** Tabla, lista o tarjetas (iconos) — alternar con botones
- **Exportar:** Botón para exportar a Excel
- **Imprimir:** Botón para imprimir o guardar PDF

### Ajuste de columnas

En todas las tablas del sistema puede:
- **Arrastrar** el borde de una columna para ajustar su ancho
- **Hacer doble clic** en el borde para ajuste automático al contenido

---

## 5. Dashboard

El Dashboard es la pantalla de bienvenida que muestra un resumen del estado del sistema.

### Indicadores clave (KPI)

| Tarjeta | Información |
|---|---|
| **OC pendientes** | Órdenes de compra por recibir |
| **Compras del mes** | Importe total de compras en el mes actual |
| **Producción en curso** | Órdenes de producción activas |
| **Insumos stock bajo** | Materiales que requieren reposición |
| **Pares en PT** | Total de producto terminado disponible |
| **Movimientos hoy** | Movimientos de inventario registrados hoy |

### Navegación desde el Dashboard

Haga clic en cualquier tarjeta KPI para ir directamente al módulo correspondiente.

### Gráfica de compras

Muestra las compras por mes en un gráfico de barras. Los datos se actualizan con cada carga.

### Tablas de detalle

- **Últimas Órdenes de Compra:** Folio, proveedor, estatus, total y fecha
- **Órdenes de Producción en curso:** Folio, modelo, variante, pares y fecha de entrega
- **Insumos con stock bajo:** Código, nombre, stock actual y mínimo
- **Movimientos recientes:** Fecha, tipo, insumo y cantidad

### Actualizar datos

Haga clic en el botón **"Actualizar"** en la esquina superior derecha para refrescar todos los indicadores.

---

## 6. Órdenes de Compra

### 6.1 Crear una nueva orden

1. Ir a **Órdenes de Compra** (`Ctrl+1`)
2. Hacer clic en **"+ Nueva Orden"**
3. Completar los datos:
   - **Proveedor:** Seleccione del catálogo
   - **Método de pago:** Transferencia bancaria, efectivo, etc.
   - **Observaciones:** Notas adicionales (opcional)
   - **Solo remisión:** Marcar si NO aplica IVA
4. Hacer clic en **"Guardar"**

### 6.2 Agregar insumos a la orden

1. Con la orden abierta, hacer clic en **"+ Agregar Insumo"**
2. Seleccionar el insumo del catálogo
3. Ingresar:
   - **Cantidad total**
   - **Precio unitario**
4. Hacer clic en **"Configurar Tallas"** para distribuir por puntos:
   - Ingresar el rango de corrida (De punto → A punto)
   - Ingresar pares por punto
   - Hacer clic en **"Aplicar"**

### 6.3 Ingresar factura

1. Seleccionar la orden o hacer clic en **"Ingresar Factura"**
2. Capturar el **folio manualmente** (ej. `FAC-0001`)
3. La factura se guarda con tipo "factura" y se resalta en **verde claro** (`#daf2d0`)
4. Las facturas **NO se reciben en inventario**

### 6.4 Recibir orden

1. Seleccionar una orden **pendiente**
2. Hacer clic en **"Recibir Orden"**
3. Confirmar la recepción
4. El sistema actualiza automáticamente el stock de insumos
5. Se registran los movimientos de inventario correspondientes

> ⚠️ Solo se pueden recibir órdenes pendientes. Las canceladas o ya recibidas no se pueden recibir nuevamente.

### 6.5 Cancelar orden

1. Seleccionar una orden **pendiente**
2. Hacer clic en **"Cancelar"**
3. Confirmar la cancelación

> ⚠️ Solo se pueden cancelar órdenes pendientes.

### 6.6 Imprimir y exportar

- **Ver Detalle:** Abre el diálogo con toda la información de la orden
- **Imprimir PDF:** Genera un recibo profesional con formato recibo
- **Exportar Excel:** Genera un archivo `.xlsx` con el formato de la orden

### 6.7 Gestión de proveedores

En la pestaña **"Proveedores"**:

- **"+ Nuevo Proveedor":** Alta de proveedor con RFC, nombre, teléfono, email
- **Editar:** Doble clic en un proveedor
- **Nombre comercial:** Se usa como alias para identificar al proveedor

---

## 7. Producción

### 7.1 Pestañas del módulo

| Pestaña | Contenido |
|---|---|
| **Kanban** | Tablero visual de estaciones de producción |
| **Órdenes de Producción** | Lista de OPs con seguimiento |
| **Catálogos** | Modelos, Variantes y Lista de Materiales |
| **Producto Terminado** | Inventario de PT por variante × talla |

### 7.2 Catálogos

#### Modelos

1. Hacer clic en **"+ Nuevo Modelo"**
2. Completar:
   - **Código:** Identificador único del modelo
   - **Nombre:** Nombre descriptivo
   - **Descripción:** Detalles adicionales (opcional)
3. Guardar

#### Variantes

1. Seleccionar un modelo
2. Hacer clic en **"+ Nueva Variante"**
3. Completar:
   - **Color:** Del catálogo de colores
   - **Piel:** Tipo de material
   - **Talla:** Talla específica (opcional)
4. El sistema genera automáticamente el código de variante

#### Lista de Materiales (BOM)

1. Seleccionar un modelo en la tabla de modelos
2. Ir a la pestaña **"Lista de Materiales"**
3. Hacer clic en **"Editar Lista de Materiales"**
4. Agregar insumos con cantidad por par
5. Guardar

### 7.3 Ficha Técnica

1. Seleccionar un modelo
2. Hacer clic en **"Ficha Técnica"**
3. La ficha se abre en pantalla completa con:
   - **Panel izquierdo:** Datos generales, comentarios, fotos
   - **Panel derecho superior:** Características por sección
   - **Panel derecho inferior:** Materiales con costos calculados

**Características de la ficha técnica:**
- **Búsqueda de campos:** Escriba en el buscador para localizar cualquier característica
- **Costos en vivo:** El costo total por par se calcula automáticamente
- **Selección de insumos:** Al elegir un insumo del catálogo, se agrega a la tabla de materiales
- **Impresión:** Genera un formato profesional de "Hoja de especificación de diseño"

### 7.4 Órdenes de Producción

1. Hacer clic en **"+ Nueva OP"**
2. Seleccionar la variante
3. Distribuir pares por talla en la matriz
4. Establecer:
   - **Fecha de inicio**
   - **Fecha de entrega**
   - **Prioridad**
5. Guardar — el sistema genera el folio `OP-0001`

### 7.5 Tablero Kanban

El tablero Kanban muestra las órdenes de producciónorganizadas por estaciones:

| Estación | Descripción |
|---|---|
| **Corte** | Corte de piel y forro |
| **Pespunte** | Costura y ensamble del corte |
| **Montado** | Horma, plantilla y suela |
| **Ensuelado** | Pegado de suela, tacón y lijado |
| **Acabado** | Pintura, brillo y cepillado |
| **Empaque** | Control de calidad y empaquetado |

**Arrastrar órdenes:** Mueva las tarjetas entre estaciones para registrar el avance.

### 7.6 Seguimiento de producción

1. Seleccionar una OP en la tabla
2. Hacer clic en **"Ver Seguimiento"**
3. Registrar por estación:
   - **Pares procesados**
   - **Pares defectuosos**
   - **Incidencias** (opcional)
4. Avanzar a la siguiente estación

### 7.7 Producto Terminado

La pestaña **"Producto Terminado"** muestra el inventario actual por:
- Modelo
- Variante (color/piel)
- Talla
- Pares disponibles

---

## 8. Inventario

### 8.1 Pestañas del módulo

| Pestaña | Contenido |
|---|---|
| **Insumos** | Catálogo de materia prima |
| **Movimientos** | Historial de movimientos |
| **Insumos en Conflicto** | Insumos con stock bajo o crítico |

### 8.2 Gestionar insumos

#### Crear insumo

1. Hacer clic en **"+ Nuevo Insumo"**
2. Completar:
   - **Código:** Identificador único (ej. `INS-001`)
   - **Nombre:** Nombre descriptivo
   - **Categoría:** Tipo de material (piel, suela, forro, etc.)
   - **Unidad de medida:** Pieza, dm², metro, kilogramo, etc.
   - **Stock mínimo:** Nivel mínimo de alerta
3. Guardar

#### Editar insumo

- Doble clic en el insumo en la tabla
- Modificar los campos necesarios
- Guardar

#### Desactivar insumo

- Seleccionar el insumo
- Hacer clic en **"Desactivar"** (o usar la columna de acciones)
- Confirmar

> ℹ️ Los insumos se desactivan con borrado lógico; no se eliminan de la base de datos.

### 8.3 Registrar movimientos

1. Seleccionar un insumo
2. Hacer clic en **"Movimiento"**
3. Seleccionar tipo:
   - **Entrada:** Aumenta el stock
   - **Salida:** Disminuye el stock
   - **Ajuste:** Corrige el stock manualmente
4. Ingresar cantidad y observaciones
5. Guardar

### 8.4 Kardex

Para ver el historial completo de un insumo:
1. Seleccionar el insumo
2. Hacer clic en **"Kardex"** en la columna de acciones
3. Se genera un reporte con todos los movimientos

### 8.5 Insumos en conflicto

La pestaña **"Insumos en Conflicto"** muestra automáticamente los insumos cuyo stock actual es igual o menor al stock mínimo. Estos insumos requieren reposición urgente.

---

## 9. Clientes y Pedidos

### 9.1 Gestionar clientes

#### Crear cliente

1. Ir a **Clientes** (`Ctrl+4`)
2. Hacer clic en **"+ Nuevo Cliente"**
3. Completar:
   - **Nombre:** Razón social o nombre completo
   - **RFC:** Registro Federal de Contribuyentes (opcional)
   - **Nombre comercial:** Alias o nombre para facturación
   - **Teléfono, Email, Dirección**
4. Guardar

#### Editar cliente

- Doble clic en el cliente en la tabla
- Modificar campos
- Guardar

### 9.2 Crear pedidos de cliente

1. Ir a la pestaña **"Pedidos"**
2. Hacer clic en **"+ Nuevo Pedido"**
3. Seleccionar el cliente
4. Agregar detalle del pedido:
   - **Modelo**
   - **Piel**
   - **Color**
   - **Distribución por talla**
5. Establecer:
   - **Fecha programado** (opcional)
   - **Suela, Horma** (opcional)
   - **Observaciones**
6. Guardar — el sistema genera el folio `PED-0001`

### 9.3 Imprimir y exportar pedidos

- **Imprimir:** Genera el formato del pedido en vista previa
- **Exportar Excel:** Genera archivo `.xlsx` con el pedido

---

## 10. Programación Semanal

### 10.1 Concepto

La programación semanal organiza los pedidos de clientes en semanas de producción, asignando fechas y distribuyendo pares por talla.

### 10.2 Crear programación

1. Ir a **Programación** (`Ctrl+5`)
2. Seleccionar o crear una **semana**
3. Agregar líneas de programación con:
   - **Cliente**
   - **Modelo, Piel, Color**
   - **Fecha programada**
   - **Distribución por talla**
4. El sistema calcula automáticamente los totales

### 10.3 Imprimir programación

1. Seleccionar la semana o grupo
2. Hacer clic en **"Imprimir"** o **"Vista previa"**
3. Se genera el reporte con:
   - Encabezado con datos de la semana
   - Tabla por cliente/modelo con columnas por talla
   - Fila de totales por talla y gran total

### 10.4 Exportar a Excel

1. Hacer clic en **"Exportar"**
2. Seleccionar ubicación
3. Se genera archivo `.xlsx` con formato profesional

---

## 11. Configuración

### 11.1 Acceso

Ir a **Archivo → Configuración** o presionar `Ctrl+,`

### 11.2 Pestañas de configuración

| Pestaña | Contenido |
|---|---|
| **Empresa** | Nombre, RFC, logo, datos de contacto |
| **Unidades de Medida** | Catálogo de unidades (pieza, dm², metro, etc.) |
| **Áreas de Producción** | Estaciones del taller |
| **Tallas / Puntos** | Catálogo de tallas con generación en serie |
| **Colores** | Colores para variantes de producto |
| **Usuarios** | Gestión de usuarios del sistema |
| **Permisos** | Asignación de permisos por usuario |

### 11.3 Generar tallas en serie

1. Ir a **Configuración → Tallas / Puntos**
2. Usar los selectores **"Desde"** y **"Hasta"**
3. Hacer clic en **"Generar"**
4. El sistema crea automáticamente todas las tallas en el rango

### 11.4 Gestión de usuarios

#### Crear usuario

1. Ir a **Configuración → Usuarios**
2. Hacer clic en **"+ Nuevo Usuario"**
3. Completar:
   - **Nombre de usuario** (para login)
   - **Nombre completo**
   - **Contraseña**
   - **Rol** (admin u operador)
4. Guardar

#### Asignar permisos

1. Seleccionar el usuario
2. Ir a la pestaña **"Permisos"**
3. Marcar/desmarcar permisos por módulo y acción:
   - `ver` — Puede ver el módulo
   - `crear` — Puede crear registros
   - `editar` — Puede modificar registros
   - `eliminar` — Puede desactivar/cancelar
   - `exportar` — Puede exportar e imprimir
4. Guardar

---

## 12. Reportes e impresión

### 12.1 Tipos de reporte

| Reporte | Módulo | Formato |
|---|---|---|
| Recibo de OC | Órdenes de Compra | PDF / Excel |
| Ficha Técnica | Producción | PDF |
| Kardex de Insumo | Inventario | PDF |
| Pedido de Cliente | Clientes | PDF / Excel |
| Programación Semanal | Programación | PDF / Excel |
| Listados genéricos | Cualquier módulo | Excel |

### 12.2 Proceso de impresión

1. Seleccionar el registro a imprimir
2. Hacer clic en **"Imprimir"** o **"Vista previa"**
3. Se abre la **vista previa de impresión** con:
   - **Zoom:** +/- para acercar/alejar
   - **Tamaño de hoja:** Carta, Oficio
   - **Orientación:** Vertical u horizontal
   - **Imprimir:** Enviar a impresora
   - **Guardar PDF:** Exportar a archivo PDF

### 12.3 Exportar a Excel

1. Seleccionar el registro (o ninguno para exportar toda la tabla)
2. Hacer clic en **"Exportar"**
3. Seleccionar ubicación del archivo
4. Se genera el archivo `.xlsx` con formato profesional

### 12.4 Formato de reportes

Todos los reportes incluyen:
- **Membrete** con logo y nombre de la empresa
- **Folio y fecha** del documento
- **Tabla de datos** con formato profesional
- **Totales** calculados automáticamente
- **Pie de página** con mensaje de agradecimiento

---

## 13. Atajos de teclado

| Atajo | Acción |
|---|---|
| `Ctrl+1` | Ir a Órdenes de Compra |
| `Ctrl+2` | Ir a Producción |
| `Ctrl+3` | Ir a Inventario |
| `Ctrl+4` | Ir a Clientes |
| `Ctrl+5` | Ir a Programación |
| `Ctrl+6` | Ir al Dashboard |
| `Ctrl+K` | Buscador global |
| `Ctrl+,` | Configuración |
| `Enter` | Aceptar / Confirmar |
| `Escape` | Cancelar / Cerrar |
| `Tab` | Siguiente campo |
| `Shift+Tab` | Campo anterior |

### Buscador global (`Ctrl+K`)

El buscador global permite encontrar registros en cualquier módulo:
1. Presionar `Ctrl+K`
2. Escribir el término de búsqueda
3. Seleccionar el resultado deseado
4. El sistema navega automáticamente al módulo y registro

---

## 14. Respaldo y restauración

### 14.1 Respaldo manual

#### SQLite

1. **Cerrar** la aplicación completamente
2. Copiar los archivos de base de datos:
   - `goretti_erp.db`
   - `goretti_erp.db-wal` (si existe)
   - `goretti_erp.db-shm` (si existe)

#### PostgreSQL

Ejecutar en terminal:
```
pg_dump -U postgres -h localhost goretti_erp > respaldo.sql
```

### 14.2 Restauración

#### SQLite

1. Cerrar la aplicación
2. Reemplazar los archivos de base de datos con el respaldo
3. Abrir la aplicación

#### PostgreSQL

Ejecutar en terminal:
```
psql -U postgres -h localhost -d goretti_erp -f respaldo.sql
```

### 14.3 Respaldo automático

Se recomienda programar una tarea de Windows (Task Scheduler) para copiar el archivo SQLite diariamente antes de la hora de apertura del sistema.

---

## 15. Solución de problemas

### Problemas comunes

| Problema | Causa | Solución |
|---|---|---|
| **El sistema no abre** | Otra instancia está ejecutándose | Cerrar procesos de Python desde el Administrador de tareas |
| **No aparecen datos nuevos** | La BD no se ha migrado | Cerrar y volver a abrir el sistema |
| **Error "Usuario o contraseña incorrectos"** | Credenciales erróneas | Usar `admin` / `admin123` o contactar al administrador |
| **Las columnas no se ven completas** | Ancho de columna insuficiente | Arrastrar el borde de la columna o hacer doble clic |
| **La impresión sale en blanco** | Logo muy pesado | Reducir el tamaño del logo de la empresa |
| **El sistema va lento** | Base de datos grande | Contactar al administrador para optimización |
| **No puedo cancelar una OC** | La OC ya fue recibida | Solo se pueden cancelar órdenes pendientes |
| **Las facturas no aparecen en inventario** | Comportamiento normal | Las facturas NO se reciben en inventario |
| **Error al importar Excel** | Nombre de hoja incorrecto | Verificar que las hojas se llamen `DIRECTOS` y `MATERIALES ` |

### Obtener ayuda

- **Logs del sistema:** Ir a **Ayuda → Logs del Sistema** (solo admin)
- **Atajos de teclado:** Ir a **Ayuda → Atajos de Teclado**
- **Acerca de:** Ir a **Ayuda → Acerca de SIAC ERP**

### Contactar soporte

Para problemas no resueltos, contactar al equipo de desarrollo con:
1. Descripción del problema
2. Pasos para reproducir
3. Captura de pantalla (si es posible)
4. Mensajes de error (si los hay)

---

<div align="center">

**SIAC ERP** — Manual de Usuario v1.0.0

*Sistema Integral de Administración y Control*

*© 2026 Mario Felipe Luevano — Todos los derechos reservados*

</div>
