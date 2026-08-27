"""Vista del Dashboard de Super Admin.

Muestra estadisticas globales, lista de empresas con metricas
y usuarios por empresa. Solo accesible con rol super_admin.
"""
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from src.controllers.super_admin_controller import SuperAdminController


class TarjetaKPI(QFrame):
    """Tarjeta de indicador clave."""

    def __init__(self, titulo: str, color: str = "#0D9488",
                 parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.setMinimumHeight(90)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)

        self.lbl_titulo = QLabel(titulo.upper())
        self.lbl_titulo.setStyleSheet(
            f"color: {color}; font-size: 10px; font-weight: bold; letter-spacing: 1px;")
        lay.addWidget(self.lbl_titulo)

        self.lbl_valor = QLabel("—")
        self.lbl_valor.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #0f172a;")
        lay.addWidget(self.lbl_valor)

    def establecer(self, valor: str) -> None:
        self.lbl_valor.setText(valor)


def _tabla(columnas: list[str], anchos: list[int]) -> QTableWidget:
    """Crea una tabla simple."""
    tabla = QTableWidget(0, len(columnas))
    tabla.setHorizontalHeaderLabels(columnas)
    tabla.verticalHeader().setVisible(False)
    tabla.setEditTriggers(QTableWidget.NoEditTriggers)
    tabla.setSelectionBehavior(QTableWidget.SelectRows)
    tabla.setAlternatingRowColors(True)
    tabla.setSortingEnabled(True)
    for c, ancho in enumerate(anchos):
        tabla.setColumnWidth(c, ancho)
    return tabla


def _fila(tabla: QTableWidget, valores: list[str],
          alineaciones: dict[int, Qt.AlignmentFlag] | None = None) -> None:
    """Agrega una fila a la tabla."""
    r = tabla.rowCount()
    tabla.insertRow(r)
    alineaciones = alineaciones or {}
    for c, texto in enumerate(valores):
        item = QTableWidgetItem(texto)
        if c in alineaciones:
            item.setTextAlignment(alineaciones[c])
        tabla.setItem(r, c, item)


