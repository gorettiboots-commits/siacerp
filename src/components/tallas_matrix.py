"""Componente reutilizable del sistema: matriz de tallas por bloques.

Aprobado desde el Sandbox. Muestra las tallas en bloques: cada bloque tiene
una fila de encabezado (fondo negro, texto blanco) y una fila de captura.
La navegación entre celdas se hace con Enter o Tabulador y las celdas no
usan controles de flechas numéricas.

Uso:
    from src.components import obtener_componente

    MatrizTallas = obtener_componente("matriz_tallas")
    dlg = MatrizTallas(tallas)          # tallas: list[dict] con "id" y "talla"
    if dlg.exec():
        valores = dlg.obtener_valores()  # -> {"3": 42, "4": 0, ...} por talla_id
"""

from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIntValidator
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QVBoxLayout, QWidget,
)

from src.models.catalogos_model import TallasModel


class CeldaMatriz(QLineEdit):
    """Celda de captura: solo números, sin borde, navegación Enter/Tab."""

    siguiente = Signal()
    anterior = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setValidator(QIntValidator(0, 100000, self))
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(30)
        self.setMaximumWidth(80)
        self.setStyleSheet(
            "QLineEdit { border: none; background: transparent; padding: 0px;"
            " font-size: 11px; color: #1e293b; }"
            "QLineEdit:focus { background-color: #f1f5f9; }"
        )

    def keyPressEvent(self, event) -> None:
        key = event.key()
        if key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Tab):
            self.siguiente.emit()
            return
        if key == Qt.Key_Backtab:
            self.anterior.emit()
            return
        super().keyPressEvent(event)


