"""Vista del Dashboard de Super Admin.

Muestra estadisticas locales, info de la empresa, lista de empresas
en Supabase (si esta configurado) y permite gestionar usuarios.
Solo accesible con rol super_admin.
"""
from datetime import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
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
            f"color: {color}; font-size: 10px; font-weight: bold; "
            "letter-spacing: 1px;")
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


class SuperAdminView(QWidget):
    """Dashboard de super_admin con estadisticas y gestion."""

    navegar_modulo = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = SuperAdminController()
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

        # --- Encabezado ---
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

        # --- Info de empresa local ---
        grp_empresa = QFrame()
        grp_empresa.setObjectName("card")
        el = QVBoxLayout(grp_empresa)
        el.setContentsMargins(12, 10, 12, 10)
        lbl_emp = QLabel("Empresa (Local)")
        lbl_emp.setStyleSheet(
            "font-weight: bold; color: #334155; font-size: 14px;")
        el.addWidget(lbl_emp)

        self.lbl_empresa_nombre = QLabel("—")
        self.lbl_empresa_nombre.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #0f172a;")
        el.addWidget(self.lbl_empresa_nombre)

        self.lbl_empresa_info = QLabel("")
        self.lbl_empresa_info.setStyleSheet(
            "color: #64748b; font-size: 12px;")
        self.lbl_empresa_info.setWordWrap(True)
        el.addWidget(self.lbl_empresa_info)

        # Boton activar/desactivar empresa local
        fila_empresa_btn = QHBoxLayout()
        self.lbl_empresa_estado = QLabel("")
        self.lbl_empresa_estado.setStyleSheet(
            "font-size: 13px; font-weight: bold;")
        self.btn_empresa_toggle = QPushButton("Desactivar")
        self.btn_empresa_toggle.setObjectName("btnSecondary")
        self.btn_empresa_toggle.setFixedHeight(30)
        self.btn_empresa_toggle.setCursor(Qt.PointingHandCursor)
        self.btn_empresa_toggle.clicked.connect(self._toggle_empresa_local)
        fila_empresa_btn.addWidget(self.lbl_empresa_estado)
        fila_empresa_btn.addStretch()
        fila_empresa_btn.addWidget(self.btn_empresa_toggle)
        el.addLayout(fila_empresa_btn)

        self.lbl_supabase = QLabel("")
        self.lbl_supabase.setStyleSheet(
            "color: #7C3AED; font-size: 11px; font-weight: bold;")
        el.addWidget(self.lbl_supabase)

        cl.addWidget(grp_empresa)

        # --- Tarjetas KPI ---
        grid_kpi = QGridLayout()
        grid_kpi.setSpacing(10)
        self.card_usuarios = TarjetaKPI("Usuarios", "#7C3AED")
        self.card_insumos = TarjetaKPI("Insumos activos", "#16A34A")
        self.card_ocs = TarjetaKPI("Ordenes de Compra", "#EA580C")
        self.card_ops = TarjetaKPI("Ordenes de Produccion", "#DC2626")
        self.card_modelos = TarjetaKPI("Modelos", "#2563EB")
        for c, card in enumerate([
            self.card_usuarios, self.card_insumos,
            self.card_ocs, self.card_ops, self.card_modelos
        ]):
            grid_kpi.addWidget(card, 0, c)
        cl.addLayout(grid_kpi)

        # --- Tabla de empresas Supabase (si configurado) ---
        self.grp_empresas_sb = QFrame()
        self.grp_empresas_sb.setObjectName("card")
        ebl = QVBoxLayout(self.grp_empresas_sb)
        ebl.setContentsMargins(8, 8, 8, 8)

        lbl_emp_sb = QLabel("Empresas en Supabase")
        lbl_emp_sb.setStyleSheet(
            "font-weight: bold; color: #334155; font-size: 14px;")
        ebl.addWidget(lbl_emp_sb)

        self.tabla_empresas = _tabla(
            ["Nombre", "RFC", "Estado", "ID"],
            [200, 120, 100, 300])
        self.tabla_empresas.cellClicked.connect(self._on_empresa_clic)
        ebl.addWidget(self.tabla_empresas)
        cl.addWidget(self.grp_empresas_sb)

        # --- Tabla de usuarios ---
        grp_usuarios = QFrame()
        grp_usuarios.setObjectName("card")
        ul = QVBoxLayout(grp_usuarios)
        ul.setContentsMargins(8, 8, 8, 8)

        lbl_usu = QLabel("Usuarios del Sistema (Local)")
        lbl_usu.setStyleSheet(
            "font-weight: bold; color: #334155; font-size: 14px;")
        self.lbl_detalle = QLabel("")
        self.lbl_detalle.setStyleSheet(
            "color: #64748b; font-size: 11px;")
        ul.addWidget(lbl_usu)
        ul.addWidget(self.lbl_detalle)

        self.tabla_usuarios = _tabla(
            ["ID", "Username", "Nombre", "Rol", "Estado", "Acciones"],
            [50, 130, 200, 120, 80, 120])
        ul.addWidget(self.tabla_usuarios)
        cl.addWidget(grp_usuarios, 3)

        area.setWidget(contenido)
        raiz.addWidget(area)

    # ----------------------------------------------------------------
    # Empresa local
    # ----------------------------------------------------------------

    def _toggle_empresa_local(self) -> None:
        """Activa o desactiva la empresa local."""
        if not hasattr(self, '_empresa_activo'):
            return
        nuevo_estado = not self._empresa_activo
        accion = "activar" if nuevo_estado else "desactivar"

        respuesta = QMessageBox.question(
            self,
            f"{accion.title()} empresa",
            f"¿Desea {accion} la empresa local?\n\n"
            f"Si la desactiva, el login sera bloqueado para todos "
            f"los usuarios.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if respuesta != QMessageBox.Yes:
            return

        resultado = self.controller.cambiar_estado_empresa_local(nuevo_estado)
        if resultado.get('ok'):
            QMessageBox.information(
                self, "Exito",
                f"Empresa {accion}da correctamente.")
            self.recargar()
        else:
            QMessageBox.warning(
                self, "Error",
                f"No se pudo {accion} la empresa: "
                f"{resultado.get('error', 'Error desconocido')}")

    # ----------------------------------------------------------------
    # Empresas Supabase
    # ----------------------------------------------------------------

    def _on_empresa_clic(self, fila: int, _columna: int) -> None:
        """Muestra info de la empresa seleccionada de Supabase."""
        if not hasattr(self, '_empresas_sb') or fila >= len(self._empresas_sb):
            return
        emp = self._empresas_sb[fila]
        nombre = emp.get('nombre', '')
        activo = emp.get('activo', True)
        eid = emp.get('id', '')

        respuesta = QMessageBox.question(
            self,
            "Cambiar estado de empresa",
            f"Empresa: {nombre}\nEstado actual: "
            f"{'Activa' if activo else 'Inactiva'}\n\n"
            f"¿Desea {'desactivar' if activo else 'activar'} esta empresa "
            f"en Supabase?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if respuesta != QMessageBox.Yes:
            return

        resultado = self.controller.cambiar_estado_empresa(
            eid, not activo)
        if resultado.get('ok'):
            QMessageBox.information(
                self, "Exito",
                f"Empresa '{nombre}' "
                f"{'activada' if not activo else 'desactivada'} "
                f"en Supabase.")
            self.recargar()
        else:
            QMessageBox.warning(
                self, "Error",
                f"No se pudo cambiar estado: "
                f"{resultado.get('error', 'Error desconocido')}")

    # ----------------------------------------------------------------
    # Usuarios locales
    # ----------------------------------------------------------------

    def _toggle_usuario(self, usuario_id: int, activo_actual: bool,
                        username: str) -> None:
        """Activa o desactiva un usuario."""
        nuevo_estado = not activo_actual
        accion = "activar" if nuevo_estado else "desactivar"

        respuesta = QMessageBox.question(
            self,
            f"{accion.title()} usuario",
            f"¿Desea {accion} el usuario '{username}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if respuesta != QMessageBox.Yes:
            return

        resultado = self.controller.cambiar_estado_usuario(
            usuario_id, nuevo_estado)

        if resultado.get('ok'):
            QMessageBox.information(
                self, "Exito",
                f"Usuario '{username}' {accion}do correctamente.")
            self.recargar()
        else:
            QMessageBox.warning(
                self, "Error",
                f"No se pudo {accion} el usuario: "
                f"{resultado.get('error', 'Error desconocido')}")

    def _cargar_tabla_usuarios(self, usuarios: list[dict]) -> None:
        """Carga la tabla de usuarios."""
        self.tabla_usuarios.setRowCount(0)
        for u in usuarios:
            activo = u.get('activo', 1) in (1, True)
            estado = "Activo" if activo else "Inactivo"
            uid = u.get('id', 0)
            username = u.get('username', '')
            r = self.tabla_usuarios.rowCount()
            self.tabla_usuarios.insertRow(r)
            self.tabla_usuarios.setItem(r, 0, QTableWidgetItem(str(uid)))
            self.tabla_usuarios.setItem(r, 1, QTableWidgetItem(username))
            self.tabla_usuarios.setItem(
                r, 2, QTableWidgetItem(u.get('nombre_completo', '')))
            self.tabla_usuarios.setItem(r, 3, QTableWidgetItem(u.get('rol', '')))
            self.tabla_usuarios.setItem(r, 4, QTableWidgetItem(estado))

            btn = QPushButton("Desactivar" if activo else "Activar")
            btn.setObjectName("btnSecondary")
            btn.setFixedHeight(28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(
                lambda checked=False, _id=uid, _a=activo, _u=username:
                self._toggle_usuario(_id, _a, _u))
            self.tabla_usuarios.setCellWidget(r, 5, btn)

    # ----------------------------------------------------------------
    # Recargar todo
    # ----------------------------------------------------------------

    def recargar(self) -> None:
        """Recarga todos los datos (local + Supabase)."""
        self.lbl_fecha.setText(
            datetime.now().strftime("Actualizado: %d/%m/%Y %H:%M"))

        try:
            # Info de empresa local
            empresa = self.controller.obtener_empresa()
            nombre_emp = empresa.get('nombre_empresa', '') or 'Sin configurar'
            self.lbl_empresa_nombre.setText(nombre_emp)
            info_parts = []
            if empresa.get('rfc'):
                info_parts.append(f"RFC: {empresa['rfc']}")
            if empresa.get('domicilio'):
                info_parts.append(f"Domicilio: {empresa['domicilio']}")
            if empresa.get('telefono'):
                info_parts.append(f"Tel: {empresa['telefono']}")
            if empresa.get('email'):
                info_parts.append(f"Email: {empresa['email']}")
            self.lbl_empresa_info.setText(
                " | ".join(info_parts) if info_parts
                else "Configure la empresa en Ajustes")

            # Estado de la empresa
            self._empresa_activo = empresa.get('activo', True)
            if self._empresa_activo:
                self.lbl_empresa_estado.setText("🟢 Empresa ACTIVA")
                self.lbl_empresa_estado.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: #16A34A;")
                self.btn_empresa_toggle.setText("Desactivar")
            else:
                self.lbl_empresa_estado.setText("🔴 Empresa INACTIVA")
                self.lbl_empresa_estado.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: #DC2626;")
                self.btn_empresa_toggle.setText("Activar")

            # Estadisticas
            stats = self.controller.obtener_estadisticas_globales()
            self.card_usuarios.establecer(
                f"{stats['usuarios_activos']}/{stats['total_usuarios']}")
            self.card_insumos.establecer(str(stats['total_insumos']))
            self.card_ocs.establecer(str(stats['total_ocs']))
            self.card_ops.establecer(str(stats['total_ops']))
            self.card_modelos.establecer(str(stats['total_modelos']))

            # Supabase status
            sb_ok = stats.get('supabase_configurado', False)
            if sb_ok:
                self.lbl_supabase.setText(
                    f"✅ Supabase conectado | "
                    f"{stats['total_empresas']} empresa(s) | "
                    f"{stats['empresas_activas']} activa(s)")
            else:
                self.lbl_supabase.setText(
                    "⚠️ Supabase no configurado (solo datos locales)")

            # Empresas de Supabase
            empresas_sb = self.controller.listar_empresas_supabase()
            self._empresas_sb = empresas_sb
            if empresas_sb:
                self.grp_empresas_sb.setVisible(True)
                self.tabla_empresas.setRowCount(0)
                for emp in empresas_sb:
                    activo = emp.get('activo', True)
                    r = self.tabla_empresas.rowCount()
                    self.tabla_empresas.insertRow(r)
                    self.tabla_empresas.setItem(
                        r, 0, QTableWidgetItem(emp.get('nombre', '')))
                    self.tabla_empresas.setItem(
                        r, 1, QTableWidgetItem(emp.get('rfc') or '—'))
                    self.tabla_empresas.setItem(
                        r, 2, QTableWidgetItem(
                            "Activa" if activo else "Inactiva"))
                    self.tabla_empresas.setItem(
                        r, 3, QTableWidgetItem(emp.get('id', '')))
            else:
                self.grp_empresas_sb.setVisible(False)

            # Usuarios locales
            usuarios = self.controller.listar_usuarios()
            activos = sum(
                1 for u in usuarios
                if u.get('activo', 1) in (1, True))
            self.lbl_detalle.setText(
                f"{activos} activos de {len(usuarios)} total")
            self._cargar_tabla_usuarios(usuarios)

        except Exception as e:
            self.card_usuarios.establecer("Error")
            print(f"Error en dashboard super_admin: {e}")
