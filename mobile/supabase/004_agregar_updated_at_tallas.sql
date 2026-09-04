-- Migracion 004: Agregar updated_at a programacion_linea_tallas_movil
-- La tabla existe sin esta columna pero el trigger trigger_actualizar_timestamp()
-- intenta escribir NEW.updated_at, causando error 42703.

-- Agregar la columna si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'programacion_linea_tallas_movil'
        AND column_name = 'updated_at'
    ) THEN
        ALTER TABLE programacion_linea_tallas_movil
            ADD COLUMN updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    END IF;
END $$;

-- Verificar
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'programacion_linea_tallas_movil'
ORDER BY ordinal_position;