class SuperAdminView(QWidget):
    """Dashboard de super_admin con estadisticas multi-empresa."""

    navegar_modulo = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = SuperAdminController()
        self._empresa_seleccionada: str | None = None
        self._setup_ui()
        self.recargar()

    def _setup_ui(self) -> None:
        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setFrameShape(QFrame.NoFrame)
        contenido = QWidget()
        cl = QVBoxLayout(contenido)
        cl.setContentsMargins(16, 12, 16, 16)
        cl.setSpacing(12)

        # Encabezado
        fila_header = QHBoxLayout()
        titulo = QLabel("Panel de Administracion")
        titulo.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #0f172a;")
        self.lbl_fecha = QLabel("")
        self.lbl_fecha.setStyleSheet("color: #64748b;")
        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setObjectName("btnSecondary")
        btn_actualizar.setCursor(Qt.PointingHandCursor)
        btn_actualizar.clicked.connect(self.recargar)
        fila_header.addWidget(titulo)
        fila_header.addStretch()
        fila_header.addWidget(self.lbl_fecha)
        fila_header.addWidget(btn_actualizar)
        cl.addLayout(fila_header)

        # Tarjetas KPI globales
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(10)
        self.card_empresas = TarjetaKPI("Empresas", "#7C3AED")
        self.card_usuarios = TarjetaKPI("Usuarios total", "#2563EB")
        self.card_insumos = TarjetaKPI("Insumos total", "#16A34A")
        self.card_ocs = TarjetaKPI("OCs total", "#EA580C")
        self.card_ops = TarjetaKPI("OPs total", "#DC2626")
        for c, card in enumerate([
            self.card_empresas, self.card_usuarios,
            self.card_insumos, self.card_ocs, self.card_ops
        ]):
            grid_kpi.addWidget(card, 0, c)
        cl.addLayout(grid_kpi)

        # Tabla de empresas
        grp_empresas = QFrame()
        grp_empresas.setObjectName("card")
        el = QVBoxLayout(grp_empresas)
        el.setContentsMargins(8, 8, 8, 8)

        lbl_emp = QLabel("Empresas Registradas")
        lbl_emp.setStyleSheet("font-weight: bold; color: #334155; font-size: 14px;")
        el.addWidget(lbl_emp)

        self.tabla_empresas = _tabla(
            ["Nombre", "RFC", "Estado", "Usuarios", "Insumos", "OCs", "OPs", "Acciones"],
            [180, 120, 80, 80, 80, 80, 80, 120])
        self.tabla_empresas.cellClicked.connect(self._on_empresa_clic)
        el.addWidget(self.tabla_empresas)
        cl.addWidget(grp_empresas, 3)

        # Tabla de usuarios
        grp_usuarios = QFrame()
        grp_usuarios.setObjectName("card")
        ul = QVBoxLayout(grp_usuarios)
        ul.setContentsMargins(8, 8, 8, 8)

        lbl_usu = QLabel("Usuarios del Sistema")
        lbl_usu.setStyleSheet("font-weight: bold; color: #334155; font-size: 14px;")
        self.lbl_detalle_empresa = QLabel("")
        self.lbl_detalle_empresa.setStyleSheet("color: #64748b; font-size: 11px;")
        ul.addWidget(lbl_usu)
        ul.addWidget(self.lbl_detalle_empresa)

        self.tabla_usuarios = _tabla(
            ["Username", "Nombre", "Rol", "Estado", "Empresa ID"],
            [120, 200, 100, 80, 280])
        ul.addWidget(self.tabla_usuarios)
        cl.addWidget(grp_usuarios, 2)

        area.setWidget(contenido)
        raiz.addWidget(area)

    def _on_empresa_clic(self, fila: int, _columna: int) -> None:
        """Muestra los usuarios de la empresa seleccionada."""
        nombre_item = self.tabla_empresas.item(fila, 0)
        if not nombre_item:
            return
        nombre = nombre_item.text()

        # Buscar empresa_id de la tabla de usuarios
        for col in range(self.tabla_usuarios.columnCount()):
            item = self.tabla_usuarios.item(0, col)
            if item and item.text() == "Empresa ID":
                break

        # Obtener empresa_id de la tabla de empresas (ynamo hidden)
        # Usamos el dato guardado
        if hasattr(self, '_empresas_datos') and fila < len(self._empresas_datos):
            eid = self._empresas_datos[fila]['id']
            self._empresa_seleccionada = eid
            usuarios = self.controller.obtener_usuarios_empresa(eid)
            self.lbl_detalle_empresa.setText(
                f"Empresa: {nombre} ({len(usuarios)} usuarios)")
            self._cargar_tabla_usuarios(usuarios)

    def _toggle_empresa(self, empresa_id: str, activo_actual: bool, nombre: str) -> None:
        """Activa o desactiva una empresa."""
        nuevo_estado = not activo_actual
        accion = "activar" if nuevo_estado else "desactivar"

        respuesta = QMessageBox.question(
            self,
            f"{accion.title()} empresa",
            f"¿Desea {accion} la empresa '{nombre}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if respuesta != QMessageBox.Yes:
            return

        resultado = self.controller.cambiar_estado_empresa(empresa_id, nuevo_estado)

        if resultado.get('ok'):
            QMessageBox.information(
                self, "Exito",
                f"Empresa '{nombre}' {accion}da correctamente.")
            self.recargar()
        else:
            QMessageBox.warning(
                self, "Error",
                f"No se pudo {accion} la empresa: {resultado.get('error', 'Error desconocido')}")

    def _cargar_tabla_usuarios(self, usuarios: list[dict]) -> None:
        """Carga la tabla de usuarios."""
        self.tabla_usuarios.setRowCount(0)
        for u in usuarios:
            estado = "Activo" if u.get('activo', True) else "Inactivo"
            _fila(self.tabla_usuarios, [
                u.get('username', ''),
                u.get('nombre_completo', ''),
                u.get('rol', ''),
                estado,
                u.get('empresa_id', '')[:8] + '...' if u.get('empresa_id') else 'NULL',
            ])

    def recargar(self) -> None:
        """Recarga todos los datos."""
        self.lbl_fecha.setText(
            datetime.now().strftime("Actualizado: %d/%m/%Y %H:%M"))

        try:
            # Estadisticas globales
            stats = self.controller.obtener_estadisticas_globales()
            self.card_empresas.establecer(str(stats['total_empresas']))
            self.card_usuarios.establecer(str(stats['total_usuarios']))
            self.card_insumos.establecer(str(stats['total_insumos']))
            self.card_ocs.establecer(str(stats['total_ocs']))
            self.card_ops.establecer(str(stats['total_ops']))

            # Tabla de empresas
            empresas = self.controller.obtener_empresas_con_estadisticas()
            self._empresas_datos = empresas
            self.tabla_empresas.setRowCount(0)
            for idx, emp in enumerate(empresas):
                estado = "Activa" if emp.get('activo', True) else "Inactiva"
                _fila(self.tabla_empresas, [
                    emp.get('nombre', ''),
                    emp.get('rfc', '') or '—',
                    estado,
                    str(emp.get('usuarios', 0)),
                    str(emp.get('insumos', 0)),
                    str(emp.get('ocs', 0)),
                    str(emp.get('ops', 0)),
                    '',  # Columna de acciones
                ], {3: Qt.AlignCenter, 4: Qt.AlignCenter,
                    5: Qt.AlignCenter, 6: Qt.AlignCenter})
                # Boton de activar/desactivar
                btn = QPushButton("Desactivar" if emp.get('activo', True) else "Activar")
                btn.setObjectName("btnSecondary")
                btn.setFixedHeight(28)
                btn.setCursor(Qt.PointingHandCursor)
                eid = emp['id']
                activo = emp.get('activo', True)
                nombre = emp.get('nombre', '')
                btn.clicked.connect(
                    lambda checked=False, _eid=eid, _activo=activo, _n=nombre:
                    self._toggle_empresa(_eid, _activo, _n))
                self.tabla_empresas.setCellWidget(idx, 7, btn)

            # Todos los usuarios
            usuarios = self.controller.obtener_todos_usuarios()
            self.tabla_usuarios.setRowCount(0)
            self.lbl_detalle_empresa.setText(
                f"Mostrando todos los usuarios ({len(usuarios)} total)")
            self._cargar_tabla_usuarios(usuarios)

        except Exception as e:
            self.card_empresas.establecer("Error")
            print(f"Error en dashboard super_admin: {e}")
