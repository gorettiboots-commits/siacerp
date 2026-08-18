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

ANCHO_ETIQUETA_MM = 76.0
ALTO_ETIQUETA_MM = 51.0

DEFAULT_DISENO = {
    "ancho_mm": ANCHO_ETIQUETA_MM,
    "alto_mm": ALTO_ETIQUETA_MM,
    "campos": [
        {"tipo": "dato", "dato": "modelo", "label": "MODELO:",
         "x_mm": 7, "y_mm": 8, "ancho_mm": 62, "alto_mm": 7,
         "size": 14, "label_size": 12, "bold": True, "cursiva": False,
         "alineacion": "izquierda", "borde_visible": False,
         "borde_grosor_mm": 0.3, "visible": True},
        {"tipo": "dato", "dato": "corte", "label": "CORTE:",
         "x_mm": 7, "y_mm": 18, "ancho_mm": 62, "alto_mm": 7,
         "size": 14, "label_size": 12, "bold": True, "cursiva": False,
         "alineacion": "izquierda", "borde_visible": False,
         "borde_grosor_mm": 0.3, "visible": True},
        {"tipo": "dato", "dato": "color", "label": "COLOR:",
         "x_mm": 7, "y_mm": 28, "ancho_mm": 62, "alto_mm": 7,
         "size": 14, "label_size": 12, "bold": True, "cursiva": False,
         "alineacion": "izquierda", "borde_visible": False,
         "borde_grosor_mm": 0.3, "visible": True},
        {"tipo": "dato", "dato": "talla", "label": "TALLA:",
         "x_mm": 38, "y_mm": 36, "ancho_mm": 32, "alto_mm": 10,
         "size": 22, "label_size": 10, "bold": True, "cursiva": False,
         "alineacion": "centro", "borde_visible": True,
         "borde_grosor_mm": 0.4, "visible": True},
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
