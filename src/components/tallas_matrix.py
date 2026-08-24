"""Componentes reutilizables del sistema: matriz de tallas por bloques.

Aprobado desde el Sandbox. Muestra las tallas en bloques: cada bloque tiene
una fila de encabezado (fondo negro, texto blanco) y una fila de captura.
La navegación entre celdas se hace con Enter o Tabulador y las celdas no
usan controles de flechas numéricas.

Dos usos disponibles:

Como control embebido (widget, sin diálogo):

    from src.components.tallas_matrix import MatrizTallasWidget

    w = MatrizTallasWidget(puntos)       # puntos: list[dict] con "id" y "punto"
    w.establecer_valores({"15": 42})     # precarga valores
    layout.addWidget(w)
    valores = w.obtener_valores()        # -> {"15": 42, "15.5": 0, ...}
    w.valoresCambiados.connect(fn)       # se emite al editar una celda
    w.celdaSeleccionada.connect(fn)      # se emite al terminar de editar (str)

Como diálogo:

    from src.components import obtener_componente

    MatrizTallas = obtener_componente("matriz_tallas")
    dlg = MatrizTallas(puntos)          # puntos: list[dict] con "id" y "punto"
    if dlg.exec():
        valores = dlg.obtener_valores()  # -> {"3": 42, "4": 0, ...} por talla

    # Con precios por talla (p. ej. en órdenes de compra / inventario):
    dlg = MatrizTallas(puntos, con_precios=True)
    dlg.establecer_precios({"3": 25.5})
    if dlg.exec():
        pares = dlg.obtener_valores()     # {"3": 42, ...}
        precios = dlg.obtener_precios()   # {"3": 25.5, ...}

También acepta filas del catálogo unificado `tallas_catalogo` (con "id" y
"talla"): en ese caso las celdas se indexan por el id de la talla.
"""

from functools import partial

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QDoubleValidator, QIntValidator
from PySide6.QtWidgets import (
    QComboBox, QDialog, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSpinBox, QTableWidget, QVBoxLayout, QWidget,
)

from src.models.catalogos_model import TallasModel


def _clave_talla(p: dict) -> str:
    """Clave canónica de celda: el punto/talla si existe, si no el id."""
    punto = p.get("punto")
    if punto not in (None, ""):
        return str(punto)
    return str(p.get("id", ""))


def _etiqueta_talla(p: dict) -> str:
    """Texto visible del encabezado de una talla."""
    punto = p.get("punto")
    if punto not in (None, ""):
        return str(punto)
    return str(p.get("talla", "") or "")


class CeldaMatriz(QLineEdit):
    """Celda de captura: solo números, sin borde, navegación Enter/Tab."""

    siguiente = Signal()
    anterior = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setValidator(QIntValidator(0, 100000, self))
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(34)
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
            # El evento se maneja aquí: sin aceptarlo, Qt además aplica su
            # navegación por Tab por defecto y el foco se va a otra celda.
            event.accept()
            return
        if key == Qt.Key_Backtab:
            self.anterior.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class CeldaPrecio(QLineEdit):
    """Celda de captura de precio: solo decimales, sin borde, Enter/Tab.

    Se muestra con el prefijo "$" (ver `_crear_celda_precio`): el texto de la
    celda solo contiene el número (con 2 decimales al precargar), por lo que
    `obtener_precios()` parsea sin conflictos.
    """

    siguiente = Signal()
    anterior = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setValidator(QDoubleValidator(0, 99999999, 2, self))
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumHeight(34)
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
            event.accept()
            return
        if key == Qt.Key_Backtab:
            self.anterior.emit()
            event.accept()
            return
        super().keyPressEvent(event)


