from PySide6.QtCore import QBuffer, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QComboBox,
    QDialog, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QListWidget, QMessageBox, QPushButton, QScrollArea, QSpinBox, QTableWidget,
    QTableWidgetItem, QTextEdit, QVBoxLayout, QWidget,
)

from src.components.date_picker import DatePicker
from src.components.tallas_matrix import MatrizTallasDialog
from src.controllers.inventario_controller import InventarioController
from src.controllers.ordenes_compra_controller import OrdenesCompraController
from src.controllers.produccion_controller import ProduccionController
from src.utils.table_utils import configurar_tabla_excel
from src.utils.ui_helpers import SearchableComboBox
from src.views.table_widget import GorettiTable


def _etiqueta_proveedor(p: dict) -> str:
    """Etiqueta para selectores de proveedor: razón social + nombre comercial."""
    nombre = (p.get("nombre") or "").strip()
    comercial = (p.get("nombre_comercial") or "").strip()
    if comercial and comercial.lower() != nombre.lower():
        return f"{nombre} ({comercial})"
    return nombre


def _subtotal_detalle(d: dict) -> float:
    """Subtotal del renglón: Σ(pares × precio) por talla si hay precios por talla;
    si no, cantidad × precio_unitario."""
    tallas = d.get("tallas", []) or []
    con_precio = [t for t in tallas if float(t.get("precio", 0) or 0) > 0]
    if con_precio:
        return sum(float(t.get("pares", 0) or 0) * float(t.get("precio", 0) or 0)
                   for t in con_precio)
    return float(d.get("cantidad", 0) or 0) * float(d.get("precio_unitario", 0) or 0)


def _subtotal_recibido(d: dict, recibido: float) -> float:
    """Subtotal del renglón al recibir: prorratea el importe por talla según la
    proporción recibida; si no hay precios por talla, recibido × precio_unitario."""
    tallas = d.get("tallas", []) or []
    con_precio = [t for t in tallas if float(t.get("precio", 0) or 0) > 0]
    if con_precio:
        solicitado = float(d.get("cantidad", 0) or 0)
        total_tallas = _subtotal_detalle(d)
        if solicitado > 0:
            return total_tallas * (recibido / solicitado)
        return 0.0
    return float(recibido) * float(d.get("precio_unitario", 0) or 0)


