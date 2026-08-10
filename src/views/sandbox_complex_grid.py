"""Demo del componente aprobado ComplexGrid (código fuente en `src/components/`).

El Sandbox ya no es dueño de la implementación: esta demo solo usa el
componente aprobado vía el catálogo (`obtener_componente("complexGrid")`).
"""

from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from src.components import obtener_componente
from src.models.inventario_model import InsumoModel

ComplexGrid = obtener_componente("complexGrid")


class ComplexGridDemo(QDialog):
    """Demo del componente aprobado ComplexGrid con datos reales de insumos."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ComplexGrid — demo del componente aprobado")
        self.resize(1080, 620)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(12)

        titulo = QLabel("ComplexGrid (componente aprobado)")
        titulo.setObjectName("sectionTitle")
        lay.addWidget(titulo)

        subtitulo = QLabel(
            "Búsqueda, filtros, agrupación, vistas lista/iconos/tabla, "
            "acciones por registro y exportación Excel/PDF/Imprimir.")
        subtitulo.setObjectName("sectionSubtitle")
        lay.addWidget(subtitulo)

        self.grid = ComplexGrid()
        self.grid.set_columnas([
            {"key": "codigo", "titulo": "Código", "ancho": 100},
            {"key": "nombre", "titulo": "Insumo", "ancho": 240},
            {"key": "categoria", "titulo": "Categoría", "ancho": 150},
            {"key": "unidad_medida", "titulo": "Unidad", "ancho": 90},
            {"key": "stock_actual", "titulo": "Stock", "ancho": 90, "tipo": "numero"},
            {"key": "stock_minimo", "titulo": "Stock mín.", "ancho": 90, "tipo": "numero"},
        ])
        self.grid.set_renderers(
            fila=lambda r: [r["codigo"], r["nombre"], r["categoria"],
                            r["unidad_medida"], r["stock_actual"], r["stock_minimo"]],
            claves=lambda r: [r["codigo"], r["nombre"], r["categoria"],
                              r["unidad_medida"], r["stock_actual"], r["stock_minimo"]],
            tarjeta=lambda r: {
                "icono": "inventario",
                "color": "#ea580c",
                "titulo": r["nombre"],
                "subtitulo": f"{r['codigo']}  ·  {r['categoria']}",
                "badge": f"Stock {r['stock_actual']:.0f}",
            },
            lista=lambda r: (f"{r['codigo']} — {r['nombre']}",
                             f"{r['categoria']}  ·  {r['unidad_medida']}  ·  "
                             f"Stock {r['stock_actual']:.0f}"),
        )
        self.grid.set_acciones([
            {"texto": "Ver", "icono": "ver", "color": "#4f46e5",
             "callback": self._ver},
            {"texto": "Editar", "icono": "editar", "color": "#d97706",
             "callback": self._editar},
            {"texto": "Eliminar", "icono": "eliminar", "color": "#dc2626",
             "callback": self._eliminar},
        ])
        self.grid.set_filtros([])
        self.grid.set_agrupacion("categoria")
        self.grid.set_reporte_config({
            "titulo": "Reporte de insumos",
            "subtitulo": "Catálogo de insumos — SIAC ERP",
        })
        self.grid.set_datos(InsumoModel().listar())
        lay.addWidget(self.grid, 1)

        bar = QHBoxLayout()
        bar.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecondary")
        btn_cerrar.clicked.connect(self.accept)
        bar.addWidget(btn_cerrar)
        lay.addLayout(bar)

    def _nombre(self, rec) -> str:
        return f"{rec.get('codigo', '')} — {rec.get('nombre', '')}"

    def _ver(self, rec) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Ver", self._nombre(rec))

    def _editar(self, rec) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Editar",
                                f"{self._nombre(rec)}\nStock actual: {rec.get('stock_actual')}")

    def _eliminar(self, rec) -> None:
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Eliminar",
                                f"Acción de prueba sobre {self._nombre(rec)}")