class MatrizTallasWidget(QWidget):
    """Matriz de tallas por bloques reutilizable como control embebido.

    Modo por defecto: captura solo pares por talla (usado en Producción).
    Con `con_precios=True` agrega una fila de precio por talla (usado en
    Órdenes de Compra e inventario).

    Propiedades públicas (referencia directa por talla):
        tallas              list[dict]                           — datos usados.
        puntos              list[dict]                           — alias de tallas.
        encabezado_general  QLabel                               — encabezado general.
        encabezados         dict[str, QLabel]                    — encabezado por talla.
        celdas              dict[str, CeldaMatriz]               — celda de pares por talla.
        celdas_precios      dict[str, CeldaPrecio]               — celda de precio por talla.
        bloques             list[list[tuple[dict, CeldaMatriz]]] — estructura por bloque.

    Señales:
        valoresCambiados()      — se emite al editar cualquier celda.
        celdaSeleccionada(str)  — se emite al terminar de editar una celda,
                                  con el punto (talla) de esa celda.

    Métodos públicos:
        obtener_valores() -> dict[str, int]      — pares capturados por talla.
        establecer_valores(dict[str, int])       — precarga pares por talla.
        obtener_precios() -> dict[str, float]    — precios por talla (si con_precios).
        establecer_precios(dict[str, float])     — precarga precios por talla.
    """

    valoresCambiados = Signal()
    celdaSeleccionada = Signal(str)

    NEGRO = "#111827"
    COLUMNAS = 11

    def __init__(self, puntos: list[dict] | None = None, titulo: str = "TALLAS",
                 parent: QWidget | None = None,
                 tallas: list[dict] | None = None,
                 con_precios: bool = False) -> None:
        super().__init__(parent)
        self.titulo = titulo
        self.con_precios = con_precios
        filas = puntos if puntos is not None else tallas
        self.puntos = list(filas) if filas is not None else TallasModel().listar()
        self.tallas = self.puntos
        self.setMinimumHeight(30)
        self.bloques: list[list[tuple[dict, CeldaMatriz]]] = []
        self._celdas: list[CeldaMatriz] = []
        self._celdas_precio: list[CeldaPrecio] = []
        self.encabezado_general: QLabel | None = None
        self.encabezados: dict[str, QLabel] = {}
        self.celdas: dict[str, CeldaMatriz] = {}
        self.celdas_precios: dict[str, CeldaPrecio] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.encabezado_general = QLabel(self.titulo)
        self.encabezado_general.setAlignment(Qt.AlignCenter)
        self.encabezado_general.setMinimumHeight(38)
        self.encabezado_general.setStyleSheet(
            f"background-color: {self.NEGRO}; color: #ffffff; font-weight: bold;"
            " font-size: 14px; padding: 0px; border: none;"
        )
        layout.addWidget(self.encabezado_general)

        if not self.tallas:
            layout.addWidget(QLabel("No hay tallas configuradas en el sistema."))
        else:
            # Layout horizontal: matriz a la izquierda, corrida+total a la derecha
            cuerpo = QHBoxLayout()
            cuerpo.setSpacing(12)

            # -- Columna izquierda: tabla de tallas --
            izquierda = QVBoxLayout()
            izquierda.setContentsMargins(0, 0, 0, 0)
            izquierda.setSpacing(6)
            self.tabla = self._crear_matriz()
            izquierda.addWidget(self.tabla)

            hint_text = (
                "Sin controles de flechas: escriba los números directamente "
                "con el teclado. Fila 'PARES': cantidad por talla; fila "
                "'PRECIO ($)': precio por talla."
                if self.con_precios
                else "Sin controles de flechas: escriba los números directamente "
                     "con el teclado.")
            hint = QLabel(hint_text)
            hint.setStyleSheet("color: #64748b; font-size: 11px;")
            izquierda.addWidget(hint)
            izquierda.addStretch()

            cuerpo.addLayout(izquierda, 1)

            # -- Columna derecha: corrida + total --
            derecha = QVBoxLayout()
            derecha.setContentsMargins(0, 0, 0, 0)
            derecha.setSpacing(10)
            self._crear_corrida(derecha)
            self._actualizar_total()
            derecha.addStretch()

            cuerpo.addLayout(derecha, 0)
            layout.addLayout(cuerpo)

        if self._celdas:
            self._celdas[0].setFocus()

    def _crear_corrida(self, layout: QVBoxLayout) -> None:
        """Corrida rápida de tallas: panel lateral vertical."""
        if not self.tallas:
            return
        corrida_box = QGroupBox("Corrida rápida")
        corrida_box.setMinimumWidth(200)
        corrida_box.setMaximumWidth(260)
        c_layout = QVBoxLayout(corrida_box)
        c_layout.setSpacing(6)

        self.cmb_talla_desde = QComboBox()
        self.cmb_talla_hasta = QComboBox()
        for p in self.tallas:
            texto = _etiqueta_talla(p)
            self.cmb_talla_desde.addItem(texto, _clave_talla(p))
            self.cmb_talla_hasta.addItem(texto, _clave_talla(p))
        if self.cmb_talla_hasta.count() > 0:
            self.cmb_talla_hasta.setCurrentIndex(self.cmb_talla_hasta.count() - 1)

        fila_desde = QHBoxLayout()
        fila_desde.addWidget(QLabel("De:"))
        fila_desde.addWidget(self.cmb_talla_desde)
        c_layout.addLayout(fila_desde)

        fila_hasta = QHBoxLayout()
        fila_hasta.addWidget(QLabel("A:"))
        fila_hasta.addWidget(self.cmb_talla_hasta)
        c_layout.addLayout(fila_hasta)

        fila_pares = QHBoxLayout()
        fila_pares.addWidget(QLabel("Pares:"))
        self.spn_corrida = QSpinBox()
        self.spn_corrida.setRange(0, 9999)
        self.spn_corrida.setValue(10)
        self.spn_corrida.setMinimumWidth(70)
        fila_pares.addWidget(self.spn_corrida)
        c_layout.addLayout(fila_pares)

        btn_corrida = QPushButton("Aplicar")
        btn_corrida.setObjectName("btnPrimary")
        btn_corrida.clicked.connect(self._aplicar_corrida)
        c_layout.addWidget(btn_corrida)

        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("btnSecondary")
        btn_limpiar.clicked.connect(self._limpiar_tallas)
        c_layout.addWidget(btn_limpiar)

        layout.addWidget(corrida_box)

        # Tarjeta de total estilo programación semanal
        self.lbl_total = QLabel("0")
        self.lbl_total.setAlignment(Qt.AlignCenter)
        self.lbl_total.setMinimumHeight(60)
        self.lbl_total.setStyleSheet(
            "background-color: #059669; color: #ffffff; font-weight: bold;"
            " font-size: 20px; border-radius: 8px; padding: 8px;"
        )
        layout.addWidget(self.lbl_total)
        lbl_nota_total = QLabel("Total pares")
        lbl_nota_total.setAlignment(Qt.AlignCenter)
        lbl_nota_total.setStyleSheet(
            "color: #64748b; font-size: 10px; margin-top: -4px;"
        )
        layout.addWidget(lbl_nota_total)

    def _aplicar_corrida(self) -> None:
        idx_desde = self.cmb_talla_desde.currentIndex()
        idx_hasta = self.cmb_talla_hasta.currentIndex()
        if idx_desde > idx_hasta:
            idx_desde, idx_hasta = idx_hasta, idx_desde
        pares = self.spn_corrida.value()
        for i, p in enumerate(self.tallas):
            if idx_desde <= i <= idx_hasta:
                celda = self.celdas.get(_clave_talla(p))
                if celda is not None:
                    celda.setText(str(pares))
        self._actualizar_total()

    def _limpiar_tallas(self) -> None:
        for celda in self.celdas.values():
            celda.setText("0")
        for celda in self.celdas_precios.values():
            celda.setText("0")
        self._actualizar_total()

    def _actualizar_total(self) -> None:
        if not hasattr(self, "lbl_total"):
            return
        total = sum(int(celda.text().strip() or 0)
                    for celda in self.celdas.values())
        if self.con_precios:
            importe = sum(
                float(celda.text().strip() or 0) * int(self.celdas[tid].text().strip() or 0)
                for tid, celda in self.celdas_precios.items())
            self.lbl_total.setText(f"{total}  ·  ${importe:,.2f}")
        else:
            self.lbl_total.setText(str(total))

    def _etiqueta_encabezado(self, texto: str) -> QLabel:
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumSize(60, 38)
        lbl.setStyleSheet(
            f"background-color: {self.NEGRO}; color: #ffffff; font-weight: bold;"
            " font-size: 12px; padding: 0px; border: none;"
        )
        return lbl

    def _etiqueta_fila(self, texto: str) -> QLabel:
        """Etiqueta de la primera columna que indica el contenido de la fila."""
        lbl = QLabel(texto)
        lbl.setAlignment(Qt.AlignCenter)
        lbl.setMinimumHeight(34)
        lbl.setStyleSheet(
            "background-color: #f1f5f9; color: #475569; font-weight: bold;"
            " font-size: 11px; padding: 0px; border: none;"
        )
        return lbl

    def _crear_celda_precio(self) -> tuple[QWidget, CeldaPrecio]:
        """Celda de precio con prefijo "$" (formato moneda).

        El "$" es una etiqueta independiente: la celda solo guarda el número
        (p. ej. "25.50"), así la captura y el parseo quedan limpios.
        """
        celda = CeldaPrecio()
        celda.setMaximumWidth(56)
        lbl = QLabel("$")
        lbl.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        contenedor = QWidget()
        h = QHBoxLayout(contenedor)
        h.setContentsMargins(2, 0, 0, 0)
        h.setSpacing(0)
        h.addWidget(lbl)
        h.addWidget(celda)
        return contenedor, celda

    def eventFilter(self, obj, event) -> bool:
        """Navegación Tab/Backtab entre celdas del mismo tipo."""
        if event.type() == QEvent.KeyPress and event.key() in (Qt.Key_Tab, Qt.Key_Backtab):
            delta = 1 if event.key() == Qt.Key_Tab else -1
            if isinstance(obj, CeldaPrecio) and obj in self._celdas_precio:
                self._mover(self._celdas_precio.index(obj), delta, self._celdas_precio)
                event.accept()
                return True
            if isinstance(obj, CeldaMatriz) and obj in self._celdas:
                self._mover(self._celdas.index(obj), delta, self._celdas)
                event.accept()
                return True
        return super().eventFilter(obj, event)

    def _crear_matriz(self) -> QTableWidget:
        bloques_tallas = [
            self.tallas[i:i + self.COLUMNAS]
            for i in range(0, len(self.tallas), self.COLUMNAS)
        ]
        filas_por_bloque = 3 if self.con_precios else 2
        # Con precios la columna 0 es de etiquetas de fila (PARES / PRECIO ($)).
        col_inicio = 1 if self.con_precios else 0
        n_columnas = self.COLUMNAS + (1 if self.con_precios else 0)

        tabla = QTableWidget()
        tabla.setRowCount(len(bloques_tallas) * filas_por_bloque)
        tabla.setColumnCount(n_columnas)
        tabla.verticalHeader().setVisible(False)
        tabla.horizontalHeader().setVisible(False)
        tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        tabla.setSelectionMode(QTableWidget.NoSelection)
        tabla.verticalHeader().setDefaultSectionSize(34)
        tabla.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        if self.con_precios:
            tabla.setColumnWidth(0, 74)
        for c in range(col_inicio, n_columnas):
            tabla.setColumnWidth(c, 85 if self.con_precios else 60)
        tabla.setFixedHeight(tabla.rowCount() * 34 + 6)

        for b, tallas_bloque in enumerate(bloques_tallas):
            fila_encabezado = b * filas_por_bloque
            fila_captura = fila_encabezado + 1
            fila_precio = fila_encabezado + 2
            if self.con_precios:
                tabla.setCellWidget(fila_encabezado, 0, self._etiqueta_fila("TALLA"))
                tabla.setCellWidget(fila_captura, 0, self._etiqueta_fila("PARES"))
                tabla.setCellWidget(fila_precio, 0, self._etiqueta_fila("PRECIO ($)"))
            bloque: list[tuple[dict, CeldaMatriz]] = []
            for c, p in enumerate(tallas_bloque):
                col = c + col_inicio
                etiqueta = self._etiqueta_encabezado(_etiqueta_talla(p))
                tabla.setCellWidget(fila_encabezado, col, etiqueta)
                self.encabezados[_etiqueta_talla(p)] = etiqueta

                celda = CeldaMatriz()
                celda.installEventFilter(self)
                tabla.setCellWidget(fila_captura, col, celda)
                self.celdas[_clave_talla(p)] = celda
                celda.textChanged.connect(self._actualizar_total)
                self._celdas.append(celda)
                celda.textChanged.connect(self.valoresCambiados)
                celda.editingFinished.connect(
                    partial(self._celda_finalizada, _etiqueta_talla(p)))
                bloque.append((p, celda))

                if self.con_precios:
                    contenedor, celda_precio = self._crear_celda_precio()
                    celda_precio.installEventFilter(self)
                    tabla.setCellWidget(fila_precio, col, contenedor)
                    self.celdas_precios[_clave_talla(p)] = celda_precio
                    celda_precio.textChanged.connect(self._actualizar_total)
                    self._celdas_precio.append(celda_precio)
            self.bloques.append(bloque)

        for i, celda in enumerate(self._celdas):
            celda.siguiente.connect(partial(self._mover, i, 1, self._celdas))
            celda.anterior.connect(partial(self._mover, i, -1, self._celdas))
        for i, celda in enumerate(self._celdas_precio):
            celda.siguiente.connect(partial(self._mover, i, 1, self._celdas_precio))
            celda.anterior.connect(partial(self._mover, i, -1, self._celdas_precio))

        return tabla

    def _celda_finalizada(self, punto) -> None:
        self.celdaSeleccionada.emit(str(punto))

    def _mover(self, indice: int, delta: int, celdas) -> None:
        siguiente = celdas[(indice + delta) % len(celdas)]
        siguiente.setFocus()
        siguiente.selectAll()

    def obtener_valores(self) -> dict[str, int]:
        """Devuelve los valores capturados por talla (los vacíos como 0)."""
        return {
            talla_id: int(celda.text().strip() or 0)
            for talla_id, celda in self.celdas.items()
        }

    def establecer_valores(self, valores: dict) -> None:
        """Precarga valores por talla (acepta clave str o int)."""
        for talla_id, valor in valores.items():
            celda = self.celdas.get(str(talla_id))
            if celda is not None:
                celda.setText(str(int(valor)))

    def obtener_precios(self) -> dict[str, float]:
        """Devuelve los precios capturados por talla (los vacíos como 0)."""
        return {
            talla_id: float(celda.text().strip() or 0)
            for talla_id, celda in self.celdas_precios.items()
        }

    def establecer_precios(self, precios: dict) -> None:
        """Precarga precios por talla (acepta clave str o int)."""
        for talla_id, valor in precios.items():
            celda = self.celdas_precios.get(str(talla_id))
            if celda is not None:
                celda.setText(f"{float(valor):.2f}")