class WidgetImagen(QFrame):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self._imagen: bytes | None = None
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)
        self.lbl_preview = QLabel("Sin imagen")
        self.lbl_preview.setObjectName("imgPreview")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setFixedSize(100, 100)
        lay.addWidget(self.lbl_preview)
        col = QVBoxLayout()
        col.setSpacing(8)
        btn_sel = QPushButton("Seleccionar...")
        btn_sel.setObjectName("btnSecondary")
        btn_sel.clicked.connect(self._seleccionar)
        btn_pegar = QPushButton("Pegar (Ctrl+V)")
        btn_pegar.setObjectName("btnSecondary")
        btn_pegar.clicked.connect(self._pegar)
        btn_quitar = QPushButton("Quitar")
        btn_quitar.setObjectName("btnDanger")
        btn_quitar.clicked.connect(self._quitar)
        col.addWidget(btn_sel)
        col.addWidget(btn_pegar)
        col.addWidget(btn_quitar)
        col.addStretch()
        lay.addLayout(col)
        lay.addStretch()

    def _seleccionar(self) -> None:
        archivo, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp *.webp *.gif)")
        if not archivo:
            return
        imagen = QImage(archivo)
        if imagen.isNull():
            QMessageBox.warning(self, "Imagen inválida",
                                "No se pudo leer el archivo seleccionado.")
            return
        self._set_qimage(imagen)

    def _pegar(self) -> None:
        imagen = QGuiApplication.clipboard().image()
        if imagen.isNull():
            QMessageBox.information(self, "Portapapeles",
                                    "El portapapeles no contiene una imagen.")
            return
        self._set_qimage(imagen)

    def _quitar(self) -> None:
        self._imagen = None
        self.lbl_preview.setPixmap(QPixmap())
        self.lbl_preview.setText("Sin imagen")

    def _set_qimage(self, imagen: QImage) -> None:
        buf = QBuffer()
        buf.open(QBuffer.WriteOnly)
        imagen.save(buf, "PNG")
        self._imagen = bytes(buf.data())
        self._mostrar(self._imagen)

    def _mostrar(self, data: bytes) -> None:
        pix = QPixmap()
        pix.loadFromData(data)
        if not pix.isNull():
            self.lbl_preview.setPixmap(
                pix.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.lbl_preview.setText("")

    def set_imagen(self, data: bytes | None) -> None:
        if data:
            self._imagen = data
            self._mostrar(data)
        else:
            self._quitar()

    def get_imagen(self) -> bytes | None:
        return self._imagen


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
        self.txt_codigo.setReadOnly(True)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Nombre del insumo")
        self.txt_nombre.editingFinished.connect(self._verificar_nombre)

        self.lbl_nombre_aviso = QLabel("")
        self.lbl_nombre_aviso.setStyleSheet("color: #b45309; font-size: 12px;")
        self.lbl_nombre_aviso.setWordWrap(True)
        self.lbl_nombre_aviso.setVisible(False)

        self.cmb_categoria = SearchableComboBox(
            placeholder="Seleccione o escriba una categoría…")
        self._cargar_categorias()

        self.cmb_unidad = QComboBox()
        self._cargar_unidades()
        self.spn_minimo = QDoubleSpinBox()
        self.spn_minimo.setRange(0, 999999)
        self.spn_minimo.setDecimals(2)
        self.spn_minimo.setValue(0)

        for w, lbl in [
            (self.txt_codigo, "Código:"),
            (self.txt_nombre, "Nombre:"),
            (self.cmb_categoria, "Categoría:"),
            (self.cmb_unidad, "Unidad de medida:"),
            (self.spn_minimo, "Stock mínimo:"),
        ]:
            form.addRow(QLabel(lbl), w)
        form.addRow(self.lbl_nombre_aviso)

        self.img_widget = WidgetImagen()
        form.addRow(QLabel("Imagen:"), self.img_widget)

        layout.addLayout(form)

        self.chk_variantes = QCheckBox("Crear variantes por talla")
        self.chk_variantes.toggled.connect(self._on_tallas_toggled)
        layout.addWidget(self.chk_variantes)

        self.frame_tallas = QFrame()
        self.frame_tallas.setObjectName("card")
        fp = QVBoxLayout(self.frame_tallas)
        fp.setContentsMargins(12, 12, 12, 12)
        fp.setSpacing(8)

        sel = QHBoxLayout()
        sel.addWidget(QLabel("Desde:"))
        self.cmb_desde = QComboBox()
        self.cmb_hasta = QComboBox()
        for p in self.controller.listar_tallas():
            self.cmb_desde.addItem(p["talla"], p["talla"])
            self.cmb_hasta.addItem(p["talla"], p["talla"])
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

        layout.addWidget(self.frame_tallas)
        self.frame_tallas.setVisible(False)

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

    def _on_tallas_toggled(self, checked: bool) -> None:
        self.frame_tallas.setVisible(checked)
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

    def _tallas_seleccionadas(self) -> list[str]:
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
        tallas = self._tallas_seleccionadas()
        colores = self._colores_seleccionadas()
        if tallas and colores:
            codigos = [f"{base}-{t}-{c}" for t in tallas for c in colores]
        elif tallas:
            codigos = [f"{base}-{t}" for t in tallas]
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

    def _cargar_categorias(self) -> None:
        self.cmb_categoria.clear()
        for cat in self.controller.listar_categorias():
            self.cmb_categoria.addItem(cat, cat)

    def _verificar_nombre(self) -> None:
        nombre = self.txt_nombre.text().strip()
        if not nombre:
            self.lbl_nombre_aviso.setVisible(False)
            return
        coincidencias = self.controller.buscar_insumos_por_nombre(
            nombre, excluir_id=self.insumo_id)
        if not coincidencias:
            self.lbl_nombre_aviso.setVisible(False)
            return
        exactos = [c for c in coincidencias
                   if c.get("nombre", "").strip().lower() == nombre.lower()]
        if exactos:
            msg = ("Ya existe un insumo con el nombre "
                   f"\"{exactos[0]['nombre']}\" (código {exactos[0]['codigo']}).")
        else:
            nombres = ", ".join(f"\"{c['nombre']}\" (código {c['codigo']})"
                                for c in coincidencias[:3])
            msg = f"Posible insumo duplicado. Ya existen nombres similares: {nombres}."
        self.lbl_nombre_aviso.setText(msg)
        self.lbl_nombre_aviso.setVisible(True)

    def _load_data(self) -> None:
        ins = self.controller.obtener_insumo(self.insumo_id)
        if ins:
            self.txt_codigo.setText(ins.get("codigo", ""))
            self.txt_nombre.setText(ins.get("nombre", ""))
            self.cmb_categoria.clear()
            for cat in self.controller.listar_categorias(excluir_id=self.insumo_id):
                self.cmb_categoria.addItem(cat, cat)
            idx = self.cmb_categoria.findText(ins.get("categoria", ""))
            if idx >= 0:
                self.cmb_categoria.setCurrentIndex(idx)
            else:
                self.cmb_categoria.setEditText(ins.get("categoria", ""))
            idx = self.cmb_unidad.findText(ins.get("unidad_medida", "pieza"))
            if idx >= 0:
                self.cmb_unidad.setCurrentIndex(idx)
            self.spn_minimo.setValue(ins.get("stock_minimo", 0))
            self.img_widget.set_imagen(
                self.controller.obtener_imagen_insumo(self.insumo_id))

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()
        categoria = self.cmb_categoria.currentText().strip()
        if not codigo or not nombre or not categoria:
            QMessageBox.warning(self, "Campos requeridos", "Código, nombre y categoría son obligatorios.")
            return
        unidad = self.cmb_unidad.currentText()
        minimo = self.spn_minimo.value()
        imagen = self.img_widget.get_imagen()
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
                self.insumo_id, codigo, nombre, categoria, unidad, minimo, imagen,
            )
        else:
            self.controller.crear_insumo(codigo, nombre, categoria, unidad, minimo, imagen)
        for c in variantes:
            self.controller.crear_insumo(c, nombre, categoria, unidad, minimo, imagen)
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
        self.txt_nombre_comercial = QLineEdit()
        self.txt_nombre_comercial.setPlaceholderText("Nombre comercial (marca con la que lo conocemos)")
        self.txt_telefono = QLineEdit()
        self.txt_telefono.setPlaceholderText("Teléfono")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("Correo electrónico")
        self.txt_direccion = QLineEdit()
        self.txt_direccion.setPlaceholderText("Dirección")

        for w, lbl in [
            (self.txt_rfc, "RFC:"), (self.txt_nombre, "Nombre:"),
            (self.txt_nombre_comercial, "Nombre Comercial:"),
            (self.txt_telefono, "Teléfono:"), (self.txt_email, "Email:"),
            (self.txt_direccion, "Dirección:"),
        ]:
            form.addRow(QLabel(lbl), w)

        layout.addLayout(form)

        prov_label = QLabel("¿Qué productos nos provee?")
        prov_label.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 6px;")
        layout.addWidget(prov_label)

        self.table_prov = GorettiTable(
            columns=[
                {"key": "material", "label": "Material", "stretch": True},
                {"key": "color", "label": "Color"},
                {"key": "unidad", "label": "Unidad", "widget": self._factory_unidad},
                {"key": "precio", "label": "Precio", "widget": self._factory_precio},
                {"key": "comentario", "label": "Comentario", "stretch": True},
                {"key": "id", "label": "InsumoID", "hidden": True},
            ],
            sortable=False,
        )
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

    def _factory_unidad(self, record: dict, row: int) -> QComboBox:
        cmb = QComboBox()
        for u in self.controller.listar_unidades():
            cmb.addItem(u["abreviatura"], u["nombre"])
        idx = cmb.findText(record.get("unidad", "pieza"))
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        return cmb

    def _factory_precio(self, record: dict, row: int) -> QDoubleSpinBox:
        spn = QDoubleSpinBox()
        spn.setRange(0, 99999999)
        spn.setDecimals(2)
        spn.setValue(float(record.get("precio", 0) or 0))
        return spn

    def _cargar_insumos_proveedor(self) -> None:
        items = self.controller.listar_insumos_proveedor(self.proveedor_id)
        self.table_prov.set_records([
            {"material": it.get("insumo_nombre", ""), "color": it.get("color", ""),
             "unidad": it.get("unidad_medida", "") or "pieza",
             "precio": it.get("precio", 0), "comentario": it.get("comentario", ""),
             "id": it["insumo_id"]}
            for it in items
        ])

    def _agregar_producto(self) -> None:
        dlg = DialogSeleccionarInsumo(self)
        if dlg.exec() == QDialog.Accepted:
            ins = dlg.get_seleccion()
            if ins:
                for row in range(self.table_prov.row_count()):
                    if self.table_prov.cell_text(row, "id") == str(ins["id"]):
                        QMessageBox.information(self, "Ya agregado",
                            f"'{ins['nombre']}' ya está en la lista.")
                        return
                self.table_prov.add_row({
                    "material": ins["nombre"], "color": "", "unidad": "pieza",
                    "precio": 0, "comentario": "", "id": ins["id"],
                })

    def _quitar_producto(self) -> None:
        row = self.table_prov.current_row()
        if row >= 0:
            self.table_prov.remove_row(row)

    def _load_data(self) -> None:
        prov = self.controller.obtener_proveedor(self.proveedor_id)
        if prov:
            self.txt_rfc.setText(prov.get("rfc", ""))
            self.txt_nombre.setText(prov.get("nombre", ""))
            self.txt_nombre_comercial.setText(prov.get("nombre_comercial", ""))
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
                self.txt_nombre_comercial.text().strip(),
            )
            proveedor_id = self.proveedor_id
        else:
            proveedor_id = self.controller.crear_proveedor(
                rfc, nombre, self.txt_telefono.text().strip(),
                self.txt_email.text().strip(), self.txt_direccion.text().strip(),
                self.txt_nombre_comercial.text().strip(),
            )

        items = []
        for row in range(self.table_prov.row_count()):
            cmb = self.table_prov.cell_widget(row, "unidad")
            spn = self.table_prov.cell_widget(row, "precio")
            items.append({
                "insumo_id": int(self.table_prov.cell_text(row, "id")),
                "color": self.table_prov.cell_text(row, "color").strip(),
                "unidad": cmb.currentText() if cmb else "pieza",
                "precio": spn.value() if spn else 0,
                "comentario": self.table_prov.cell_text(row, "comentario").strip(),
            })
        self.controller.guardar_insumos_proveedor(proveedor_id, items)
        self.accept()


