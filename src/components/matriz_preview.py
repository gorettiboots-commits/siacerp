"""Widget flotante de vista previa read-only de la matriz de tallas.

Se muestra al pasar el mouse sobre una celda de tipo ``matriz`` en un
`ComplexGrid`.  El widget es un `QFrame` ligero con una tabla de solo
lectura: encabezados de tallas (fondo negro, texto blanco) y una fila
de pares.

Uso (integrado automáticamente por ComplexGrid):

    # La vista registra un handler que extrae datos de tallas del registro:
    grid.set_matriz_handler(fn_que_extrae_tallas)

    # En set_columnas se marca la columna como tipo "matriz":
    grid.set_columnas([..., {"key": "corrida", "tipo": "matriz", ...}])

    # ComplexGrid instancia MatrizPreviewWidget al hacer hover sobre esa celda.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QFrame, QLabel, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)

_NEGRO = "#111827"


class MatrizPreviewWidget(QFrame):
    """Vista previa compacta y read-only de una matriz de tallas.

    Args:
        datos: ``{"corrida": "del 22 al 27", "pares": {"22": 10, "23": 12, ...}}``
        parent: Widget padre (el viewport de la tabla).
    """

    def __init__(self, datos: dict, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("matrizPreview")
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet(
            "QFrame#matrizPreview {"
            "  background-color: #ffffff; border: 1px solid #cbd5e1;"
            "  border-radius: 6px; padding: 4px;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(4)

        corrida = datos.get("corrida", "")
        if corrida:
            lbl = QLabel(corrida)
            lbl.setStyleSheet(
                "color: #475569; font-size: 11px; font-weight: bold;"
            )
            layout.addWidget(lbl)

        pares = datos.get("pares", {})
        if not pares:
            lbl = QLabel("Sin datos de tallas")
            lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            layout.addWidget(lbl)
            return

        tallas_ordenadas = sorted(
            pares.keys(),
            key=lambda t: self._valor_talla(t),
        )

        n_cols = len(tallas_ordenadas)
        COLUMNAS_BLOQUE = 11
        n_bloques = (n_cols + COLUMNAS_BLOQUE - 1) // COLUMNAS_BLOQUE
        cols_usar = min(n_cols, COLUMNAS_BLOQUE)

        from PySide6.QtWidgets import QHeaderView, QScrollArea, QWidget
        from PySide6.QtCore import Qt as QtConst

        if n_bloques <= 1:
            tabla = QTableWidget(2, n_cols)
            tabla.verticalHeader().setVisible(False)
            tabla.horizontalHeader().setVisible(False)
            tabla.setEditTriggers(QTableWidget.NoEditTriggers)
            tabla.setSelectionMode(QTableWidget.NoSelection)
            tabla.verticalHeader().setDefaultSectionSize(26)
            for c in range(n_cols):
                tabla.setColumnWidth(c, 48)
            tabla.setFixedHeight(58)
            self._llenar_tabla(tabla, tallas_ordenadas, pares, 0, n_cols)
            layout.addWidget(tabla)
        else:
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(QtConst.ScrollBarAsNeeded)
            scroll.setVerticalScrollBarPolicy(QtConst.ScrollBarAlwaysOff)
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)
            inner_layout.setContentsMargins(0, 0, 0, 0)
            inner_layout.setSpacing(6)
            for b in range(n_bloques):
                inicio = b * COLUMNAS_BLOQUE
                fin = min(inicio + COLUMNAS_BLOQUE, n_cols)
                sub_tallas = tallas_ordenadas[inicio:fin]
                sub_cols = fin - inicio
                tbl = QTableWidget(2, sub_cols)
                tbl.verticalHeader().setVisible(False)
                tbl.horizontalHeader().setVisible(False)
                tbl.setEditTriggers(QTableWidget.NoEditTriggers)
                tbl.setSelectionMode(QTableWidget.NoSelection)
                tbl.verticalHeader().setDefaultSectionSize(26)
                for c in range(sub_cols):
                    tbl.setColumnWidth(c, 48)
                tbl.setFixedHeight(58)
                self._llenar_tabla(tbl, sub_tallas, pares, 0, sub_cols)
                inner_layout.addWidget(tbl)
            scroll.setWidget(inner)
            scroll.setFixedHeight(58 * n_bloques + 12)
            scroll.setFixedWidth(COLUMNAS_BLOQUE * 48 + 20)
            layout.addWidget(scroll)

        total = sum(pares.get(t, 0) for t in tallas_ordenadas)
        if total > 0:
            total_lbl = QLabel(f"Total: {total} pares")
            total_lbl.setStyleSheet(
                "color: #1e40af; font-size: 10px; font-weight: bold;"
            )
            layout.addWidget(total_lbl)

    @staticmethod
    def _valor_talla(talla_str: str):
        try:
            return (0, float(talla_str))
        except (TypeError, ValueError):
            return (1, str(talla_str))

    @staticmethod
    def _llenar_tabla(tabla: QTableWidget, tallas: list, pares: dict,
                      col_inicio: int, n_cols: int) -> None:
        from PySide6.QtCore import Qt
        for c_offset, talla in enumerate(tallas[:n_cols]):
            col = col_inicio + c_offset
            hdr = QTableWidgetItem(str(talla))
            hdr.setTextAlignment(Qt.AlignCenter)
            hdr.setFlags(Qt.ItemIsEnabled)
            hdr.setBackground(QColor(_NEGRO))
            hdr.setForeground(QColor("#ffffff"))
            fnt = QFont()
            fnt.setBold(True)
            fnt.setPointSize(8)
            hdr.setFont(fnt)
            tabla.setItem(0, col, hdr)

            valor = pares.get(talla, 0)
            celda = QTableWidgetItem(str(valor))
            celda.setTextAlignment(Qt.AlignCenter)
            celda.setFlags(Qt.ItemIsEnabled)
            if valor > 0:
                celda.setForeground(QColor("#1e40af"))
                fnt_v = QFont()
                fnt_v.setBold(True)
                fnt_v.setPointSize(8)
                celda.setFont(fnt_v)
            else:
                celda.setForeground(QColor("#94a3b8"))
                fnt_v = QFont()
                fnt_v.setPointSize(8)
                celda.setFont(fnt_v)
            tabla.setItem(1, col, celda)
