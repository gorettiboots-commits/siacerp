from PySide6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem


def configurar_tabla_excel(table: QTableWidget) -> None:
    """Permite redimensionar columnas y filas al estilo Excel:
    arrastrando el borde de la cabecera o con doble clic (ajuste automático)."""
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        header.setSectionResizeMode(col, QHeaderView.Interactive)
    header.setStretchLastSection(True)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
    # Doble clic en cabecera = auto-ajustar ancho de columna
    header.sectionDoubleClicked.connect(
        lambda logical: table.resizeColumnToContents(logical))


class NumericItem(QTableWidgetItem):
    """Ítem que ordena numéricamente (no alfabéticamente) en la tabla.

    Usar para columnas de pares/cantidades/tallas. Las celdas vacías se
    muestran vacías y ordenan como 0.
    """

    def __init__(self, valor) -> None:
        super().__init__(str(valor) if valor else "")
        self._val = float(valor) if valor else 0.0

    def __lt__(self, otro) -> bool:
        if isinstance(otro, NumericItem):
            return self._val < otro._val
        return super().__lt__(otro)