class DialogMatrizTallas(QDialog):
    """Matriz de tallas de Órdenes de Compra con pares y precio por talla.

    Adaptación de la matriz de Goretti_prep (pares + precio por talla) al
    catálogo unificado tallas_catalogo (RD-1). Es un diálogo independiente:
    no extiende el componente aprobado MatrizTallasDialog (que no maneja
    precios) para no alterarlo; el componente sigue usándose en Producción.
    """

    def __init__(self, controller: OrdenesCompraController,
                 inicial: dict[int, int] | None = None,
                 precios_iniciales: dict[int, float] | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.setWindowTitle("Matriz de Tallas")
        self.setMinimumSize(620, 420)
        self.setModal(True)
        self._matriz = dict(inicial or {})
        self._precios = dict(precios_iniciales or {})
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        self._tallas = self.controller.listar_tallas()
        self.spn_pares: dict[int, QSpinBox] = {}
        self.spn_precios: dict[int, QDoubleSpinBox] = {}

        filas: list[QWidget] = []
        fila = QWidget()
        fila_layout = QHBoxLayout(fila)
        fila_layout.setContentsMargins(0, 0, 0, 0)
        cols = 0
        for t in self._tallas:
            gb = QGroupBox(f"Talla {t['talla']}")
            gb.setStyleSheet("QGroupBox { font-weight: bold; font-size: 11px; }")
            vb = QHBoxLayout(gb)
            spn = QSpinBox()
            spn.setRange(0, 9999)
            spn.setValue(int(self._matriz.get(t["id"], 0)))
            spn.setMinimumHeight(30)
            spn.setStyleSheet("font-size: 14px; font-weight: bold;")
            spn.valueChanged.connect(self._actualizar_total)
            self.spn_pares[t["id"]] = spn
            vb.addWidget(spn)
            spn_p = QDoubleSpinBox()
            spn_p.setRange(0, 99999999)
            spn_p.setDecimals(2)
            spn_p.setPrefix("$")
            spn_p.setValue(float(self._precios.get(t["id"], 0) or 0))
            spn_p.setMinimumHeight(30)
            spn_p.setButtonSymbols(QAbstractSpinBox.NoButtons)
            spn_p.setStyleSheet("font-size: 13px;")
            spn_p.valueChanged.connect(self._actualizar_total)
            self.spn_precios[t["id"]] = spn_p
            vb.addWidget(spn_p)
            fila_layout.addWidget(gb)
            cols += 1
            if cols % 2 == 0:
                filas.append(fila)
                fila = QWidget()
                fila_layout = QHBoxLayout(fila)
                fila_layout.setContentsMargins(0, 0, 0, 0)
        if cols % 2 != 0:
            filas.append(fila)
        for f in filas:
            layout.addWidget(f)

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
                self.spn_pares[t["id"]].setValue(pares)

    def _limpiar_tallas(self) -> None:
        for spn in self.spn_pares.values():
            spn.setValue(0)

    def _actualizar_total(self) -> None:
        total = sum(spn.value() for spn in self.spn_pares.values())
        importe = sum(self.spn_pares[pid].value() * self.spn_precios[pid].value()
                      for pid in self.spn_pares)
        self.lbl_total.setText(f"Total de pares: {total}    |    Importe: ${importe:,.2f}")

    def get_matriz(self) -> dict[int, int]:
        return {talla_id: spn.value() for talla_id, spn in self.spn_pares.items()
                if spn.value() > 0}

    def get_precios(self) -> dict[int, float]:
        return {talla_id: spn.value() for talla_id, spn in self.spn_precios.items()
                if spn.value() > 0}


def _tipo_documento(tipo: str) -> str:
    if tipo == "factura":
        return "Factura"
    if tipo == "remision":
        return "Remisión"
    return "Orden de Compra"


class DialogOrdenCompra(QDialog):
    def __init__(self, controller: OrdenesCompraController, tipo: str = "orden") -> None:
        super().__init__()
        self.controller = controller
        self.tipo = tipo
        titulos = {"factura": "Ingresar Factura", "remision": "Ingresar Remisión"}
        self.setWindowTitle(titulos.get(tipo, "Nueva Orden de Compra"))
        self.setMinimumSize(820, 620)
        self.setModal(True)
        # Por fila: talla_id -> {"pares": int, "precio": float}
        self._tallas_fila: dict[int, dict[int, dict]] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        form = QFormLayout()
        form.setSpacing(10)

        self.cmb_proveedor = SearchableComboBox(placeholder="Buscar proveedor…")
        self.cmb_proveedor.addItem("Compra a inventario", None)
        for p in self.controller.listar_proveedores():
            self.cmb_proveedor.addItem(_etiqueta_proveedor(p), p["id"])

        self.txt_folio = QLineEdit()
        prefijo = {"factura": "FAC", "remision": "REM"}.get(self.tipo, "OC")
        self.txt_folio.setPlaceholderText(f"Ej: {prefijo}-0001")
        if self.tipo in ("factura", "remision"):
            self.txt_folio.setReadOnly(False)
        else:
            self.txt_folio.setText(siguiente_folio("ordenes_compra", "folio", prefijo))
            self.txt_folio.setReadOnly(True)
        self.txt_obs = QTextEdit()
        self.txt_obs.setPlaceholderText("Observaciones (opcional)")
        self.txt_obs.setMaximumHeight(60)

        self.cmb_metodo_pago = QComboBox()
        self.cmb_metodo_pago.setEditable(True)
        self.cmb_metodo_pago.addItems([
            "Transferencia bancaria", "Efectivo", "Cheque", "Crédito",
        ])

        self.chk_remision = QCheckBox("Solo remisión (sin impuestos)")
        if self.tipo == "remision":
            self.chk_remision.setChecked(True)

        form.addRow(QLabel("Proveedor:"), self.cmb_proveedor)
        form.addRow(QLabel("Folio:"), self.txt_folio)
        form.addRow(QLabel("Método de pago:"), self.cmb_metodo_pago)
        form.addRow(QLabel("Observaciones:"), self.txt_obs)
        layout.addLayout(form)

        layout.addWidget(self.chk_remision)

        hint = QLabel(
            "Puede agregar cualquier insumo del catálogo; el precio sugerido se toma "
            "del proveedor seleccionado cuando lo tenga registrado."
        )
        hint.setStyleSheet("color: #64748b; font-size: 12px;")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        det_label = QLabel("Detalle de la orden:")
        det_label.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(det_label)

        self.table_detalle = GorettiTable(
            columns=[
                {"key": "nombre", "label": "Insumo", "stretch": True},
                {"key": "tallas", "label": "Tallas", "widget": self._factory_tallas},
                {"key": "cantidad", "label": "Cantidad", "widget": self._factory_cantidad},
                {"key": "precio", "label": "Precio Unit.", "widget": self._factory_precio_oc},
                {"key": "subtotal", "label": "Subtotal", "align": "right"},
                {"key": "id", "label": "InsumoID", "hidden": True},
            ],
            sortable=False,
            row_height=50,
        )
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
        btn_save = QPushButton(
            {"factura": "Guardar Factura", "remision": "Guardar Remisión"}.get(self.tipo, "Crear Orden"))
        btn_save.setObjectName("btnSuccess")
        btn_save.clicked.connect(self._save)
        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save)
        layout.addLayout(btns)

    def _factory_tallas(self, record: dict, row: int) -> QPushButton:
        btn = QPushButton("Configurar Tallas")
        btn.setObjectName("btnSecondary")
        btn.clicked.connect(lambda _=False, r=row: self._configurar_tallas(r))
        return btn

    def _factory_cantidad(self, record: dict, row: int) -> QDoubleSpinBox:
        spn = QDoubleSpinBox()
        spn.setRange(0, 999999)
        spn.setDecimals(2)
        spn.setButtonSymbols(QAbstractSpinBox.NoButtons)
        spn.setValue(float(record.get("cantidad", 1) or 0))
        spn.valueChanged.connect(self._recalcular)
        return spn

    def _factory_precio_oc(self, record: dict, row: int) -> QDoubleSpinBox:
        spn = QDoubleSpinBox()
        spn.setRange(0, 99999999)
        spn.setDecimals(2)
        spn.setButtonSymbols(QAbstractSpinBox.NoButtons)
        spn.setValue(float(record.get("precio", 0) or 0))
        spn.valueChanged.connect(self._recalcular)
        return spn

    def _agregar_insumo(self) -> None:
        proveedor_id = self.cmb_proveedor.currentData()
        dlg = DialogSeleccionarInsumo(self)
        if dlg.exec() == QDialog.Accepted:
            insumo = dlg.get_seleccion()
            if insumo:
                for row in range(self.table_detalle.row_count()):
                    if self.table_detalle.cell_text(row, "id") == str(insumo["id"]):
                        QMessageBox.information(self, "Ya agregado",
                            f"'{insumo['nombre']}' ya está en la orden.")
                        return
                precio_default = 0.0
                if proveedor_id:
                    for pi in self.controller.listar_insumos_proveedor_por_insumo(insumo["id"]):
                        if pi["proveedor_id"] == proveedor_id:
                            precio_default = float(pi.get("precio", 0) or 0)
                            break
                row = self.table_detalle.row_count()
                self.table_detalle.add_row({
                    "nombre": insumo["nombre"], "tallas": None, "cantidad": 1,
                    "precio": precio_default, "subtotal": "0.00", "id": insumo["id"],
                })
                self._tallas_fila[row] = {}
                self._recalcular()

    def _configurar_tallas(self, row: int) -> None:
        prev = self._tallas_fila.get(row, {})
        dlg = DialogMatrizTallas(
            self.controller,
            inicial={tid: v["pares"] for tid, v in prev.items()},
            precios_iniciales={tid: v["precio"] for tid, v in prev.items()},
        )
        if dlg.exec() == QDialog.Accepted:
            matriz = dlg.get_matriz()
            precios = dlg.get_precios()
            self._tallas_fila[row] = {
                tid: {"pares": matriz[tid], "precio": precios.get(tid, 0.0)}
                for tid in matriz
            }
            total_pares = sum(matriz.values())
            btn = self.table_detalle.cell_widget(row, "tallas")
            if btn:
                btn.setText(f"Editar Tallas ({total_pares} pr)")
            spn_c = self.table_detalle.cell_widget(row, "cantidad")
            if spn_c:
                spn_c.setValue(total_pares)
            self._recalcular()

    def _quitar_insumo(self) -> None:
        row = self.table_detalle.current_row()
        if row >= 0:
            self.table_detalle.remove_row(row)
            self._tallas_fila.pop(row, None)
            self._recalcular()

    def _recalcular(self, *_args) -> None:
        total = 0.0
        for row in range(self.table_detalle.row_count()):
            spn_c = self.table_detalle.cell_widget(row, "cantidad")
            spn_p = self.table_detalle.cell_widget(row, "precio")
            puntos = self._tallas_fila.get(row, {})
            if puntos:
                sub = sum(v["pares"] * v["precio"] for v in puntos.values())
            elif spn_c and spn_p:
                sub = spn_c.value() * spn_p.value()
            else:
                sub = 0.0
            self.table_detalle.set_cell_text(row, "subtotal", f"{sub:.2f}")
            total += sub
        self.lbl_total.setText(f"Total: ${total:.2f}")

    def _save(self) -> None:
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.warning(self, "Campo requerido", "El folio es obligatorio.")
            return
        if self.controller.folio_existe(folio):
            QMessageBox.warning(self, "Folio duplicado",
                                f"Ya existe un documento con el folio '{folio}'.")
            return
        proveedor_id = self.cmb_proveedor.currentData()
        detalle = []
        for row in range(self.table_detalle.row_count()):
            insumo_id = int(self.table_detalle.cell_text(row, "id"))
            spn_c = self.table_detalle.cell_widget(row, "cantidad")
            spn_p = self.table_detalle.cell_widget(row, "precio")
            puntos = self._tallas_fila.get(row, {})
            cantidad = sum(v["pares"] for v in puntos.values()) if puntos else (spn_c.value() if spn_c else 0)
            precio = spn_p.value() if spn_p else 0
            if cantidad > 0:
                detalle.append({
                    "insumo_id": insumo_id,
                    "cantidad": cantidad,
                    "precio": precio,
                    "tallas": [
                        {"talla_id": tid, "pares": v["pares"], "precio": v["precio"]}
                        for tid, v in puntos.items()
                    ],
                })
        if not detalle:
            QMessageBox.warning(self, "Detalle vacío", "Agregue al menos un insumo a la orden.")
            return
        oc_id = self.controller.crear_orden(
            folio, detalle, self.txt_obs.toPlainText().strip(),
            proveedor_id=proveedor_id,
            metodo_pago=self.cmb_metodo_pago.currentText().strip(),
            solo_remision=self.chk_remision.isChecked(),
            tipo=self.tipo,
        )
        if self.tipo in ("factura", "remision"):
            self.controller.recibir_orden(oc_id)
        self.accept()


