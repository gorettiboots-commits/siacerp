import json
from copy import deepcopy

from src.database.db_manager import DatabaseManager

DATOS_ETIQUETA = [
    ("modelo", "Modelo"),
    ("corte", "Corte (Piel)"),
    ("color", "Color"),
    ("talla", "Talla"),
    ("folio_prog", "Folio Prog."),
    ("cliente", "Cliente"),
    ("pares", "Pares"),
    ("fecha_prog", "Fecha Prog."),
]

DEFAULT_DISENO = {
    "ancho_mm": 76.0,
    "alto_mm": 51.0,
    "campos": [
        {"tipo": "texto", "texto": "MODELO:", "x_mm": 7, "y_mm": 8,
         "size": 13, "bold": True, "visible": True},
        {"tipo": "dato", "dato": "modelo", "x_mm": 34, "y_mm": 8,
         "size": 13, "bold": False, "visible": True},
        {"tipo": "texto", "texto": "CORTE:", "x_mm": 7, "y_mm": 20,
         "size": 13, "bold": True, "visible": True},
        {"tipo": "dato", "dato": "corte", "x_mm": 34, "y_mm": 20,
         "size": 13, "bold": False, "visible": True},
        {"tipo": "texto", "texto": "COLOR:", "x_mm": 7, "y_mm": 32,
         "size": 13, "bold": True, "visible": True},
        {"tipo": "dato", "dato": "color", "x_mm": 34, "y_mm": 32,
         "size": 13, "bold": False, "visible": True},
        {"tipo": "texto", "texto": "TALLA:", "x_mm": 7, "y_mm": 42,
         "size": 14, "bold": True, "visible": True},
        {"tipo": "dato", "dato": "talla", "x_mm": 34, "y_mm": 42,
         "size": 16, "bold": True, "visible": True},
    ],
}


class EtiquetaModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def cargar_diseno(self) -> dict:
        row = self.db.fetch_one(
            "SELECT valor FROM etiqueta_config WHERE clave = 'diseno'")
        if not row:
            return deepcopy(DEFAULT_DISENO)
        try:
            diseno = json.loads(row["valor"])
        except (ValueError, TypeError):
            return deepcopy(DEFAULT_DISENO)
        if not isinstance(diseno, dict) or "campos" not in diseno:
            return deepcopy(DEFAULT_DISENO)
        base = deepcopy(DEFAULT_DISENO)
        base.update({k: v for k, v in diseno.items() if k in base})
        if isinstance(diseno.get("campos"), list):
            base["campos"] = diseno["campos"]
        return base

    def guardar_diseno(self, diseno: dict) -> None:
        self.db.execute(
            "INSERT INTO etiqueta_config (clave, valor) VALUES ('diseno', ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, "
            "updated_at = datetime('now')",
            (json.dumps(diseno, ensure_ascii=False),),
        )
