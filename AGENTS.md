# Esquema de trabajo — SIAC ERP

Este archivo define convenciones del proyecto. Leelo siempre antes de trabajar.
Viaja con el repositorio, así el esquema aplica en cualquier máquina que lo clone.

## Sandbox
`Sandbox` es el área donde se prueban controles/componentes antes de aprobarlos.

- Vista: `src/views/sandbox_view.py` (`SandboxView`), visible solo para el rol `admin`.
- Todo control experimental se desarrolla aquí, como prototipo, hasta que el
  usuario lo apruebe. Los prototipos del sandbox pueden ser código de prueba.

## Ciclo de vida de un control
1. **Prototipo en Sandbox**: la idea se desarrolla primero en `SandboxView`
   (p. ej. `DialogControlesTallas`) para probarla.
2. **Aprobar**: cuando el usuario diga **"aprobar X control de sandbox"**
   (o "aprobar X"), desarrollar el componente de forma **reutilizable** y
   agregarlo al **stack de componentes propios del sistema** en `src/components/`,
   registrándolo en el catálogo con `registrar_componente(...)`.
   El sandbox deja de ser el dueño del código: pasa a ser una demo que usa el
   componente aprobado.
3. **Listar**: cuando el usuario pida **"lista los componentes disponibles"**,
   responder con `src.components.listar_componentes()` (nombre + descripción).
4. **Usar**: cuando el usuario diga **"usa X componente en determinada tarea"**,
   importar el componente desde `src.components.obtener_componente("X")` (o con
   import directo) y aplicarlo en la tarea indicada.

## Catálogo de componentes propios
Ubicación: `src/components/__init__.py`.

- `registrar_componente(nombre, clase, descripcion)` — registra un componente
  reutilizable en el catálogo.
- `listar_componentes()` — devuelve la lista de componentes disponibles
  (nombre + descripción).
- `obtener_componente(nombre)` — devuelve la clase registrada o lanza `KeyError`.

Los componentes aprobados viven en `src/components/` o, si ya existían en
`src/utils/`, se registran en el catálogo sin duplicar código.
