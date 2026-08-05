from PySide6.QtWidgets import QHeaderView, QTableWidget


def configurar_tabla_excel(table: QTableWidget) -> None:
    """Permite redimensionar columnas y filas al estilo Excel:
    arrastrando el borde de la cabecera o con doble clic (ajuste automático)."""
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        header.setSectionResizeMode(col, QHeaderView.Interactive)
    header.setStretchLastSection(True)
    table.verticalHeader().setSectionResizeMode(QHeaderView.Interactive)
