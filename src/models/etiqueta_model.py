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


PREFIJO_DISENO = "diseno:"


class EtiquetaModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    @staticmethod
    def _parsear_diseno(valor: str | None) -> dict | None:
        """Convierte el JSON guardado en un diseño válido (o None)."""
        if not valor:
            return None
        try:
            diseno = json.loads(valor)
        except (ValueError, TypeError):
            return None
        if not isinstance(diseno, dict) or "campos" not in diseno:
            return None
        base = deepcopy(DEFAULT_DISENO)
        base.update({k: v for k, v in diseno.items() if k in base})
        if isinstance(diseno.get("campos"), list):
            base["campos"] = diseno["campos"]
        return base

    def cargar_diseno(self) -> dict:
        row = self.db.fetch_one(
            "SELECT valor FROM etiqueta_config WHERE clave = 'diseno'")
        diseno = self._parsear_diseno(row["valor"] if row else None)
        return diseno or deepcopy(DEFAULT_DISENO)

    def guardar_diseno(self, diseno: dict) -> None:
        self.db.execute(
            "INSERT INTO etiqueta_config (clave, valor) VALUES ('diseno', ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, "
            "updated_at = datetime('now')",
            (json.dumps(diseno, ensure_ascii=False),),
        )

    # ---- Diseños nombrados (guardados en BD, sin archivos sueltos) ----

    def listar_disenos(self) -> list[dict]:
        """Diseños guardados con nombre: [{'clave', 'valor', 'updated_at'}]."""
        return self.db.fetch_all(
            "SELECT clave, valor, updated_at FROM etiqueta_config "
            "WHERE clave LIKE ? ORDER BY clave",
            (PREFIJO_DISENO + "%",),
        )

    def guardar_diseno_nombre(self, nombre: str, diseno: dict) -> None:
        self.db.execute(
            "INSERT INTO etiqueta_config (clave, valor) VALUES (?, ?) "
            "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, "
            "updated_at = datetime('now')",
            (PREFIJO_DISENO + nombre, json.dumps(diseno, ensure_ascii=False)),
        )

    def cargar_diseno_nombre(self, nombre: str) -> dict | None:
        row = self.db.fetch_one(
            "SELECT valor FROM etiqueta_config WHERE clave = ?",
            (PREFIJO_DISENO + nombre,),
        )
        return self._parsear_diseno(row["valor"] if row else None)

    def eliminar_diseno(self, nombre: str) -> None:
        self.db.execute(
            "DELETE FROM etiqueta_config WHERE clave = ?",
            (PREFIJO_DISENO + nombre,),
        )