class MatrizTallasDialog(QDialog):
    """Matriz de tallas por bloques presentada como diálogo.

    Envuelve `MatrizTallasWidget` y conserva la API pública de la versión
    anterior (puntos, encabezado_general, encabezados, celdas, bloques,
    obtener_valores, establecer_valores). Con `con_precios=True` agrega la
    captura de precio por talla (usado en Órdenes de Compra e inventario).
    """

    def __init__(self, puntos: list[dict] | None = None, titulo: str = "TALLAS",
                 parent: QWidget | None = None,
                 tallas: list[dict] | None = None,
                 con_precios: bool = False) -> None:
        super().__init__(parent)
        self.titulo = titulo
        self.con_precios = con_precios
        self.setWindowTitle("Controles de tallas")
        self.setModal(True)
        # Con precios se agregan la columna de etiquetas de fila y el prefijo
        # "$", por lo que la matriz necesita más ancho.
        self.resize(1060, 520) if con_precios else self.resize(720, 480)
        self.widget = MatrizTallasWidget(
            puntos=puntos, titulo=titulo, parent=self, tallas=tallas,
            con_precios=con_precios)
        self.puntos = self.widget.puntos
        self.tallas = self.widget.tallas
        self.bloques = self.widget.bloques
        self.encabezado_general = self.widget.encabezado_general
        self.encabezados = self.widget.encabezados
        self.celdas = self.widget.celdas
        self.celdas_precios = self.widget.celdas_precios
        self.tabla = getattr(self.widget, "tabla", None)
        self.lbl_total = self.widget.lbl_total
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

        layout.addWidget(self.widget, 1)

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

    def obtener_valores(self) -> dict[str, int]:
        return self.widget.obtener_valores()

    def establecer_valores(self, valores: dict[str, int]) -> None:
        self.widget.establecer_valores(valores)

    def obtener_precios(self) -> dict[str, float]:
        return self.widget.obtener_precios()

    def establecer_precios(self, precios: dict[str, float]) -> None:
        self.widget.establecer_precios(precios)

    def _limpiar_tallas(self) -> None:
        self.widget._limpiar_tallas()

    def _mostrar_resumen(self) -> None:
        partes = []
        for b, bloque in enumerate(self.bloques, start=1):
            valores = " | ".join(celda.text().strip() or "0"
                                 for _p, celda in bloque)
            partes.append(f"Bloque {b}: {valores}")
        QMessageBox.information(self, "Captura", "\n\n".join(partes))
