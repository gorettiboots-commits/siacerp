# Configuración de Supabase para SIAC ERP Móvil

## Pasos para configurar Supabase

### 1. Crear el esquema de tablas

1. Ve a [Supabase Dashboard](https://supabase.com/dashboard)
2. Selecciona tu proyecto
3. Ve a **SQL Editor**
4. Copia y pega el contenido de `schema.sql`
5. Ejecuta el script

### 1.1 Ejecutar migraciones numeradas

Si es la primera vez, ejecuta en orden:

1. `001_impresiones_etiqueta.sql` - Tabla de impresion de etiquetas
2. `002_actualizar_empresa_nombre.sql` - Actualiza nombre de empresa a "EskinBoots"
3. `003_sincronizar_estatus_produccion.sql` - Vista de estatus de produccion

### 2. Desactivar confirmación de email (para desarrollo)

1. Ve a **Authentication → Settings**
2. En **Email**, desactiva **"Confirm email"**
3. Esto permite que los usuarios se logueen sin verificar su email

### 3. Crear usuario de prueba

#### Opción A: Desde el Dashboard (recomendado)

1. Ve a **Authentication → Users**
2. Haz clic en **"Add user"**
3. Completa:
   - **Email**: `operador@siac.com`
   - **Password**: `operador123`
   - **Auto Confirm User**: Sí (marcar)
4. Haz clic en **"Create user"**

#### Opción B: Desde SQL Editor

```sql
-- Crear usuario directamente (requiere service_role key)
-- NOTA: Este método NO crea el usuario en Auth, solo el perfil

-- Primero crea el usuario desde el Dashboard (Authentication → Users)
-- Luego ejecuta esto para crear el perfil:

INSERT INTO perfiles_usuario (id, username, nombre_completo, rol, activo)
VALUES (
    'UUID_DEL_USUARIO_AQUI',  -- Reemplaza con el UUID del usuario creado
    'operador',
    'Operador de Prueba',
    'operador',
    true
);
```

### 4. Configurar las credenciales en el escritorio

En `config.ini` del escritorio:

```ini
[supabase]
url = https://makeccmgamhumiktuhxh.supabase.co
anon_key = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. Configurar las credenciales en la app móvil

En `mobile/.env`:

```
EXPO_PUBLIC_SUPABASE_URL=https://makeccmgamhumiktuhxh.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Usuarios de prueba

| Email | Password | Rol | Descripción |
|---|---|---|---|
| `operador@siac.com` | `operador123` | operador | Consulta inventario, OCs, producción |
| `admin@siac.com` | `admin123` | admin | Acceso completo |

## Verificar la configuración

### Desde el escritorio

```bash
# Listar usuarios en Supabase
python scripts/crear_usuario_supabase.py --listar

# Sincronizar datos
python scripts/sincronizar_supabase.py
```

### Desde la app móvil

```bash
cd mobile
npm install
npx expo start
```

## Solución de problemas

| Problema | Causa | Solución |
|---|---|---|
| `getaddrinfo failed` | Sin conexión a internet | Verificar conexión de red |
| `Invalid login credentials` | Credenciales incorrectas | Verificar email/password |
| `Email not confirmed` | Confirmación de email activa | Desactivar en Authentication → Settings |
| `relation does not exist` | Tablas no creadas | Ejecutar schema.sql en SQL Editor |
| `permission denied` | RLS no configurado | Verificar políticas RLS |

## Flujo de autenticación

```
1. Usuario ingresa email/contraseña en la app móvil
2. La app llama a Supabase Auth (signInWithPassword)
3. Supabase verifica las credenciales
4. Si son correctas, retorna el access_token
5. La app carga el perfil desde perfiles_usuario
6. Si el perfil existe y está activo, permite el acceso
```
