from src.database.db_manager import DatabaseManager


def siguiente_folio(tabla: str, columna: str, prefijo: str, digitos: int = 4) -> str:
    """Genera el siguiente folio secuencial: PREFIJO-0001, PREFIJO-0002, ..."""
    db = DatabaseManager()
    p = f"{prefijo}-"
    maximo = 0
    for r in db.fetch_all(f'SELECT "{columna}" FROM "{tabla}"'):
        val = r[columna]
        if val and str(val).startswith(p):
            sufijo = str(val)[len(p):]
            if sufijo.isdigit():
                maximo = max(maximo, int(sufijo))
    return f"{p}{maximo + 1:0{digitos}d}"
