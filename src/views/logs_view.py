"""Vista de logs del sistema — solo accesible para administradores."""

from PySide6.QtCore import Qt, QDateTime
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDateTimeEdit, QFrame, QHBoxLayout, QHeaderView,
    QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout,
)

from src.controllers.logs_controller import LogsController


_NIVEL_COLORES = {
    "info": "#1F2937",
    "warning": "#D97706",
    "error": "#DC2626",
    "debug": "#6B7280",
}


class DialogLogs(QDialog):
    """Diálogo modal que muestra los logs de auditoría del sistema."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Logs del Sistema")
        self.setMinimumSize(1000, 600)
        self.setModal(True)
        self._ctrl = LogsController()
        self._setup_ui()
        self._cargar_filtros()
        self._cargar_datos()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        header = QHBoxLayout()
        titulo = QLabel("Logs de Auditoría del Sistema")
        titulo.setObjectName("sectionTitle")
        header.addWidget(titulo)
        header.addStretch()

        btn_limpiar = QPushButton("Limpiar Logs")
        btn_limpiar.setObjectName("btnDanger")
        btn_limpiar.setCursor(Qt.PointingHandCursor)
        btn_limpiar.clicked.connect(self._limpiar_logs)
        header.addWidget(btn_limpiar)

        btn_exportar = QPushButton("Exportar")
        btn_exportar.setObjectName("btnSecondary")
        btn_exportar.setCursor(Qt.PointingHandCursor)
        btn_exportar.clicked.connect(self._exportar)
        header.addWidget(btn_exportar)

        layout.addLayout(header)

        filtros_frame = QFrame()
        filtros_frame.setObjectName("card")
        filtros_layout = QHBoxLayout(filtros_frame)
        filtros_layout.setContentsMargins(12, 10, 12, 10)
        filtros_layout.setSpacing(10)

        filtros_layout.addWidget(QLabel("Buscar:"))
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("Texto libre...")
        self.txt_buscar.setMinimumWidth(180)
        self.txt_buscar.textChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.txt_buscar)

        filtros_layout.addWidget(QLabel("Módulo:"))
        self.cmb_modulo = QComboBox()
        self.cmb_modulo.setMinimumWidth(130)
        self.cmb_modulo.currentTextChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.cmb_modulo)

        filtros_layout.addWidget(QLabel("Acción:"))
        self.cmb_accion = QComboBox()
        self.cmb_accion.setMinimumWidth(130)
        self.cmb_accion.currentTextChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.cmb_accion)

        filtros_layout.addWidget(QLabel("Nivel:"))
        self.cmb_nivel = QComboBox()
        self.cmb_nivel.addItems(["Todos", "info", "warning", "error", "debug"])
        self.cmb_nivel.setMinimumWidth(90)
        self.cmb_nivel.currentTextChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.cmb_nivel)

        filtros_layout.addWidget(QLabel("Desde:"))
        self.dt_desde = QDateTimeEdit()
        self.dt_desde.setDisplayFormat("yyyy-MM-dd")
        self.dt_desde.setCalendarPopup(True)
        self.dt_desde.setDateTime(QDateTime.currentDateTime().addDays(-30))
        self.dt_desde.dateChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.dt_desde)

        filtros_layout.addWidget(QLabel("Hasta:"))
        self.dt_hasta = QDateTimeEdit()
        self.dt_hasta.setDisplayFormat("yyyy-MM-dd")
        self.dt_hasta.setCalendarPopup(True)
        self.dt_hasta.setDateTime(QDateTime.currentDateTime())
        self.dt_hasta.dateChanged.connect(self._cargar_datos)
        filtros_layout.addWidget(self.dt_hasta)

        layout.addWidget(filtros_frame)

        self._lbl_contador = QLabel("")
        self._lbl_contador.setStyleSheet("color: #6B7280; font-size: 11px;")
        layout.addWidget(self._lbl_contador)

        self.tabla = QTableWidget()
        self.tabla.setColumnCount(8)
        self.tabla.setHorizontalHeaderLabels([
            "ID", "Fecha", "Usuario", "Módulo", "Acción",
            "Entidad", "Detalle", "Nivel",
        ])
        self.tabla.horizontalHeader().setSectionResizeMode(
            QHeaderView.Stretch)
        self.tabla.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeToContents)
        self.tabla.setSelectionBehavior(QTableWidget.SelectRows)
        self.tabla.setEditTriggers(QTableWidget.NoEditTriggers)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.doubleClicked.connect(self._ver_detalle)
        layout.addWidget(self.tabla, 1)

        footer = QHBoxLayout()
        footer.addStretch()
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.setObjectName("btnSecondary")
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.clicked.connect(self.accept)
        footer.addWidget(btn_cerrar)
        layout.addLayout(footer)

    def _cargar_filtros(self) -> None:
        modulos = self._ctrl.modulos_registrados()
        self.cmb_modulo.clear()
        self.cmb_modulo.addItem("Todos")
        for m in modulos:
            self.cmb_modulo.addItem(m)

        self._recargar_acciones()

    def _recargar_acciones(self) -> None:
        modulo = self.cmb_modulo.currentText()
        if modulo == "Todos":
            modulo = None
        acciones = self._ctrl.acciones_registradas(modulo)
        self.cmb_accion.blockSignals(True)
        self.cmb_accion.clear()
        self.cmb_accion.addItem("Todas")
        for a in acciones:
            self.cmb_accion.addItem(a)
        self.cmb_accion.blockSignals(False)

    def _obtener_filtros(self) -> dict:
        filtros: dict = {}
        termino = self.txt_buscar.text().strip()
        if termino:
            filtros["termino"] = termino
        modulo = self.cmb_modulo.currentText()
        if modulo != "Todos":
            filtros["modulo"] = modulo
        accion = self.cmb_accion.currentText()
        if accion != "Todas":
            filtros["accion"] = accion
        nivel = self.cmb_nivel.currentText()
        if nivel != "Todos":
            filtros["nivel"] = nivel
        filtros["desde"] = self.dt_desde.date().toString("yyyy-MM-dd")
        filtros["hasta"] = self.dt_hasta.date().toString("yyyy-MM-dd")
        return filtros

    def _cargar_datos(self) -> None:
        self._recargar_acciones()
        filtros = self._obtener_filtros()
        registros = self._ctrl.listar_logs(filtros)
        self.tabla.setRowCount(len(registros))
        for fila, log in enumerate(registros):
            self.tabla.setItem(fila, 0, QTableWidgetItem(str(log.get("id", ""))))
            self.tabla.setItem(fila, 1, QTableWidgetItem(log.get("fecha", "")))
            self.tabla.setItem(fila, 2, QTableWidgetItem(log.get("usuario", "")))
            self.tabla.setItem(fila, 3, QTableWidgetItem(log.get("modulo", "")))
            self.tabla.setItem(fila, 4, QTableWidgetItem(log.get("accion", "")))
            entidad = log.get("entidad", "")
            eid = log.get("entidad_id", "")
            texto_entidad = f"{entidad} (ID {eid})" if eid else entidad
            self.tabla.setItem(fila, 5, QTableWidgetItem(texto_entidad))
            self.tabla.setItem(fila, 6, QTableWidgetItem(log.get("detalle", "")))
            nivel_item = QTableWidgetItem(log.get("nivel", "info"))
            color = _NIVEL_COLORES.get(log.get("nivel", ""), "#1F2937")
            nivel_item.setForeground(Qt.GlobalColor(0))
            nivel_item.setData(Qt.UserRole, color)
            self.tabla.setItem(fila, 7, nivel_item)
        total = len(registros)
        self._lbl_contador.setText(
            f"{total} registro{'s' if total != 1 else ''} encontrado{'s' if total != 1 else ''}")

    def _ver_detalle(self) -> None:
        row = self.tabla.currentRow()
        if row < 0:
            return
        id_item = self.tabla.item(row, 0)
        if not id_item:
            return

        fecha = self.tabla.item(row, 1).text() if self.tabla.item(row, 1) else ""
        usuario = self.tabla.item(row, 2).text() if self.tabla.item(row, 2) else ""
        modulo = self.tabla.item(row, 3).text() if self.tabla.item(row, 3) else ""
        accion = self.tabla.item(row, 4).text() if self.tabla.item(row, 4) else ""
        entidad = self.tabla.item(row, 5).text() if self.tabla.item(row, 5) else ""
        detalle = self.tabla.item(row, 6).text() if self.tabla.item(row, 6) else ""
        nivel = self.tabla.item(row, 7).text() if self.tabla.item(row, 7) else ""

        registros = self._ctrl.listar_logs(self._obtener_filtros())
        log_id = int(id_item.text())
        datos_extra = {}
        metadata_extra = {}
        for reg in registros:
            if reg.get("id") == log_id:
                import json
                try:
                    datos_extra = json.loads(reg.get("datos") or "{}")
                except (json.JSONDecodeError, TypeError):
                    datos_extra = {}
                try:
                    metadata_extra = json.loads(reg.get("metadata") or "{}")
                except (json.JSONDecodeError, TypeError):
                    metadata_extra = {}
                break

        lineas = [
            f"Fecha: {fecha}",
            f"Usuario: {usuario}",
            f"Módulo: {modulo}",
            f"Acción: {accion}",
            f"Entidad: {entidad}",
            f"Nivel: {nivel}",
            f"Detalle: {detalle}",
            "",
            "--- Datos ---",
        ]
        for k, v in datos_extra.items():
            lineas.append(f"  {k}: {v}")
        lineas.append("")
        lineas.append("--- Metadata ---")
        for k, v in metadata_extra.items():
            lineas.append(f"  {k}: {v}")

        QMessageBox.information(self, f"Detalle del Log #{log_id}", "\n".join(lineas))

    def _limpiar_logs(self) -> None:
        respuesta = QMessageBox.question(
            self, "Limpiar Logs",
            "¿Está seguro de eliminar TODOS los logs del sistema?\n"
            "Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if respuesta == QMessageBox.Yes:
            eliminados = self._ctrl.limpiar()
            self._cargar_filtros()
            self._cargar_datos()
            QMessageBox.information(
                self, "Logs Limpiados",
                f"Se eliminaron {eliminados} registros.")

    def _exportar(self) -> None:
        from src.utils.export_utils import export_table_to_excel
        headers = [
            "ID", "Fecha", "Usuario", "Módulo", "Acción",
            "Entidad", "Detalle", "Nivel",
        ]
        datos = []
        for fila in range(self.tabla.rowCount()):
            row_data = []
            for col in range(self.tabla.columnCount()):
                item = self.tabla.item(fila, col)
                row_data.append(item.text() if item else "")
            datos.append(row_data)
        export_table_to_excel(
            "Logs_Sistema.xlsx", headers, datos,
            "Logs de Auditoría del Sistema", "Reporte generado desde SIAC ERP")
        QMessageBox.information(
            self, "Exportar", "Archivo Excel generado exitosamente.")