class MatrizTallasDialog(QDialog):
    """Matriz de tallas por bloques con encabezados negros y captura por celdas.

    Propiedades públicas (referencia directa por talla):
        tallas              list[dict]                          — datos usados.
        encabezado_general  QLabel                              — encabezado general.
        encabezados         dict[str, QLabel]                   — encabezado por talla.
        celdas              dict[str, CeldaMatriz]              — celda de captura por talla.
        bloques             list[list[tuple[dict, CeldaMatriz]]] — estructura por bloque.

    Métodos públicos:
        obtener_valores() -> dict[str, int]  — valores capturados por talla_id.
        establecer_valores(dict[str, int])   — precarga valores por talla_id.
    """

    NEGRO = "#111827"
    COLUMNAS = 11

    def __init__(self, tallas: list[dict] | None = None, titulo: str = "TALLAS",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.titulo = titulo
        self.setWindowTitle("Controles de tallas")
        self.setModal(True)
        self.resize(720, 480)
        self.tallas = list(tallas) if tallas is not None else TallasModel().listar()
        self.bloques: list[list[tuple[dict, CeldaMatriz]]] = []
        self._celdas: list[CeldaMatriz] = []
        self.encabezado_general: QLabel | None = None
        self.encabezados: dict[str, QLabel] = {}
        self.celdas: dict[str, CeldaMatriz] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        titulo = QLabel("Controles de tallas")
        titulo.setObjectName("sectionTitle")
        layout.addWidget(titulo)

        subtitulo = QLabel(
            "Matriz de celdas por bloques: cada bloque tiene su fila de "
            "encabezado y su fila de captura. Navegue entre celdas con Enter "
            "o Tabulador.")
        subtitulo.setObjectName("sectionSubtitle")
        subtitulo.setWordWrap(True)
        layout.addWidget(subtitulo)

        self.encabezado_general = QLabel(self.titulo)
        self.encabezado_general.setAlignment(Qt.AlignCenter)
        self.encabezado_general.setMinimumHeight(32)
        self.encabezado_general.setStyleSheet(
            f"background-color: {self.NEGRO}; color: #ffffff; font-weight: bold;"
            " font-size: 14px; padding: 0px; border: none;"
        )
        layout.addWidget(self.encabezado_general)

        if not self.tallas:
            layout.addWidget(QLabel("No hay tallas configuradas en el sistema."))
        else:
            self.tabla = self._crear_matriz()
            layout.addWidget(self.tabla, 1)

            hint = QLabel(
                "Sin controles de flechas: escriba los números directamente "
                "con el teclado.")
            hint.setStyleSheet("color: #64748b; font-size: 11px;")
            layout.addWidget(hint)

        self._crear_corrida(layout)

        bar = QHBoxLayout()
        bar.addStretch()
        btn_capturar = QPushButton("Capturar")
        btn_capturar.setObjectName("btnPrimary")
        btn_capturar.clicked.connect(self._mostrar_resumen)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecondary")
        btn_cerrar.clicked.connect(self.accept)
        bar.addWidget(btn_capturar)
        bar.addWidget(btn_cerrar)
        layout.addLayout(bar)

        self._actualizar_total()

        if self._celdas:
            self._celdas[0].setFocus()

    def _crear_corrida(self, layout: QVBoxLayout) -> None:
        """Corrida rápida de tallas: aplica el mismo valor a un rango."""
        if not self.tallas:
            return
        corrida_box = QGroupBox("Corrida rápida de tallas")
        corrida_layout = QHBoxLayout(corrida_box)
        corrida_layout.setSpacing(8)

        corrida_layout.addWidget(QLabel("De talla:"))
        self.cmb_talla_desde = QComboBox()
        self.cmb_talla_hasta = QComboBox()
        for t in self.tallas:
            self.cmb_talla_desde.addItem(str(t["talla"]), t["id"])
            self.cmb_talla_hasta.addItem(str(t["talla"]), t["id"])
        if self.cmb_talla_hasta.count() > 0:
            self.cmb_talla_hasta.setCurrentIndex(self.cmb_talla_hasta.count() - 1)
        corrida_layout.addWidget(self.cmb_talla_desde)
        corrida_layout.addWidget(QLabel("a talla:"))
        corrida_layout.addWidget(self.cmb_talla_hasta)
        corrida_layout.addWidget(QLabel("con"))
        self.spn_corrida = QSpinBox()
        self.spn_corrida.setRange(0, 9999)
        self.spn_corrida.setValue(10)
        self.spn_corrida.setMinimumWidth(80)
        corrida_layout.addWidget(self.spn_corrida)
        corrida_layout.addWidget(QLabel("pares por talla"))

        btn_corrida = QPushButton("Aplicar Corrida")
        btn_corrida.setObjectName("btnPrimary")
        btn_corrida.clicked.connect(self._aplicar_corrida)
        corrida_layout.addWidget(btn_corrida)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("btnSecondary")
        btn_limpiar.clicked.connect(self._limpiar_tallas)
        corrida_layout.addWidget(btn_limpiar)

        layout.addWidget(corrida_box)

        self.lbl_total = QLabel("Total de pares: 0")
        self.lbl_total.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #4f46e5;")
        layout.addWidget(self.lbl_total)

    def _aplicar_corrida(self) -> None:
        idx_desde = self.cmb_talla_desde.currentIndex()
        idx_hasta = self.cmb_talla_hasta.currentIndex()
        if idx_desde > idx_hasta:
            idx_desde, idx_hasta = idx_hasta, idx_desde
        pares = self.spn_corrida.value()
        for i, t in enumerate(self.tallas):
            if idx_desde <= i <= idx_hasta:
                celda = self.celdas.get(str(t["id"]))
                if celda is not None:
                    celda.setText(str(pares))
        self._actualizar_total()

    def _limpiar_tallas(self) -> None:
        for celda in self.celdas.values():
            celda.setText("0")
        self._actualizar_total()

    def _actualizar_total(self) -> None:
        if not hasattr(self, "lbl_total"):
            return
        total = sum(int(celda.text().strip() or 0)
                    for celda in self.celdas.values())
        self.lbl_total.setText(f"Total de pares: {total}")

    def _etiqueta_encabezado(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumSize(60, 32)
        lbl.setStyleSheet(
            f"background-color: {self.NEGRO}; color: #ffffff; font-weight: bold;"
            " font-size: 12px; padding: 0px; border: none;"
        )
        return lbl

    def _crear_matriz(self) -> QTableWidget:
        bloques_tallas = [
            self.tallas[i:i + self.COLUMNAS]
            for i in range(0, len(self.tallas), self.COLUMNAS)
        ]

        tabla = QTableWidget()
        tabla.setRowCount(len(bloques_tallas) * 2)
        tabla.setColumnCount(self.COLUMNAS)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.NoSelection)
        tabla.verticalHeader().setDefaultSectionSize(32)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        for c in range(self.COLUMNAS):
            tabla.setColumnWidth(c, 60)
        tabla.setFixedHeight(tabla.rowCount() * 32 + 6)

        for b, tallas_bloque in enumerate(bloques_tallas):
            fila_encabezado = b * 2
            fila_captura = b * 2 + 1
            bloque: list[tuple[dict, CeldaMatriz]] = []
            for c, p in enumerate(tallas_bloque):
                etiqueta = self._etiqueta_encabezado(p["talla"])
                tabla.setCellWidget(fila_encabezado, c, etiqueta)
                self.encabezados[p["talla"]] = etiqueta

                celda = CeldaMatriz()
                tabla.setCellWidget(fila_captura, c, celda)
                self.celdas[str(p["id"])] = celda
                celda.textChanged.connect(self._actualizar_total)
                self._celdas.append(celda)
                bloque.append((p, celda))
            self.bloques.append(bloque)

        for i, celda in enumerate(self._celdas):
            celda.siguiente.connect(partial(self._mover, i, 1))
            celda.anterior.connect(partial(self._mover, i, -1))

        return tabla

    def _mover(self, indice: int, delta: int) -> None:
        siguiente = self._celdas[(indice + delta) % len(self._celdas)]
        siguiente.setFocus()
        siguiente.selectAll()

    def obtener_valores(self) -> dict[str, int]:
        """Devuelve los valores capturados por talla_id (los vacíos como 0)."""
        return {
            talla_id: int(celda.text().strip() or 0)
            for talla_id, celda in self.celdas.items()
        }

    def establecer_valores(self, valores: dict[str, int]) -> None:
        """Precarga valores por talla_id (acepta clave str o int)."""
        for talla_id, valor in valores.items():
            celda = self.celdas.get(str(talla_id))
            if celda is not None:
                celda.setText(str(int(valor)))

    def _mostrar_resumen(self) -> None:
        partes = []
        for b, bloque in enumerate(self.bloques, start=1):
            valores = " | ".join(celda.text().strip() or "0"
                                 for _p, celda in bloque)
            partes.append(f"Bloque {b}: {valores}")
        QMessageBox.information(self, "Captura", "\n\n".join(partes))