class DialogSeleccionarInsumo(QDialog):
    def __init__(self, parent=None, proveedor_id: int | None = None,
                 sin_proveedor: bool = False) -> None:
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Insumo")
        self.setMinimumSize(700, 400)
        self.setModal(True)
        self._selected = None
        self._proveedor_id = proveedor_id
        self._sin_proveedor = sin_proveedor
        self._setup_ui()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        ancho = self._ancho_ventana_principal()
        self.resize(ancho, self.height())
        self._centrar_en_pantalla()

    def _centrar_en_pantalla(self) -> None:
        screen = QApplication.primaryScreen()
        if screen is None:
            return
        geo = screen.availableGeometry()
        frame = self.frameGeometry()
        self.move(geo.center().x() - frame.width() // 2,
                  geo.center().y() - frame.height() // 2)

    def _ancho_ventana_principal(self) -> int:
        app = QApplication.instance()
        ancho = 1400
        if app is not None:
            for w in app.topLevelWidgets():
                if w is self or not w.isVisible():
                    continue
                ancho = max(ancho, w.width())
        return ancho

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Buscar insumo...")
        layout.addWidget(self.txt_buscar)

        self.table = GorettiTable(
            columns=[
                {"key": "codigo", "label": "Código"},
                {"key": "nombre", "label": "Nombre", "stretch": True},
                {"key": "categoria", "label": "Categoría"},
                {"key": "stock_actual", "label": "Stock", "align": "right"},
            ],
        )
        self.table.recordDoubleClicked.connect(self._accept)

        ctrl = InventarioController()
        if self._proveedor_id is not None:
            insumos = ctrl.listar_insumos_de_proveedor(self._proveedor_id)
        elif self._sin_proveedor:
            insumos = ctrl.listar_insumos_sin_proveedor()
        else:
            insumos = ctrl.listar_insumos()
        self._insumos = insumos
        self._mostrar(insumos)

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

    def _mostrar(self, insumos: list[dict]) -> None:
        self.table.set_records(list(insumos))

    def _filtrar(self, texto: str) -> None:
        texto = texto.strip().lower()
        if not texto:
            self._mostrar(self._insumos)
            return
        filtrados = [
            ins for ins in self._insumos
            if texto in str(ins.get("codigo", "")).lower()
            or texto in str(ins.get("nombre", "")).lower()
            or texto in str(ins.get("categoria", "")).lower()
        ]
        self._mostrar(filtrados)

    def _accept(self) -> None:
        rec = self.table.current_record()
        if rec is not None:
            self._selected = rec
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
        info.addRow("Tipo:", QLabel(_tipo_documento(oc.get("tipo", "orden"))))
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
            ["Insumo", "Proveedor", "Tallas", "Cantidad", "Precio Unit.", "Subtotal"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(46)
        configurar_tabla_excel(self.table)

        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        self.table.setRowCount(len(detalle))
        for i, d in enumerate(detalle):
            self.table.setItem(i, 0, QTableWidgetItem(d.get("insumo_nombre", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("proveedor_nombre", "") or "—"))
            tallas = d.get("tallas", [])
            if tallas:
                texto_tallas = ", ".join(
                    f"T{t['talla']}: {t['pares']}"
                    + (f" (${float(t['precio']):,.2f})"
                       if float(t.get('precio', 0) or 0) > 0 else "")
                    for t in tallas)
                self.table.setItem(i, 2, QTableWidgetItem(texto_tallas))
            else:
                self.table.setItem(i, 2, QTableWidgetItem("—"))
            self.table.setItem(i, 3, QTableWidgetItem(str(d.get("cantidad", 0))))
            self.table.setItem(i, 4, QTableWidgetItem(f"${d.get('precio_unitario', 0):.2f}"))
            sub = _subtotal_detalle(d)
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
        info.addRow("Tipo:", QLabel(_tipo_documento(oc.get("tipo", "orden"))))
        info.addRow("Proveedor:", QLabel(oc.get("proveedor_nombre") or "Compra a inventario"))
        info.addRow("Fecha:", QLabel(oc.get("fecha_emision", "")))
        layout.addLayout(info)

        instruccion = QLabel("Verifique las cantidades. Ajuste si hay diferencias:")
        instruccion.setStyleSheet("font-weight: bold; color: #475569; margin-top: 8px;")
        layout.addWidget(instruccion)

        self.table = GorettiTable(
            columns=[
                {"key": "insumo_nombre", "label": "Insumo", "stretch": True},
                {"key": "proveedor_nombre", "label": "Proveedor", "stretch": True},
                {"key": "cantidad", "label": "Cant. Solicitada", "align": "right"},
                {"key": "recibida", "label": "Cant. Recibida", "widget": self._factory_recibida},
                {"key": "precio", "label": "Precio Unit.", "align": "right"},
                {"key": "subtotal", "label": "Subtotal", "align": "right"},
                {"key": "id", "label": "DetalleID", "hidden": True},
            ],
            sortable=False,
        )

        detalle = self.controller.obtener_detalle_orden(self.oc_id)
        self._detalle = detalle
        self.table.set_records([
            {"insumo_nombre": d.get("insumo_nombre", ""),
             "proveedor_nombre": d.get("proveedor_nombre", "") or "—",
             "cantidad": d.get("cantidad", 0),
             "recibida": d.get("cantidad", 0),
             "precio": f"${d.get('precio_unitario', 0):.2f}",
             "subtotal": f"${_subtotal_detalle(d):.2f}",
             "id": d.get("id", "")}
            for d in detalle
        ])

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

    def _factory_recibida(self, record: dict, row: int) -> QDoubleSpinBox:
        cant = float(record.get("cantidad", 0) or 0)
        spn = QDoubleSpinBox()
        spn.setRange(0, cant * 10)
        spn.setDecimals(2)
        spn.setValue(cant)
        spn.valueChanged.connect(self._on_cantidad_changed)
        return spn

    def _on_cantidad_changed(self) -> None:
        diferencias = False
        total = 0
        for i, d in enumerate(self._detalle):
            spn = self.table.cell_widget(i, "recibida")
            recibido = spn.value() if spn else d.get("cantidad", 0)
            solicitado = d.get("cantidad", 0)
            sub = _subtotal_recibido(d, recibido)
            self.table.set_cell_text(i, "subtotal", f"${sub:.2f}")
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
        recibidos = []
        for i, d in enumerate(self._detalle):
            spn = self.table.cell_widget(i, "recibida")
            recibido = spn.value() if spn else 0
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
            recibidos.append({"insumo_id": d["insumo_id"], "solicitado": d["cantidad"],
                              "recibido": recibido})

        estatus = "recibida_con_diferencias" if self._diferencias else "recibida"
        total = sum(
            _subtotal_recibido(d, self.table.cell_widget(i, "recibida").value()
                               if self.table.cell_widget(i, "recibida") else 0)
            for i, d in enumerate(self._detalle)
        )
        from src.database.db_manager import DatabaseManager
        db = DatabaseManager()
        db.execute(
            "UPDATE ordenes_compra SET estatus=?, fecha_recibido=datetime('now'), total=? WHERE id=?",
            (estatus, total, self.oc_id),
        )
        from src.utils.logs import registrar_log
        registrar_log("ordenes_compra", "recibir", "orden", self.oc_id,
                      datos={"estatus": estatus, "total": total,
                             "diferencias": self._diferencias, "detalle_recibido": recibidos})
        self.accept()


# ============================================================
# PRODUCCIÓN
# ============================================================

class DialogModelo(QDialog):
    def __init__(self, controller: ProduccionController, inv_controller: InventarioController,
                 modelo_id: int | None = None) -> None:
        super().__init__()
        self.controller = controller
        self.inv_controller = inv_controller
        self.modelo_id = modelo_id
        self.setWindowTitle("Nuevo Modelo" if modelo_id is None else "Editar Modelo")
        self.setMinimumWidth(560)
        self.setModal(True)
        self._combos: list[dict] = []
        self._setup_ui()
        if modelo_id:
            self._load_data()

    def _setup_ui(self) -> None:
        from src.utils.folios import siguiente_folio

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(12)

        self.txt_codigo = QLineEdit()
        self.txt_codigo.setText(siguiente_folio("modelos", "codigo", "MOD"))
        self.txt_codigo.setPlaceholderText("Ej: MOD-0001")
        self.txt_codigo.setReadOnly(True)
        self.txt_nombre = QLineEdit()
        self.txt_nombre.setPlaceholderText("Ej: Botín Vaquero, Bota Roper, etc.")
        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Descripción opcional")

        form.addRow("Código:", self.txt_codigo)
        form.addRow("Nombre:", self.txt_nombre)
        form.addRow("Descripción:", self.txt_desc)
        self.img_widget = WidgetImagen()
        form.addRow("Imagen:", self.img_widget)
        layout.addLayout(form)

        self.chk_variantes = QCheckBox("Generar variantes por talla")
        self.chk_variantes.toggled.connect(self._on_variantes_toggled)
        layout.addWidget(self.chk_variantes)

        self.frame_tallas = QFrame()
        self.frame_tallas.setObjectName("card")
        ft = QVBoxLayout(self.frame_tallas)
        ft.setContentsMargins(12, 12, 12, 12)
        ft.setSpacing(8)

        sel = QHBoxLayout()
        sel.addWidget(QLabel("De talla:"))
        self.cmb_desde = QComboBox()
        self.cmb_hasta = QComboBox()
        for t in self.controller.listar_tallas():
            self.cmb_desde.addItem(t["talla"], t["talla"])
            self.cmb_hasta.addItem(t["talla"], t["talla"])
        self.cmb_hasta.setCurrentIndex(max(0, self.cmb_hasta.count() - 1))
        sel.addWidget(self.cmb_desde)
        sel.addWidget(QLabel("a talla:"))
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
        ft.addLayout(sel)

        layout.addWidget(self.frame_tallas)
        self.frame_tallas.setVisible(False)

        self.chk_colores = QCheckBox("Variantes de color")
        self.chk_colores.toggled.connect(self._on_colores_toggled)
        layout.addWidget(self.chk_colores)

        self.frame_colores = QFrame()
        self.frame_colores.setObjectName("card")
        fc = QVBoxLayout(self.frame_colores)
        fc.setContentsMargins(12, 12, 12, 12)
        fc.setSpacing(8)
        fc.addWidget(QLabel("Seleccione los colores a generar:"))

        self._color_checks: list[tuple[QCheckBox, dict]] = []
        grid = QGridLayout()
        grid.setSpacing(8)
        for i, c in enumerate(self.inv_controller.listar_colores()):
            chk = QCheckBox(f"{c['nombre']} ({c['codigo']})")
            chk.setChecked(True)
            chk.toggled.connect(self._regenerar_variantes)
            self._color_checks.append((chk, c))
            grid.addWidget(chk, i // 3, i % 3)
        fc.addLayout(grid)

        layout.addWidget(self.frame_colores)
        self.frame_colores.setVisible(False)

        layout.addWidget(QLabel("Piel de las variantes (opcional):"))
        self.txt_piel = QLineEdit()
        self.txt_piel.setPlaceholderText("Ej: Vaquera, Gamuza, Industrial")
        layout.addWidget(self.txt_piel)

        self.frame_preview = QFrame()
        self.frame_preview.setObjectName("card")
        fpv = QVBoxLayout(self.frame_preview)
        fpv.setContentsMargins(12, 12, 12, 12)
        fpv.setSpacing(8)
        fpv.addWidget(QLabel("Previsualización de variantes:"))
        self.lst_variantes = QListWidget()
        self.lst_variantes.setMaximumHeight(150)
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

    def _load_data(self) -> None:
        m = self.controller.obtener_modelo(self.modelo_id)
        if m:
            self.txt_codigo.setText(m.get("codigo", ""))
            self.txt_nombre.setText(m.get("nombre", ""))
            self.txt_desc.setText(m.get("descripcion", ""))
            self.img_widget.set_imagen(
                self.controller.obtener_imagen_modelo(self.modelo_id))

    def _on_variantes_toggled(self, checked: bool) -> None:
        self.frame_tallas.setVisible(checked)
        self._regenerar_variantes()
        self._update_preview_visibility()

    def _on_colores_toggled(self, checked: bool) -> None:
        self.frame_colores.setVisible(checked)
        self._regenerar_variantes()
        self._update_preview_visibility()

    def _update_preview_visibility(self) -> None:
        self.frame_preview.setVisible(
            self.chk_variantes.isChecked() or self.chk_colores.isChecked())

    def _tallas_seleccionadas(self) -> list[str]:
        if not self.chk_variantes.isChecked():
            return []
        idx_d = self.cmb_desde.currentIndex()
        idx_h = self.cmb_hasta.currentIndex()
        if idx_d > idx_h:
            idx_d, idx_h = idx_h, idx_d
        return [self.cmb_desde.itemData(i) for i in range(idx_d, idx_h + 1)]

    def _colores_seleccionados(self) -> list[dict]:
        if not self.chk_colores.isChecked():
            return []
        return [c for chk, c in self._color_checks if chk.isChecked()]

    def _regenerar_variantes(self) -> None:
        base = self.txt_codigo.text().strip()
        self._combos = []
        self.lst_variantes.clear()
        if not base:
            self._update_count()
            return
        tallas = self._tallas_seleccionadas()
        colores = self._colores_seleccionados()
        if tallas and colores:
            combos = [{"talla": t, "color": c["nombre"], "codigo_color": c["codigo"]}
                      for t in tallas for c in colores]
            codigos = [f"{base}-{co['talla']}-{co['codigo_color']}" for co in combos]
        elif tallas:
            combos = [{"talla": t, "color": "", "codigo_color": ""} for t in tallas]
            codigos = [f"{base}-{co['talla']}" for co in combos]
        elif colores:
            combos = [{"talla": "", "color": c["nombre"], "codigo_color": c["codigo"]}
                      for c in colores]
            codigos = [f"{base}-{co['codigo_color']}" for co in combos]
        else:
            combos, codigos = [], []
        for co, cod in zip(combos, codigos):
            co["codigo"] = cod
            self.lst_variantes.addItem(cod)
        self._combos = combos
        self._update_count()

    def _limpiar_variantes(self) -> None:
        self._combos = []
        self.lst_variantes.clear()
        self._update_count()

    def _update_count(self) -> None:
        n = len(self._combos)
        self.lbl_variantes_count.setText(
            f"{n} variante{'s' if n != 1 else ''} generada{'s' if n != 1 else ''}")

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        nombre = self.txt_nombre.text().strip()
        if not codigo or not nombre:
            QMessageBox.warning(self, "Campos requeridos", "Código y nombre son obligatorios.")
            return

        existentes_modelo: set[str] = set()
        if self.modelo_id:
            existentes_modelo = {v["codigo_variante"]
                                 for v in self.controller.listar_variantes(self.modelo_id)}

        combos: list[dict] = []
        conflictos: list[str] = []
        for c in self._combos:
            if c["codigo"] in existentes_modelo:
                continue
            if self.controller.existe_codigo_variante(c["codigo"]):
                conflictos.append(c["codigo"])
            else:
                combos.append(c)
        if conflictos:
            QMessageBox.warning(
                self, "Códigos existentes",
                "Los siguientes códigos de variante ya existen en otros modelos:\n\n"
                + "\n".join(conflictos)
                + "\n\nAjuste el código base o la selección de variantes.")
            return

        if self.modelo_id:
            self.controller.actualizar_modelo(self.modelo_id, codigo, nombre,
                                              self.txt_desc.text().strip(),
                                              self.img_widget.get_imagen())
            modelo_id = self.modelo_id
        else:
            modelo_id = self.controller.crear_modelo(codigo, nombre,
                                                     self.txt_desc.text().strip(),
                                                     self.img_widget.get_imagen())

        piel = self.txt_piel.text().strip()
        for c in combos:
            self.controller.crear_variante(modelo_id, c["color"], piel, c["talla"], c["codigo"])
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
        self.txt_codigo.setReadOnly(True)
        self.txt_color = QLineEdit()
        self.txt_color.setPlaceholderText("Ej: Negro, Café, Blanco")
        self.cmb_talla = QComboBox()
        self.cmb_talla.setEditable(True)
        self.cmb_talla.addItem("")
        for t in self.controller.listar_tallas():
            self.cmb_talla.addItem(t["talla"])
        self.cmb_talla.setPlaceholderText("Ej: 25, 25.5 (opcional)")
        self.txt_piel = QLineEdit()
        self.txt_piel.setPlaceholderText("Ej: Vaquera, Gamuza, Industrial")

        form.addRow("Modelo:", self.cmb_modelo)
        form.addRow("Código Variante:", self.txt_codigo)
        form.addRow("Color:", self.txt_color)
        form.addRow("Talla:", self.cmb_talla)
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
            idx = self.cmb_talla.findText(v.get("talla", ""))
            if idx >= 0:
                self.cmb_talla.setCurrentIndex(idx)
            else:
                self.cmb_talla.setEditText(v.get("talla", ""))
            self.txt_piel.setText(v.get("piel", ""))

    def _save(self) -> None:
        codigo = self.txt_codigo.text().strip()
        color = self.txt_color.text().strip()
        piel = self.txt_piel.text().strip()
        talla = self.cmb_talla.currentText().strip()
        if not codigo or not color:
            QMessageBox.warning(self, "Campos requeridos", "Código y color son obligatorios.")
            return
        if self.variante_id:
            self.controller.actualizar_variante(self.variante_id, self.cmb_modelo.currentData(),
                                                 color, piel, talla, codigo)
        else:
            self.controller.crear_variante(self.cmb_modelo.currentData(), color, piel, talla, codigo)
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

        self.table = GorettiTable(
            columns=[
                {"key": "insumo_nombre", "label": "Insumo", "stretch": True},
                {"key": "cantidad_por_par", "label": "Cantidad por Par", "widget": self._factory_cantidad_bom},
                {"key": "unidad", "label": "Unidad", "widget": self._factory_unidad_bom},
                {"key": "id", "label": "InsumoID", "hidden": True},
            ],
            sortable=False,
        )

        self._cargar_bom()

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

    def _factory_cantidad_bom(self, record: dict, row: int) -> QDoubleSpinBox:
        spn = QDoubleSpinBox()
        spn.setRange(0, 999999)
        spn.setDecimals(2)
        spn.setValue(float(record.get("cantidad_por_par", 0) or 0))
        return spn

    def _factory_unidad_bom(self, record: dict, row: int) -> QComboBox:
        cmb = QComboBox()
        for u in self.controller.listar_unidades():
            cmb.addItem(u["abreviatura"], u["nombre"])
        idx = cmb.findText(record.get("unidad", "pieza"))
        if idx >= 0:
            cmb.setCurrentIndex(idx)
        return cmb

    def _cargar_bom(self) -> None:
        bom = self.controller.obtener_bom(self.modelo_id)
        self.table.set_records([
            {"insumo_nombre": b.get("insumo_nombre", ""),
             "cantidad_por_par": b.get("cantidad_por_par", 0),
             "unidad": b.get("unidad_medida", "") or "pieza",
             "id": b.get("insumo_id", "")}
            for b in bom
        ])

    def _agregar(self) -> None:
        dlg = DialogSeleccionarInsumo(self)
        if dlg.exec() == QDialog.Accepted:
            ins = dlg.get_seleccion()
            if ins:
                self.table.add_row({
                    "insumo_nombre": ins["nombre"], "cantidad_por_par": 1,
                    "unidad": "pieza", "id": ins["id"],
                })

    def _quitar(self) -> None:
        row = self.table.current_row()
        if row >= 0:
            self.table.remove_row(row)

    def _save(self) -> None:
        insumos = []
        for row in range(self.table.row_count()):
            spn = self.table.cell_widget(row, "cantidad_por_par")
            cmb = self.table.cell_widget(row, "unidad")
            insumos.append({
                "insumo_id": int(self.table.cell_text(row, "id")),
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
        self.txt_folio.setReadOnly(True)

        self.cmb_variante = QComboBox()
        variantes = self.controller.listar_variantes()
        for v in variantes:
            detalle = f"{v['color']}/{v['piel']}"
            if v.get("talla"):
                detalle += f"/T{v['talla']}"
            self.cmb_variante.addItem(
                f"{v['codigo_variante']} - {v.get('modelo_nombre', '')} ({detalle})",
                v["id"],
            )

        from PySide6.QtCore import QDate
        self.dte_inicio = DatePicker()
        self.dte_entrega = DatePicker(QDate.currentDate().addDays(7))

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

        self._tallas = self.controller.listar_tallas()
        self._matriz_tallas: dict[int, int] = {}
        tallas_row = QHBoxLayout()
        btn_tallas = QPushButton("Configurar Tallas")
        btn_tallas.setObjectName("btnPrimary")
        btn_tallas.clicked.connect(self._configurar_tallas)
        tallas_row.addWidget(btn_tallas)
        self.lbl_total = QLabel("Total de pares: 0")
        self.lbl_total.setStyleSheet(
            "font-weight: bold; font-size: 13px; color: #4f46e5;")
        tallas_row.addWidget(self.lbl_total)
        tallas_row.addStretch()
        layout.addLayout(tallas_row)

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

    def _configurar_tallas(self) -> None:
        """Abre el componente aprobado de tallas (misma apariencia en toda la app)."""
        from src.components.tallas_matrix import MatrizTallasDialog
        dlg = MatrizTallasDialog(
            tallas=self._tallas, titulo="MATRIZ DE TALLAS", parent=self)
        dlg.establecer_valores(
            {str(tid): pr for tid, pr in self._matriz_tallas.items()})
        if dlg.exec() == QDialog.Accepted:
            valores = dlg.obtener_valores()  # dict[str, int] por talla_id
            self._matriz_tallas = {
                int(tid): pr for tid, pr in valores.items() if pr > 0}
            self.lbl_total.setText(
                f"Total de pares: {sum(self._matriz_tallas.values())}")

    def _save(self) -> None:
        folio = self.txt_folio.text().strip()
        if not folio:
            QMessageBox.warning(self, "Campo requerido", "El folio es obligatorio.")
            return
        if self.cmb_variante.count() == 0:
            QMessageBox.warning(self, "Sin variantes", "Cree al menos una variante primero.")
            return

        matriz = []
        for talla_id, pares in self._matriz_tallas.items():
            if pares > 0:
                matriz.append({"talla_id": talla_id, "pares": pares})

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
            self.dte_inicio.fecha_bd(),
            self.dte_entrega.fecha_bd(),
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
        self.table = GorettiTable(
            columns=[
                {"key": "estacion_nombre", "label": "Estación", "stretch": True},
                {"key": "fecha_entrada", "label": "Entrada"},
                {"key": "fecha_salida", "label": "Salida"},
                {"key": "pares_procesados", "label": "Procesados", "align": "right"},
                {"key": "estatus", "label": "Estatus"},
            ],
            foreground_fn=self._color_estatus,
        )
        self._cargar_seguimiento()

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

    def _color_estatus(self, record: dict, key: str) -> QColor | None:
        if key == "estatus":
            if record.get("estatus_raw") == "completado":
                return QColor("#15803d")
            if record.get("estatus_raw") == "en_proceso":
                return QColor("#ca8a04")
        return None

    def _cargar_seguimiento(self) -> None:
        seguimiento = self.controller.obtener_seguimiento(self.op_id)
        self.table.set_records([
            {"estacion_nombre": s.get("estacion_nombre", ""),
             "fecha_entrada": s.get("fecha_entrada", "") or "-",
             "fecha_salida": s.get("fecha_salida", "") or "-",
             "pares_procesados": s.get("pares_procesados", 0) or 0,
             "estatus": s.get("estatus", "").capitalize(),
             "estatus_raw": s.get("estatus", "")}
            for s in seguimiento
        ])

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
            self._cargar_seguimiento()


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
