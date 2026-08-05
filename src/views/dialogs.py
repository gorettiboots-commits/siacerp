from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDateEdit, QDialog, QDoubleSpinBox,
    QFormLayout, QFrame, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QSpinBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from src.controllers.inventario_controller import InventarioController
from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.controllers.produccion_controller import ProduccionController


class DialogInsumo(QDialog):
    def __init__(self, controller: InventarioController, insumo_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.insumo_id = insumo_id
        self.setWindowTitle("Nuevo Insumo" if insumo_id is None else "Editar Insumo")
        self.setMinimumWidth(560)
        self.setModal(True)
        self._setup_ui()
        if insumo_id:
            self._load_data()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(siguiente_folio("insumos", "codigo", "INS"))
        self.txt_codigo.setPlaceholderText("Ej: INS-0001")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del insumo")
        self.txt_categoria = QLineEdit()
        self.txt_categoria.setPlaceholderText("Ej: Piel, Suela, Forro, etc.")
        self.cmb_unidad = QComboBox()
        self._cargar_unidades()
        self.spn_minimo = QDoubleSpinBox()
        self.spn_minimo.setRange(0, 999999)
        self.spn_minimo.setDecimals(2)
        self.spn_minimo.setValue(0)

        for w, lbl in [
            (self.txt_codigo, "Código:"),
            (self.txt_nombre, "Nombre:"),
            (self.txt_categoria, "Categoría:"),
            (self.cmb_unidad, "Unidad de medida:"),
            (self.spn_minimo, "Stock mínimo:"),
        ]:
            form.addRow(QLabel(lbl), w)

        layout.addLayout(form)

        self.chk_variantes = QCheckBox("Crear variantes por punto")
        self.chk_variantes.toggled.connect(self._on_puntos_toggled)
        layout.addWidget(self.chk_variantes)

        self.frame_puntos = QFrame()
        self.frame_puntos.setObjectName("card")
        fp = QVBoxLayout(self.frame_puntos)
        fp.setContentsMargins(12, 12, 12, 12)
        fp.setSpacing(8)

        sel = QHBoxLayout()
        sel.addWidget(QLabel("Desde:"))
        self.cmb_desde = QComboBox()
        self.cmb_hasta = QComboBox()
        for p in self.controller.listar_puntos():
            self.cmb_desde.addItem(p["punto"], p["punto"])
            self.cmb_hasta.addItem(p["punto"], p["punto"])
        self.cmb_hasta.setCurrentIndex(max(0, self.cmb_hasta.count() - 1))
        sel.addWidget(self.cmb_desde)
        sel.addWidget(QLabel("hasta:"))
        sel.addWidget(self.cmb_hasta)
        sel.addSpacing(8)
        btn_generar = QPushButton("Generar")
        btn_generar.setObjectName("btnPrimary")
        btn_generar.clicked.connect(self._regenerar_variantes)
        sel.addWidget(btn_generar)
        btn_limpiar = QPushButton("Limpiar")
        btn_limpiar.setObjectName("btnSecondary")
        btn_limpiar.clicked.connect(self._limpiar_variantes)
        sel.addWidget(btn_limpiar)
        sel.addStretch()
        fp.addLayout(sel)

        layout.addWidget(self.frame_puntos)
        self.frame_puntos.setVisible(False)

        self.chk_colores = QCheckBox("Variantes de color")
        self.chk_colores.toggled.connect(self._on_colores_toggled)
        layout.addWidget(self.chk_colores)

        self.frame_colores = QFrame()
        self.frame_colores.setObjectName("card")
        fc = QVBoxLayout(self.frame_colores)
        fc.setContentsMargins(12, 12, 12, 12)
        fc.setSpacing(8)
        fc.addWidget(QLabel("Seleccione los colores a generar:"))

        self._color_checks: list[tuple[QCheckBox, str]] = []
        grid = QGridLayout()
        grid.setSpacing(8)
        colores = self.controller.listar_colores()
        for i, c in enumerate(colores):
            chk = QCheckBox(f"{c['nombre']} ({c['codigo']})")
            chk.setChecked(True)
            self._color_checks.append((chk, c["codigo"]))
            grid.addWidget(chk, i // 3, i % 3)
        fc.addLayout(grid)

        layout.addWidget(self.frame_colores)
        self.frame_colores.setVisible(False)

        self.frame_preview = QFrame()
        self.frame_preview.setObjectName("card")
        fpv = QVBoxLayout(self.frame_preview)
        fpv.setContentsMargins(12, 12, 12, 12)
        fpv.setSpacing(8)
        fpv.addWidget(QLabel("Previsualización de códigos:"))
        self.lst_variantes = QListWidget()
        self.lst_variantes.setMaximumHeight(160)
        fpv.addWidget(self.lst_variantes)
        self.lbl_variantes_count = QLabel("0 variantes generadas")
        self.lbl_variantes_count.setObjectName("sectionSubtitle")
        fpv.addWidget(self.lbl_variantes_count)

        layout.addWidget(self.frame_preview)
        self.frame_preview.setVisible(False)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _on_puntos_toggled(self, checked: bool) -> None:
        self.frame_puntos.setVisible(checked)
        if not checked:
            self._limpiar_variantes()
        self._update_preview_visibility()

    def _on_colores_toggled(self, checked: bool) -> None:
        self.frame_colores.setVisible(checked)
        if not checked:
            self._limpiar_variantes()
        self._update_preview_visibility()

    def _update_preview_visibility(self) -> None:
        visible = self.chk_variantes.isChecked() or self.chk_colores.isChecked()
        self.frame_preview.setVisible(visible)

    def _puntos_seleccionados(self) -> list[str]:
        if not self.chk_variantes.isChecked():
            return []
        idx_d = self.cmb_desde.currentIndex()
        idx_h = self.cmb_hasta.currentIndex()
        if idx_d > idx_h:
            idx_d, idx_h = idx_h, idx_d
        return [self.cmb_desde.itemData(i) for i in range(idx_d, idx_h + 1)]

    def _colores_seleccionados(self) -> list[str]:
        if not self.chk_colores.isChecked():
            return []
        return [codigo for chk, codigo in self._color_checks if chk.isChecked()]

    def _regenerar_variantes(self) -> None:
        base = self.txt_codigo.text().strip()
        self.lst_variantes.clear()
        if not base:
            self._update_count()
            return
        puntos = self._puntos_seleccionados()
        colores = self._colores_seleccionados()
        if puntos and colores:
            codigos = [f"{base}-{p}-{c}" for p in puntos for c in colores]
        elif puntos:
            codigos = [f"{base}-{p}" for p in puntos]
        elif colores:
            codigos = [f"{base}-{c}" for c in colores]
        else:
            codigos = []
        for cod in codigos:
            self.lst_variantes.addItem(cod)
        self._update_count()

    def _limpiar_variantes(self) -> None:
        self.lst_variantes.clear()
        self._update_count()

    def _update_count(self) -> None:
        n = self.lst_variantes.count()
        self.lbl_variantes_count.setText(
            f"{n} variante{'s' if n != 1 else ''} generada{'s' if n != 1 else ''}")

    def _cargar_unidades(self) -> None:
        self.cmb_unidad.clear()
        for u in self.controller.listar_unidades():
            self.cmb_unidad.addItem(u["abreviatura"], u["nombre"])

    def _load_data(self) -> None:
        ins = self.controller.obtener_insumo(self.insumo_id)
        if ins:
            self.txt_codigo.setText(ins.get("codigo", ""))
            self.txt_nombre.setText(ins.get("nombre", ""))
            self.txt_categoria.setText(ins.get("categoria", ""))
            idx = self.cmb_unidad.findText(ins.get("unidad_medida", "pieza"))
            if idx >= 0:
                self.cmb_unidad.setCurrentIndex(idx)
            self.spn_minimo.setValue(ins.get("stock_minimo", 0))

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()
        categoria = self.txt_categoria.text().strip()
        if not codigo or not nombre or not categoria:
            QMessageBox.warning(self, "Campos requeridos", "Código, nombre y categoría son obligatorios.")
            return
        unidad = self.cmb_unidad.currentText()
        minimo = self.spn_minimo.value()
        variantes = [self.lst_variantes.item(i).text() for i in range(self.lst_variantes.count())]
        if variantes:
            existentes = [c for c in variantes if self.controller.existe_codigo_insumo(c)]
            if existentes:
                QMessageBox.warning(
                    self, "Códigos existentes",
                    "Los siguientes códigos ya existen en el catálogo:\n\n"
                    + "\n".join(existentes)
                    + "\n\nAjuste el código base o la lista de variantes.",
                )
                return
        if self.insumo_id:
            self.controller.actualizar_insumo(
                self.insumo_id, codigo, nombre, categoria, unidad, minimo,
            )
        else:
            self.controller.crear_insumo(codigo, nombre, categoria, unidad, minimo)
        for c in variantes:
            self.controller.crear_insumo(c, nombre, categoria, unidad, minimo)
        self.accept()


class DialogMovimientoStock(QDialog):
    def __init__(self, controller: InventarioController, insumo_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Movimiento de Inventario")
        self.setMinimumWidth(450)
        self.setModal(True)
        self.insumo_id = insumo_id
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        form = QFormLayout()
        form.setSpacing(12)

        self.cmb_insumo = QComboBox()
        insumos = self.controller.listar_insumos()
        for ins in insumos:
            self.cmb_insumo.addItem(f"{ins['codigo']} - {ins['nombre']}", ins["id"])
        if self.insumo_id:
            for i in range(self.cmb_insumo.count()):
                if self.cmb_insumo.itemData(i) == self.insumo_id:
                    self.cmb_insumo.setCurrentIndex(i)
                    break

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["entrada", "salida", "ajuste"])

        self.spn_cantidad = QDoubleSpinBox()
        self.spn_cantidad.setRange(0.01, 999999)
        self.spn_cantidad.setDecimals(2)
        self.spn_cantidad.setValue(1)

        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Motivo del movimiento (opcional)")
        self.txt_obs.setMaximumHeight(80)

        form.addRow(QLabel("Insumo:"), self.cmb_insumo)
        form.addRow(QLabel("Tipo:"), self.cmb_tipo)
        form.addRow(QLabel("Cantidad:"), self.spn_cantidad)
        form.addRow(QLabel("Observaciones:"), self.txt_obs)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Registrar Movimiento")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self) -> None:
        insumo_id = self.cmb_insumo.currentData()
        tipo = self.cmb_tipo.currentText()
        cantidad = self.spn_cantidad.value()
        obs = self.txt_obs.toPlainText().strip()
        if tipo != "entrada":
            ins = self.controller.obtener_insumo(insumo_id)
            if ins and ins["stock_actual"] < cantidad:
                QMessageBox.warning(self, "Stock insuficiente",
                    f"Stock actual: {ins['stock_actual']}. No puede registrar una salida de {cantidad}.")
                return
        self.controller.registrar_movimiento(insumo_id, tipo, cantidad, obs=obs)
        self.accept()


class DialogProveedor(QDialog):
    def __init__(self, controller: OrdenesCompraController, proveedor_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.proveedor_id = proveedor_id
        self.setWindowTitle("Nuevo Proveedor" if proveedor_id is None else "Editar Proveedor")
        self.setMinimumSize(850, 600)
        self.setModal(True)
        self._setup_ui()
        if proveedor_id:
            self._load_data()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        form = QFormLayout()
        form.setSpacing(10)

        self.txt_rfc = QLineEdit()
        self.txt_rfc.setPlaceholderText("RFC del proveedor")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre o razón social")
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Teléfono")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Correo electrónico")
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Dirección")

        for w, lbl in [
            (self.txt_rfc, "RFC:"), (self.txt_nombre, "Nombre:"),
            (self.txt_telefono, "Teléfono:"), (self.txt_email, "Email:"),
            (self.txt_direccion, "Dirección:"),
        ]:
            form.addRow(QLabel(lbl), w)

        layout.addLayout(form)

        prov_label = QLabel("¿Qué productos nos provee?")
        prov_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 6px;")
        layout.addWidget(prov_label)

        self.table_prov = QTableWidget()
        self.table_prov.setColumnCount(6)
        self.table_prov.setHorizontalHeaderLabels(
            ["Material", "Color", "Unidad", "Precio", "Comentario", "InsumoID"]
        )
        self.table_prov.setColumnHidden(5, True)
        self.table_prov.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_prov.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_prov.verticalHeader().setDefaultSectionSize(46)
        self.table_prov.setMinimumHeight(220)

        btn_add_prov = QPushButton("+ Agregar Producto")
        btn_add_prov.setObjectName("btnPrimary")
        btn_add_prov.clicked.connect(self._agregar_producto)
        btn_rm_prov = QPushButton("Quitar Seleccionado")
        btn_rm_prov.setObjectName("btnDanger")
        btn_rm_prov.clicked.connect(self._quitar_producto)

        prov_toolbar = QHBoxLayout()
        prov_toolbar.addWidget(btn_add_prov)
        prov_toolbar.addWidget(btn_rm_prov)
        prov_toolbar.addStretch()

        layout.addWidget(self.table_prov)
        layout.addLayout(prov_toolbar)

        if self.proveedor_id:
            self._cargar_insumos_proveedor()

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _cargar_insumos_proveedor(self) -> None:
        items = self.controller.listar_insumos_proveedor(self.proveedor_id)
        self.table_prov.setRowCount(len(items))
        for i, it in enumerate(items):
            self._set_fila(i, it["insumo_nombre"], it.get("color", ""),
                           it.get("unidad_medida", "pieza"), it.get("precio", 0),
                           it.get("comentario", ""), it["insumo_id"])

    def _set_fila(self, row: int, material: str, color: str, unidad: str,
                  precio: float, comentario: str, insumo_id: int) -> None:
        self.table_prov.setItem(row, 0, QTableWidgetItem(material))
        self.table_prov.setItem(row, 1, QTableWidgetItem(color))
        cmb = QComboBox()
        for u in self.controller.listar_unidades():
            cmb.addItem(u["abreviatura"], u["nombre"])
        idx = cmb.findText(unidad)
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        self.table_prov.setCellWidget(row, 2, cmb)
        spn = QDoubleSpinBox()
        spn.setRange(0, 99999999)
        spn.setDecimals(2)
        spn.setValue(precio)
        self.table_prov.setCellWidget(row, 3, spn)
        self.table_prov.setItem(row, 4, QTableWidgetItem(comentario))
        self.table_prov.setItem(row, 5, QTableWidgetItem(str(insumo_id)))

    def _agregar_producto(self) -> None:
        dlg = DialogSeleccionarInsumo(self)
        if dlg.exec() == QDialog.Accepted:
            ins = dlg.get_seleccion()
            if ins:
                for row in range(self.table_prov.rowCount()):
                    if self.table_prov.item(row, 5) and self.table_prov.item(row, 5).text() == str(ins["id"]):
                        QMessageBox.information(self, "Ya agregado",
                            f"'{ins['nombre']}' ya está en la lista.")
                        return
                row = self.table_prov.rowCount()
                self.table_prov.insertRow(row)
                self._set_fila(row, ins["nombre"], "", "pieza", 0, "", ins["id"])

    def _quitar_producto(self) -> None:
        row = self.table_prov.currentRow()
        if row >= 0:
            self.table_prov.removeRow(row)

    def _load_data(self) -> None:
        prov = self.controller.obtener_proveedor(self.proveedor_id)
        if prov:
            self.txt_rfc.setText(prov.get("rfc", ""))
            self.txt_nombre.setText(prov.get("nombre", ""))
            self.txt_telefono.setText(prov.get("telefono", ""))
            self.txt_email.setText(prov.get("email", ""))
            self.txt_direccion.setText(prov.get("direccion", ""))

    def _save(self) -> None:
        rfc = self.txt_rfc.text().strip()
        nombre = self.txt_nombre.text().strip()
        if not rfc or not nombre:
            QMessageBox.warning(self, "Campos requeridos", "RFC y nombre son obligatorios.")
            return
        if self.proveedor_id:
            self.controller.actualizar_proveedor(
                self.proveedor_id, rfc, nombre,
                self.txt_telefono.text().strip(),
                self.txt_email.text().strip(),
                self.txt_direccion.text().strip(),
            )
            proveedor_id = self.proveedor_id
        else:
            proveedor_id = self.controller.crear_proveedor(
                rfc, nombre, self.txt_telefono.text().strip(),
                self.txt_email.text().strip(), self.txt_direccion.text().strip(),
            )

        items = []
        for row in range(self.table_prov.rowCount()):
            cmb = self.table_prov.cellWidget(row, 2)
            spn = self.table_prov.cellWidget(row, 3)
            items.append({
                "insumo_id": int(self.table_prov.item(row, 5).text()),
                "color": self.table_prov.item(row, 1).text().strip(),
                "unidad": cmb.currentText() if cmb else "pieza",
                "precio": spn.value() if spn else 0,
                "comentario": self.table_prov.item(row, 4).text().strip(),
            })
        self.controller.guardar_insumos_proveedor(proveedor_id, items)
        self.accept()


class DialogMatrizTallas(QDialog):
    def __init__(self, controller: OrdenesCompraController,
                 inicial: dict[int, int] | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Matriz de Tallas")
        self.setMinimumSize(560, 400)
        self.setModal(True)
        self._matriz = dict(inicial or {})
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._puntos = self.controller.listar_puntos()
        self.spn_puntos: dict[int, QSpinBox] = {}

        filas: list[QWidget] = []
        fila = QWidget()
        fila_layout = QHBoxLayout(fila)
        fila_layout.setContentsMargins(0, 0, 0, 0)
        cols = 0
        for t in self._puntos:
            gb = QGroupBox(f"Punto {t['punto']}")
            gb.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
            vb = QVBoxLayout(gb)
            spn = QSpinBox()
            spn.setRange(0, 9999)
            spn.setValue(int(self._matriz.get(t["id"], 0)))
            spn.setMinimumHeight(34)
            spn.setStyleSheet("font-size: 14px; font-weight: bold;")
            spn.valueChanged.connect(self._actualizar_total)
            self.spn_puntos[t["id"]] = spn
            vb.addWidget(spn)
            fila_layout.addWidget(gb)
            cols += 1
            if cols % 5 == 0:
                filas.append(fila)
                fila = QWidget()
                fila_layout = QHBoxLayout(fila)
                fila_layout.setContentsMargins(0, 0, 0, 0)
        if cols % 5 != 0:
            filas.append(fila)
        for f in filas:
            layout.addWidget(f)

        corrida_box = QGroupBox("Corrida rápida de puntos")
        corrida_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        corrida_layout = QHBoxLayout(corrida_box)
        corrida_layout.setSpacing(8)

        corrida_layout.addWidget(QLabel("De punto:"))
        self.cmb_talla_desde = QComboBox()
        self.cmb_talla_hasta = QComboBox()
        for t in self._puntos:
            self.cmb_talla_desde.addItem(t["punto"], t["id"])
            self.cmb_talla_hasta.addItem(t["punto"], t["id"])
        if self.cmb_talla_hasta.count() > 0:
            self.cmb_talla_hasta.setCurrentIndex(self.cmb_talla_hasta.count() - 1)

        corrida_layout.addWidget(self.cmb_talla_desde)
        corrida_layout.addWidget(QLabel("a punto:"))
        corrida_layout.addWidget(self.cmb_talla_hasta)
        corrida_layout.addWidget(QLabel("con"))
        self.spn_corrida = QSpinBox()
        self.spn_corrida.setRange(0, 9999)
        self.spn_corrida.setValue(10)
        self.spn_corrida.setMinimumWidth(80)
        corrida_layout.addWidget(self.spn_corrida)
        corrida_layout.addWidget(QLabel("pares por punto"))

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
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px; color: #4f46e5;")
        layout.addWidget(self.lbl_total)

        self._actualizar_total()

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_aceptar = QPushButton("Aceptar")
        btn_aceptar.setObjectName("btnSuccess")
        btn_aceptar.clicked.connect(self.accept)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_aceptar)
        layout.addLayout(btns)

    def _aplicar_corrida(self) -> None:
        idx_desde = self.cmb_talla_desde.currentIndex()
        idx_hasta = self.cmb_talla_hasta.currentIndex()
        if idx_desde > idx_hasta:
            idx_desde, idx_hasta = idx_hasta, idx_desde
        pares = self.spn_corrida.value()
        for i, t in enumerate(self._puntos):
            if idx_desde <= i <= idx_hasta:
                self.spn_puntos[t["id"]].setValue(pares)

    def _limpiar_tallas(self) -> None:
        for spn in self.spn_puntos.values():
            spn.setValue(0)

    def _actualizar_total(self) -> None:
        total = sum(spn.value() for spn in self.spn_puntos.values())
        self.lbl_total.setText(f"Total de pares: {total}")

    def get_matriz(self) -> dict[int, int]:
        return {punto_id: spn.value() for punto_id, spn in self.spn_puntos.items()
                if spn.value() > 0}


class DialogOrdenCompra(QDialog):
    def __init__(self, controller: OrdenesCompraController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Nueva Orden de Compra")
        self.setMinimumSize(820, 620)
        self.setModal(True)
        self._puntos_fila: dict[int, dict[int, int]] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_proveedor = QComboBox()
        self.cmb_proveedor.addItem("Compra a inventario", None)
        for p in self.controller.listar_proveedores():
            self.cmb_proveedor.addItem(p["nombre"], p["id"])

        self.txt_folio = QLineEdit()
        self.txt_folio.setText(siguiente_folio("ordenes_compra", "folio", "OC"))
        self.txt_folio.setPlaceholderText("Ej: OC-0001")
        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")
        self.txt_obs.setMaximumHeight(60)

        self.cmb_metodo_pago = QComboBox()
        self.cmb_metodo_pago.setEditable(True)
        self.cmb_metodo_pago.addItems([
            "Transferencia bancaria", "Efectivo", "Cheque", "Crédito",
        ])

        self.chk_remision = QCheckBox("Solo remisión (sin impuestos)")

        form.addRow(QLabel("Proveedor:"), self.cmb_proveedor)
        form.addRow(QLabel("Folio:"), self.txt_folio)
        form.addRow(QLabel("Método de pago:"), self.cmb_metodo_pago)
        form.addRow(QLabel("Observaciones:"), self.txt_obs)
        layout.addLayout(form)

        layout.addWidget(self.chk_remision)

        hint = QLabel(
            "Seleccione un proveedor para comprar solo los insumos de su catálogo, "
            "o use 'Compra a inventario' para registrar insumos que no tienen proveedor asignado."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        det_label = QLabel("Detalle de la orden:")
        det_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(det_label)

        self.table_detalle = QTableWidget()
        self.table_detalle.setColumnCount(6)
        self.table_detalle.setHorizontalHeaderLabels(
            ["Insumo", "Tallas", "Cantidad", "Precio Unit.", "Subtotal", "InsumoID"]
        )
        self.table_detalle.setColumnHidden(5, True)
        self.table_detalle.horizontalHeader().setStretchLastSection(True)
        self.table_detalle.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_detalle.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_detalle.verticalHeader().setDefaultSectionSize(46)
        self.table_detalle.setMinimumHeight(200)

        btn_add = QPushButton("+ Agregar Insumo")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self._agregar_insumo)

        btn_remove = QPushButton("Quitar Seleccionado")
        btn_remove.setObjectName("btnDanger")
        btn_remove.clicked.connect(self._quitar_insumo)

        toolbar = QHBoxLayout()
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_remove)
        toolbar.addStretch()

        self.lbl_total = QLabel("Total: $0.00")
        self.lbl_total.setStyleSheet("font-size: 15px; font-weight: bold; color: #4f46e5;")
        toolbar.addWidget(self.lbl_total)

        layout.addWidget(self.table_detalle)
        layout.addLayout(toolbar)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Crear Orden")
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _agregar_insumo(self) -> None:
        proveedor_id = self.cmb_proveedor.currentData()
        dlg = DialogSeleccionarInsumo(
            self, proveedor_id=proveedor_id, sin_proveedor=(proveedor_id is None)
        )
        if dlg.exec() == QDialog.Accepted:
            insumo = dlg.get_seleccion()
            if insumo:
                for row in range(self.table_detalle.rowCount()):
                    if self.table_detalle.item(row, 5) and self.table_detalle.item(row, 5).text() == str(insumo["id"]):
                        QMessageBox.information(self, "Ya agregado",
                            f"'{insumo['nombre']}' ya está en la orden.")
                        return
                row = self.table_detalle.rowCount()
                self.table_detalle.insertRow(row)
                self._set_fila(row, insumo, proveedor_id)

    def _set_fila(self, row: int, insumo: dict, proveedor_id: int | None) -> None:
        self.table_detalle.setItem(row, 0, QTableWidgetItem(insumo["nombre"]))

        self._puntos_fila[row] = {}
        btn_tallas = QPushButton("Configurar Tallas")
        btn_tallas.setObjectName("btnSecondary")
        btn_tallas.clicked.connect(lambda _=False, r=row: self._configurar_tallas(r))
        self.table_detalle.setCellWidget(row, 1, btn_tallas)

        precio_default = 0.0
        if proveedor_id:
            for pi in self.controller.listar_insumos_proveedor_por_insumo(insumo["id"]):
                if pi["proveedor_id"] == proveedor_id:
                    precio_default = float(pi.get("precio", 0) or 0)
                    break

        spn_c = QDoubleSpinBox()
        spn_c.setRange(0, 999999)
        spn_c.setDecimals(2)
        spn_c.setValue(1)
        spn_c.valueChanged.connect(self._recalcular)
        self.table_detalle.setCellWidget(row, 2, spn_c)

        spn_p = QDoubleSpinBox()
        spn_p.setRange(0, 99999999)
        spn_p.setDecimals(2)
        spn_p.setValue(precio_default)
        spn_p.valueChanged.connect(self._recalcular)
        self.table_detalle.setCellWidget(row, 3, spn_p)

        self.table_detalle.setItem(row, 4, QTableWidgetItem(f"{precio_default:.2f}"))
        self.table_detalle.setItem(row, 5, QTableWidgetItem(str(insumo["id"])))
        self._recalcular()

    def _configurar_tallas(self, row: int) -> None:
        dlg = DialogMatrizTallas(self.controller, self._puntos_fila.get(row))
        if dlg.exec() == QDialog.Accepted:
            matriz = dlg.get_matriz()
            self._puntos_fila[row] = matriz
            total_pares = sum(matriz.values())
            btn = self.table_detalle.cellWidget(row, 1)
            if btn:
                btn.setText(f"Editar Tallas ({total_pares} pr)")
            spn_c = self.table_detalle.cellWidget(row, 2)
            if spn_c:
                spn_c.setValue(total_pares)
            self._recalcular()

    def _quitar_insumo(self) -> None:
        row = self.table_detalle.currentRow()
        if row >= 0:
            self.table_detalle.removeRow(row)
            self._puntos_fila.pop(row, None)
            self._recalcular()

    def _recalcular(self, *_args) -> None:
        total = 0.0
        for row in range(self.table_detalle.rowCount()):
            spn_c = self.table_detalle.cellWidget(row, 2)
            spn_p = self.table_detalle.cellWidget(row, 3)
            if spn_c and spn_p:
                sub = spn_c.value() * spn_p.value()
                self.table_detalle.item(row, 4).setText(f"{sub:.2f}")
                total += sub
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _save(self) -> None:
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.warning(self, "Campo requerido", "El folio es obligatorio.")
            return
        proveedor_id = self.cmb_proveedor.currentData()
        detalle = []
        for row in range(self.table_detalle.rowCount()):
            insumo_id = int(self.table_detalle.item(row, 5).text())
            spn_c = self.table_detalle.cellWidget(row, 2)
            spn_p = self.table_detalle.cellWidget(row, 3)
            puntos = self._puntos_fila.get(row, {})
            cantidad = sum(puntos.values()) if puntos else (spn_c.value() if spn_c else 0)
            precio = spn_p.value() if spn_p else 0
            if cantidad > 0:
                detalle.append({
                    "insumo_id": insumo_id,
                    "cantidad": cantidad,
                    "precio": precio,
                    "puntos": [{"punto_id": pid, "pares": pr} for pid, pr in puntos.items()],
                })
        if not detalle:
            QMessageBox.warning(self, "Detalle vacío", "Agregue al menos un insumo a la orden.")
            return
        self.controller.crear_orden(
            folio, detalle, self.txt_obs.toPlainText().strip(),
            proveedor_id=proveedor_id,
            metodo_pago=self.cmb_metodo_pago.currentText().strip(),
            solo_remision=self.chk_remision.isChecked(),
        )
        self.accept()


class DialogSeleccionarInsumo(QDialog):
    def __init__(self, parent=None, proveedor_id: int | None = None,
                 sin_proveedor: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Insumo")
        self.setMinimumSize(500, 400)
        self.setModal(True)
        self._selected = None
        self._proveedor_id = proveedor_id
        self._sin_proveedor = sin_proveedor
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar insumo...")
        layout.addWidget(self.txt_buscar)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Código", "Nombre", "Categoría", "Stock"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.doubleClicked.connect(self._accept)

        ctrl = InventarioController()
        if self._proveedor_id is not None:
            insumos = ctrl.listar_insumos_de_proveedor(self._proveedor_id)
        elif self._sin_proveedor:
            insumos = ctrl.listar_insumos_sin_proveedor()
        else:
            insumos = ctrl.listar_insumos()
        self._insumos = insumos
        self.table.setRowCount(len(insumos))
        for i, ins in enumerate(insumos):
            self.table.setItem(i, 0, QTableWidgetItem(ins["codigo"]))
            self.table.setItem(i, 1, QTableWidgetItem(ins["nombre"]))
            self.table.setItem(i, 2, QTableWidgetItem(ins["categoria"]))
            self.table.setItem(i, 3, QTableWidgetItem(str(ins["stock_actual"])))
            self.table.item(i, 0).setData(Qt.UserRole, ins["id"])

        self.txt_buscar.textChanged.connect(self._filtrar)
        layout.addWidget(self.table)

        btns = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_sel = QPushButton("Seleccionar")
        btn_sel.setObjectName("btnPrimary")
        btn_sel.clicked.connect(self._accept)
        btns.addStretch()
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_sel)
        layout.addLayout(btns)

    def _filtrar(self, texto: str) -> None:
        for row in range(self.table.rowCount()):
            match = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and texto.lower() in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def _accept(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            insumo_id = self.table.item(row, 0).data(Qt.UserRole)
            ins = next((x for x in self._insumos if x["id"] == insumo_id), None)
            if ins:
                self._selected = ins
                self.accept()

    def get_seleccion(self) -> dict | None:
        return self._selected


class DialogVerOrden(QDialog):
    def __init__(self, controller: OrdenesCompraController, oc_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.oc_id = oc_id
        self.setWindowTitle(f"Orden de Compra")
        self.setMinimumSize(650, 500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        oc = self.controller.obtener_orden(self.oc_id)
        if not oc:
            layout.addWidget(QLabel("Orden no encontrada"))
            return

        info = QFormLayout()
        info.addRow("Folio:", QLabel(oc.get("folio", "")))
        info.addRow("Proveedor:", QLabel(oc.get("proveedor_nombre") or "Compra a inventario"))
        info.addRow("Fecha:", QLabel(oc.get("fecha_emision", "")))
        info.addRow("Estatus:", QLabel(oc.get("estatus", "").capitalize()))
        info.addRow("Método de pago:", QLabel(oc.get("metodo_pago") or "Transferencia bancaria"))
        if oc.get("solo_remision"):
            info.addRow("Documento:", QLabel("Solo remisión (sin impuestos)"))
        info.addRow("Total:", QLabel(f"${oc.get('total', 0):.2f}"))
        if oc.get("observaciones"):
            info.addRow("Observaciones:", QLabel(oc["observaciones"]))
        layout.addLayout(info)

        det_label = QLabel("Detalle:")
        det_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(det_label)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Insumo", "Proveedor", "Puntos", "Cantidad", "Precio Unit.", "Subtotal"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(46)

        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        self.table.setRowCount(len(detalle))
        for i, d in enumerate(detalle):
            self.table.setItem(i, 0, QTableWidgetItem(d.get("insumo_nombre", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("proveedor_nombre", "") or "—"))
            puntos = d.get("puntos", [])
            if puntos:
                texto_puntos = ", ".join(f"P{t['punto']}: {t['pares']}" for t in puntos)
                self.table.setItem(i, 2, QTableWidgetItem(texto_puntos))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("—"))
            self.table.setItem(i, 3, QTableWidgetItem(str(d.get("cantidad", 0))))
            self.table.setItem(i, 4, QTableWidgetItem(f"${d.get('precio_unitario', 0):.2f}"))
            sub = d.get("cantidad", 0) * d.get("precio_unitario", 0)
            self.table.setItem(i, 5, QTableWidgetItem(f"${sub:.2f}"))

        layout.addWidget(self.table)

        from src.utils.export_utils import export_orden_compra_excel, print_orden_compra
        btn_print = QPushButton("Imprimir PDF")
        btn_print.setObjectName("btnPrimary")
        btn_print.clicked.connect(lambda: print_orden_compra(oc, detalle, self))

        btn_excel = QPushButton("Exportar Excel")
        btn_excel.setObjectName("btnPrimary")
        btn_excel.clicked.connect(lambda: export_orden_compra_excel(oc, detalle, self))

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        btns_row = QHBoxLayout()
        btns_row.addWidget(btn_print)
        btns_row.addWidget(btn_excel)
        btns_row.addStretch()
        btns_row.addWidget(btn_close)
        layout.addLayout(btns_row)


class DialogRecibirOrden(QDialog):
    def __init__(self, controller: 'OrdenesCompraController', oc_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.oc_id = oc_id
        self.setWindowTitle("Recibir Orden de Compra")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._diferencias = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        oc = self.controller.obtener_orden(self.oc_id)
        if not oc:
            layout.addWidget(QLabel("Orden no encontrada"))
            return

        info = QFormLayout()
        info.addRow("Folio:", QLabel(f"<b>{oc.get('folio', '')}</b>"))
        info.addRow("Proveedor:", QLabel(oc.get("proveedor_nombre") or "Compra a inventario"))
        info.addRow("Fecha:", QLabel(oc.get("fecha_emision", "")))
        layout.addLayout(info)

        instruccion = QLabel("Verifique las cantidades. Ajuste si hay diferencias:")
        instruccion.setStyleSheet("font-weight: bold; color: #475569; margin-top: 8px;")
        layout.addWidget(instruccion)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Insumo", "Proveedor", "Cant. Solicitada", "Cant. Recibida",
            "Precio Unit.", "Subtotal", "DetalleID"
        ])
        self.table.setColumnHidden(6, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(46)

        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        self._spins: list[QDoubleSpinBox] = []
        self._detalle_ids: list[int] = []
        self.table.setRowCount(len(detalle))
        for i, d in enumerate(detalle):
            cant = d.get("cantidad", 0)
            precio = d.get("precio_unitario", 0)
            self.table.setItem(i, 0, QTableWidgetItem(d.get("insumo_nombre", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("proveedor_nombre", "") or "—"))
            self.table.setItem(i, 2, QTableWidgetItem(str(cant)))
            spn = QDoubleSpinBox()
            spn.setRange(0, cant * 10)
            spn.setDecimals(2)
            spn.setValue(cant)
            spn.valueChanged.connect(self._on_cantidad_changed)
            self._spins.append(spn)
            self.table.setCellWidget(i, 3, spn)
            self.table.setItem(i, 4, QTableWidgetItem(f"${precio:.2f}"))
            sub_item = QTableWidgetItem(f"${cant * precio:.2f}")
            self.table.setItem(i, 5, sub_item)
            self.table.setItem(i, 6, QTableWidgetItem(str(d.get("id", ""))))
            self._detalle_ids.append(d.get("id", 0))

        layout.addWidget(self.table)

        self.lbl_diferencia = QLabel("")
        self.lbl_diferencia.setStyleSheet("color: #d97706; font-weight: bold;")
        layout.addWidget(self.lbl_diferencia)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_recibir = QPushButton("Confirmar Recepción")
        btn_recibir.setObjectName("btnSuccess")
        btn_recibir.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_recibir)
        layout.addLayout(btns)

    def _on_cantidad_changed(self) -> None:
        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        diferencias = False
        total = 0
        for i, d in enumerate(detalle):
            recibido = self._spins[i].value()
            solicitado = d.get("cantidad", 0)
            precio = d.get("precio_unitario", 0)
            sub = recibido * precio
            self.table.item(i, 5).setText(f"${sub:.2f}")
            total += sub
            if abs(recibido - solicitado) > 0.01:
                diferencias = True
        self._diferencias = diferencias
        if diferencias:
            self.lbl_diferencia.setText("⚠ Hay diferencias entre lo solicitado y lo recibido. "
                                         "La orden se marcará como 'recibida con diferencias'.")
        else:
            self.lbl_diferencia.setText("✓ Cantidades coinciden. Orden se marcará como 'recibida'.")

    def _save(self) -> None:
        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        for i, d in enumerate(detalle):
            recibido = self._spins[i].value()
            if recibido > 0:
                from src.database.db_manager import DatabaseManager
                db = DatabaseManager()
                db.execute(
                    "UPDATE insumos SET stock_actual = stock_actual + ?, updated_at = datetime('now') WHERE id = ?",
                    (recibido, d["insumo_id"]),
                )
                db.execute(
                    "INSERT INTO movimiento_inventario (insumo_id, tipo_movimiento, cantidad, referencia_tipo, referencia_id, observaciones) VALUES (?, 'entrada', ?, 'orden_compra', ?, ?)",
                    (d["insumo_id"], recibido, self.oc_id,
                     f"OC {d['orden_compra_id']} - Recibido: {recibido}/{d['cantidad']}"),
                )

        estatus = "recibida_con_diferencias" if self._diferencias else "recibida"
        total = sum(
            self._spins[i].value() * d.get("precio_unitario", 0)
            for i, d in enumerate(detalle)
        )
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.execute(
            "UPDATE ordenes_compra SET estatus=?, fecha_recibido=datetime('now'), total=? WHERE id=?",
            (estatus, total, self.oc_id),
        )
        self.accept()


# ============================================================
# PRODUCCIÓN
# ============================================================

class DialogModelo(QDialog):
    def __init__(self, controller: ProduccionController, modelo_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.modelo_id = modelo_id
        self.setWindowTitle("Nuevo Modelo" if modelo_id is None else "Editar Modelo")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        if modelo_id:
            self._load_data()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(siguiente_folio("modelos", "codigo", "MOD"))
        self.txt_codigo.setPlaceholderText("Ej: MOD-0001")
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Botín Vaquero, Bota Roper, etc.")
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción opcional")

        form.addRow("Código:", self.txt_codigo)
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Descripción:", self.txt_desc)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        m = self.controller.obtener_modelo(self.modelo_id)
        if m:
            self.txt_codigo.setText(m.get("codigo", ""))
            self.txt_nombre.setText(m.get("nombre", ""))
            self.txt_desc.setText(m.get("descripcion", ""))

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()
        if not codigo or not nombre:
            QMessageBox.warning(self, "Campos requeridos", "Código y nombre son obligatorios.")
            return
        if self.modelo_id:
            self.controller.actualizar_modelo(self.modelo_id, codigo, nombre, self.txt_desc.text().strip())
        else:
            self.controller.crear_modelo(codigo, nombre, self.txt_desc.text().strip())
        self.accept()


class DialogVariante(QDialog):
    def __init__(self, controller: ProduccionController, variante_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.variante_id = variante_id
        self.setWindowTitle("Nueva Variante" if variante_id is None else "Editar Variante")
        self.setMinimumWidth(500)
        self.setModal(True)
        self._setup_ui()
        if variante_id:
            self._load_data()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.setSpacing(12)

        self.cmb_modelo = QComboBox()
        modelos = self.controller.listar_modelos()
        for m in modelos:
            self.cmb_modelo.addItem(f"{m['codigo']} - {m['nombre']}", m["id"])

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(siguiente_folio("variantes", "codigo_variante", "VAR"))
        self.txt_codigo.setPlaceholderText("Ej: VAR-0001")
        self.txt_color = QLineEdit()
        self.txt_color.setPlaceholderText("Ej: Negro, Café, Blanco")
        self.txt_piel = QLineEdit()
        self.txt_piel.setPlaceholderText("Ej: Vaquera, Gamuza, Industrial")

        form.addRow("Modelo:", self.cmb_modelo)
        form.addRow("Código Variante:", self.txt_codigo)
        form.addRow("Color:", self.txt_color)
        form.addRow("Piel:", self.txt_piel)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar")
        btn_save.setObjectName("btnPrimary")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _load_data(self) -> None:
        v = self.controller.obtener_variante(self.variante_id)
        if v:
            for i in range(self.cmb_modelo.count()):
                if self.cmb_modelo.itemData(i) == v["modelo_id"]:
                    self.cmb_modelo.setCurrentIndex(i)
                    break
            self.txt_codigo.setText(v.get("codigo_variante", ""))
            self.txt_color.setText(v.get("color", ""))
            self.txt_piel.setText(v.get("piel", ""))

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        color = self.txt_color.text().strip()
        piel = self.txt_piel.text().strip()
        if not codigo or not color:
            QMessageBox.warning(self, "Campos requeridos", "Código y color son obligatorios.")
            return
        if self.variante_id:
            self.controller.actualizar_variante(self.variante_id, self.cmb_modelo.currentData(),
                                                 color, piel, codigo)
        else:
            self.controller.crear_variante(self.cmb_modelo.currentData(), color, piel, codigo)
        self.accept()


class DialogBOM(QDialog):
    def __init__(self, controller: ProduccionController, inv_controller: InventarioController,
                 modelo_id: int, modelo_nombre: str) -> None:
        super().__init__()
        self.controller = controller
        self.inv_controller = inv_controller
        self.modelo_id = modelo_id
        self.setWindowTitle(f"Lista de Materiales - {modelo_nombre}")
        self.setMinimumSize(700, 500)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Insumo", "Cantidad por Par", "Unidad", "InsumoID"])
        self.table.setColumnHidden(3, True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.verticalHeader().setDefaultSectionSize(46)

        bom = self.controller.obtener_bom(self.modelo_id)
        self.table.setRowCount(len(bom))
        for i, b in enumerate(bom):
            self.table.setItem(i, 0, QTableWidgetItem(b.get("insumo_nombre", "")))
            self._set_widgets_fila(i, b.get("cantidad_por_par", 0),
                                   b.get("unidad_medida", "") or "pieza",
                                   b.get("insumo_id", ""))

        layout.addWidget(self.table)

        btn_add = QPushButton("+ Agregar Insumo")
        btn_add.setObjectName("btnPrimary")
        btn_add.clicked.connect(self._agregar)

        btn_remove = QPushButton("Quitar Seleccionado")
        btn_remove.setObjectName("btnDanger")
        btn_remove.clicked.connect(self._quitar)

        toolbar = QHBoxLayout()
        toolbar.addWidget(btn_add)
        toolbar.addWidget(btn_remove)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Guardar BOM")
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _set_widgets_fila(self, row: int, cantidad: float, unidad: str, insumo_id) -> None:
        spn = QDoubleSpinBox()
        spn.setRange(0, 999999)
        spn.setDecimals(2)
        spn.setValue(cantidad)
        self.table.setCellWidget(row, 1, spn)
        cmb = QComboBox()
        for u in self.controller.listar_unidades():
            cmb.addItem(u["abreviatura"], u["nombre"])
        idx = cmb.findText(unidad)
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        self.table.setCellWidget(row, 2, cmb)
        self.table.setItem(row, 3, QTableWidgetItem(str(insumo_id)))

    def _agregar(self) -> None:
        dlg = DialogSeleccionarInsumo(self)
        if dlg.exec() == QDialog.Accepted:
            ins = dlg.get_seleccion()
            if ins:
                row = self.table.rowCount()
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(ins["nombre"]))
                self._set_widgets_fila(row, 1, "pieza", ins["id"])

    def _quitar(self) -> None:
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)

    def _save(self) -> None:
        insumos = []
        for row in range(self.table.rowCount()):
            spn = self.table.cellWidget(row, 1)
            cmb = self.table.cellWidget(row, 2)
            insumos.append({
                "insumo_id": int(self.table.item(row, 3).text()),
                "cantidad": spn.value() if spn else 0,
                "unidad": cmb.currentText() if cmb else "pieza",
            })
        self.controller.guardar_bom(self.modelo_id, insumos)
        self.accept()


class DialogOrdenProduccion(QDialog):
    def __init__(self, controller: ProduccionController) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Nueva Orden de Producción")
        self.setMinimumSize(800, 650)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        self.txt_folio = QLineEdit()
        self.txt_folio.setText(siguiente_folio("ordenes_produccion", "folio", "OP"))
        self.txt_folio.setPlaceholderText("Ej: OP-0001")

        self.cmb_variante = QComboBox()
        variantes = self.controller.listar_variantes()
        for v in variantes:
            self.cmb_variante.addItem(
                f"{v['codigo_variante']} - {v.get('modelo_nombre', '')} ({v['color']}/{v['piel']})",
                v["id"],
            )

        self.dte_inicio = QDateEdit()
        self.dte_inicio.setCalendarPopup(True)
        from PySide6.QtCore import QDate
        self.dte_inicio.setDate(QDate.currentDate())

        self.dte_entrega = QDateEdit()
        self.dte_entrega.setCalendarPopup(True)
        self.dte_entrega.setDate(QDate.currentDate().addDays(7))

        self.cmb_prioridad = QComboBox()
        self.cmb_prioridad.addItems(["baja", "normal", "alta", "urgente"])

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")

        form.addRow("Folio:", self.txt_folio)
        form.addRow("Variante:", self.cmb_variante)
        form.addRow("Fecha Inicio:", self.dte_inicio)
        form.addRow("Fecha Entrega:", self.dte_entrega)
        form.addRow("Prioridad:", self.cmb_prioridad)
        form.addRow("Observaciones:", self.txt_obs)
        layout.addLayout(form)

        talla_label = QLabel("Matriz de Tallas (ingrese pares por talla):")
        talla_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 8px;")
        layout.addWidget(talla_label)

        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        self._tallas = db.fetch_all("SELECT * FROM tallas_corrida ORDER BY orden")

        self._tallas_container = QWidget()
        tallas_container_layout = QVBoxLayout(self._tallas_container)
        tallas_container_layout.setContentsMargins(0, 0, 0, 0)
        tallas_container_layout.setSpacing(4)

        self._tallas_filas: list[QWidget] = []
        fila = QWidget()
        fila_layout = QHBoxLayout(fila)
        fila_layout.setContentsMargins(0, 0, 0, 0)

        self.spn_tallas: dict[int, QSpinBox] = {}
        cols = 0
        for t in self._tallas:
            gb = QGroupBox(f"Talla {t['talla']}")
            gb.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
            vb = QVBoxLayout(gb)
            spn = QSpinBox()
            spn.setRange(0, 9999)
            spn.setValue(0)
            spn.setMinimumHeight(36)
            spn.setStyleSheet("font-size: 14px; font-weight: bold;")
            spn.valueChanged.connect(self._actualizar_total)
            self.spn_tallas[t["id"]] = spn
            vb.addWidget(spn)
            fila_layout.addWidget(gb)
            cols += 1
            if cols % 5 == 0:
                self._tallas_filas.append(fila)
                fila = QWidget()
                fila_layout = QHBoxLayout(fila)
                fila_layout.setContentsMargins(0, 0, 0, 0)
        if cols % 5 != 0:
            self._tallas_filas.append(fila)
        for f in self._tallas_filas:
            tallas_container_layout.addWidget(f)

        corrida_box = QGroupBox("Corrida rápida de tallas")
        corrida_box.setStyleSheet("QGroupBox { font-weight: bold; font-size: 12px; }")
        corrida_layout = QHBoxLayout(corrida_box)
        corrida_layout.setSpacing(8)

        corrida_layout.addWidget(QLabel("De talla:"))
        self.cmb_talla_desde = QComboBox()
        self.cmb_talla_hasta = QComboBox()
        for t in self._tallas:
            self.cmb_talla_desde.addItem(t["talla"], t["id"])
            self.cmb_talla_hasta.addItem(t["talla"], t["id"])
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

        tallas_container_layout.addWidget(corrida_box)

        self.lbl_total = QLabel("Total de pares: 0")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px; color: #4f46e5;")
        tallas_container_layout.addWidget(self.lbl_total)

        layout.addWidget(self._tallas_container)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Crear Orden de Producción")
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _aplicar_corrida(self) -> None:
        idx_desde = self.cmb_talla_desde.currentIndex()
        idx_hasta = self.cmb_talla_hasta.currentIndex()
        if idx_desde > idx_hasta:
            idx_desde, idx_hasta = idx_hasta, idx_desde
        pares = self.spn_corrida.value()
        for i, t in enumerate(self._tallas):
            if idx_desde <= i <= idx_hasta:
                self.spn_tallas[t["id"]].setValue(pares)

    def _limpiar_tallas(self) -> None:
        for spn in self.spn_tallas.values():
            spn.setValue(0)

    def _actualizar_total(self) -> None:
        total = sum(spn.value() for spn in self.spn_tallas.values())
        self.lbl_total.setText(f"Total de pares: {total}")

    def _save(self) -> None:
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.warning(self, "Campo requerido", "El folio es obligatorio.")
            return
        if self.cmb_variante.count() == 0:
            QMessageBox.warning(self, "Sin variantes", "Cree al menos una variante primero.")
            return

        matriz = []
        for talla_id, spn in self.spn_tallas.items():
            if spn.value() > 0:
                matriz.append({"talla_id": talla_id, "pares": spn.value()})

        if not matriz:
            QMessageBox.warning(self, "Matriz vacía", "Ingrese al menos un par en alguna talla.")
            return

        total = sum(m["pares"] for m in matriz)

        materiales = self.controller.verificar_materiales(self.cmb_variante.currentData(), total)
        faltantes = [m for m in materiales if m["faltante"] > 0.005]
        if faltantes:
            msg = "⚠ Materiales insuficientes para esta producción:\n\n"
            for m in faltantes:
                msg += (f"• {m['insumo_nombre']}: requiere {m['requerido']:.2f} "
                        f"{m['unidad']}, disponible {m['disponible']:.2f}\n")
            msg += "\n¿Crear la orden de todos modos?"
            resp = QMessageBox.question(self, "Materiales insuficientes", msg,
                                        QMessageBox.Yes | QMessageBox.No)
            if resp != QMessageBox.Yes:
                return

        resp = QMessageBox.question(
            self, "Confirmar",
            f"Crear OP '{folio}' con {total} pares?\n{len(matriz)} tallas diferentes.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if resp != QMessageBox.Yes:
            return

        self.controller.crear_op(
            folio, self.cmb_variante.currentData(), matriz,
            self.dte_inicio.date().toString("yyyy-MM-dd"),
            self.dte_entrega.date().toString("yyyy-MM-dd"),
            self.cmb_prioridad.currentText(),
            self.txt_obs.toPlainText().strip(),
        )
        self.accept()


class DialogSeguimientoOP(QDialog):
    def __init__(self, controller: ProduccionController, op_id: int) -> None:
        super().__init__()
        self.controller = controller
        self.op_id = op_id
        self.setWindowTitle("Seguimiento de OP")
        self.setMinimumSize(700, 550)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        op = self.controller.obtener_op(self.op_id)
        if not op:
            layout.addWidget(QLabel("OP no encontrada"))
            return

        info = QFormLayout()
        info.addRow("Folio:", QLabel(op.get("folio", "")))
        info.addRow("Modelo:", QLabel(f"{op.get('modelo_nombre', '')} - {op.get('codigo_variante', '')}"))
        info.addRow("Total Pares:", QLabel(str(op.get("total_pares", 0))))
        info.addRow("Estatus:", QLabel(op.get("estatus", "").capitalize()))
        layout.addLayout(info)

        tallas = self.controller.obtener_tallas_op(self.op_id)
        if tallas:
            t_label = QLabel("Distribución por talla: " + ", ".join(f"T{t['talla']}: {t['pares']}pr" for t in tallas))
            t_label.setStyleSheet("font-size: 12px; color: #64748b;")
            layout.addWidget(t_label)

        layout.addWidget(QLabel("Avance en línea de producción:"))
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Estación", "Entrada", "Salida", "Procesados", "Estatus"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        seguimiento = self.controller.obtener_seguimiento(self.op_id)
        self.table.setRowCount(len(seguimiento))
        for i, s in enumerate(seguimiento):
            self.table.setItem(i, 0, QTableWidgetItem(s.get("estacion_nombre", "")))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("fecha_entrada", "") or "-"))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("fecha_salida", "") or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(str(s.get("pares_procesados", 0) or 0)))
            est_item = QTableWidgetItem(s.get("estatus", "").capitalize())
            if s.get("estatus") == "completado":
                est_item.setForeground(Qt.darkGreen)
            elif s.get("estatus") == "en_proceso":
                est_item.setForeground(Qt.darkYellow)
            self.table.setItem(i, 4, est_item)

        layout.addWidget(self.table)

        # Avance button
        self.btn_avanzar = QPushButton("Avanzar a Siguiente Estación")
        self.btn_avanzar.setObjectName("btnSuccess")
        self.btn_avanzar.clicked.connect(lambda: self._avanzar(op))
        layout.addWidget(self.btn_avanzar, 0, Qt.AlignRight)

        btn_close = QPushButton("Cerrar")
        btn_close.setObjectName("btnSecondary")
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, 0, Qt.AlignRight)

    def _avanzar(self, op: dict) -> None:
        seg = self.controller.obtener_seguimiento(self.op_id)
        siguiente = None
        for s in seg:
            if s["estatus"] == "en_proceso" or (s["estatus"] == "pendiente" and siguiente is None):
                siguiente = s
                break
        if not siguiente:
            QMessageBox.information(self, "Completado", "Esta OP ya está terminada.")
            return

        dlg = DialogAvanceEstacion(self.controller, self.op_id, siguiente)
        if dlg.exec() == QDialog.Accepted:
            self._refresh()

    def _refresh(self) -> None:
        op = self.controller.obtener_op(self.op_id)
        seguimiento = self.controller.obtener_seguimiento(self.op_id)
        self.table.setRowCount(len(seguimiento))
        for i, s in enumerate(seguimiento):
            self.table.setItem(i, 0, QTableWidgetItem(s.get("estacion_nombre", "")))
            self.table.setItem(i, 1, QTableWidgetItem(s.get("fecha_entrada", "") or "-"))
            self.table.setItem(i, 2, QTableWidgetItem(s.get("fecha_salida", "") or "-"))
            self.table.setItem(i, 3, QTableWidgetItem(str(s.get("pares_procesados", 0) or 0)))
            est_item = QTableWidgetItem(s.get("estatus", "").capitalize())
            if s.get("estatus") == "completado":
                est_item.setForeground(Qt.darkGreen)
            elif s.get("estatus") == "en_proceso":
                est_item.setForeground(Qt.darkYellow)
            self.table.setItem(i, 4, est_item)


class DialogAvanceEstacion(QDialog):
    def __init__(self, controller: ProduccionController, op_id: int,
                 estacion: dict) -> None:
        super().__init__()
        self.controller = controller
        self.op_id = op_id
        self.estacion = estacion
        self.setWindowTitle(f"Avanzar: {estacion['estacion_nombre']}")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        op = self.controller.obtener_op(self.op_id)
        total = op.get("total_pares", 0) if op else 0

        QLabel(f"Estación: <b>{self.estacion['estacion_nombre']}</b>").setParent(self)
        QLabel(f"Total pares en OP: {total}").setParent(self)

        form = QFormLayout()
        self.spn_procesados = QSpinBox()
        self.spn_procesados.setRange(0, total)
        self.spn_procesados.setValue(total)

        self.spn_defectuosos = QSpinBox()
        self.spn_defectuosos.setRange(0, total)
        self.spn_defectuosos.setValue(0)

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)
        self.txt_obs.setPlaceholderText("Incidencias (opcional)")

        form.addRow("Pares procesados:", self.spn_procesados)
        form.addRow("Pares defectuosos:", self.spn_defectuosos)
        form.addRow("Observaciones:", self.txt_obs)
        layout.addLayout(form)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Completar Estación")
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _save(self) -> None:
        procesados = self.spn_procesados.value()
        defectuosos = self.spn_defectuosos.value()
        if procesados == 0:
            QMessageBox.warning(self, "Validación", "Debe procesar al menos 1 par.")
            return
        self.controller.avanzar_estacion(
            self.op_id, self.estacion["estacion_id"],
            procesados, defectuosos, self.txt_obs.toPlainText().strip(),
        )
        self.accept()
