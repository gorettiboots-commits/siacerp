"""Diálogo para programar un pedido de cliente.

Permite elegir la semana (actual y restantes del año), decidir por modelo los
pares que se envían a programación (corrida por punto, con el restante como
máximo) y genera uno o más folios de programación con estatus
'programación incompleta' o 'programado' según el avance del pedido.
"""
from datetime import date, datetime, timedelta

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QHeaderView, QLabel,
    QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from src.views.dialogs import DialogMatrizTallas


class ProgramarPedidoDialog(QDialog):
    def __init__(self, clientes_controller, programacion_controller,
                 pedido_id: int, parent=None) -> None:
        super().__init__(parent)
        self.clientes = clientes_controller
        self.prog = programacion_controller
        self.pedido_id = pedido_id
        self.folios_generados: list[str] = []
        self.pedido = self.clientes.obtener_pedido(pedido_id) or {}
        self.detalle = self.clientes.obtener_detalle_pedido(pedido_id)
        self.puntos = self.clientes.listar_puntos()
        self.punto_str = {p["id"]: p["punto"] for p in self.puntos}
        self._corridas: dict[int, dict] = {}
        self._restante: dict[int, int] = {}
        self.setWindowTitle(f"Programar Pedido — {self.pedido.get('folio', '')}")
        self.setMinimumWidth(920)
        self._setup_ui()
        self._cargar()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        form = QFormLayout()
        form.setSpacing(8)
        self.lbl_cliente = QLabel()
        self.lbl_total = QLabel()
        self.lbl_programado = QLabel()
        self.lbl_restante = QLabel()
        for etiqueta, lbl in (
            ("Cliente:", self.lbl_cliente),
            ("Pares del pedido:", self.lbl_total),
            ("Pares programados:", self.lbl_programado),
            ("Pares restantes:", self.lbl_restante),
        ):
            lbl.setStyleSheet("font-weight: bold;")
            form.addRow(f"<b>{etiqueta}</b>", lbl)

        semana_row = QHBoxLayout()
        semana_row.addWidget(QLabel("<b>Semana:</b>"))
        self.cmb_semana = QComboBox()
        self.cmb_semana.setMinimumWidth(260)
        self.cmb_semana.currentIndexChanged.connect(self._actualizar_folios)
        semana_row.addWidget(self.cmb_semana)
        semana_row.addStretch()
        form.addRow("", semana_row)

        self.lbl_folios = QLabel("")
        self.lbl_folios.setStyleSheet("color: #4f46e5; font-weight: bold;")
        form.addRow("Folios Prog.:", self.lbl_folios)
        layout.addLayout(form)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["Modelo", "Piel", "Color", "Total", "Programado", "Restante",
             "Corrida a programar"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeToContents)
        self.table.verticalHeader().setDefaultSectionSize(42)
        layout.addWidget(self.table)

        self.lbl_total_programar = QLabel("Total a programar: 0 pares")
        self.lbl_total_programar.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #4f46e5;")
        layout.addWidget(self.lbl_total_programar)

        btns = QHBoxLayout()
        btns.addStretch()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setObjectName("btnSecondary")
        btn_cancel.clicked.connect(self.reject)
        self.btn_programar = QPushButton("Programar")
        self.btn_programar.setObjectName("btnPrimary")
        self.btn_programar.clicked.connect(self._programar)
        btns.addWidget(btn_cancel)
        btns.addWidget(self.btn_programar)
        layout.addLayout(btns)

    def _cargar(self) -> None:
        total = int(self.pedido.get("total_pares", 0) or 0)
        programado = self.prog.pares_programados_pedido(self.pedido_id)
        restante = max(0, total - programado)
        self.lbl_cliente.setText(self.pedido.get("cliente_nombre", ""))
        self.lbl_total.setText(str(total))
        self.lbl_programado.setText(str(programado))
        self.lbl_restante.setText(str(restante))

        hoy = date.today()
        for s in self.prog.listar_semanas_programar():
            label = s["nombre"]
            try:
                ini = datetime.strptime(s["fecha_inicio"], "%Y-%m-%d").date()
                if ini <= hoy <= ini + timedelta(days=6):
                    label = f"Semana actual — {label}"
            except (TypeError, ValueError):
                pass
            self.cmb_semana.addItem(label, s["id"])
        if self.cmb_semana.count() == 0:
            self.cmb_semana.addItem("Sin semanas disponibles", None)

        self.table.setRowCount(len(self.detalle))
        for i, d in enumerate(self.detalle):
            det_total = sum(int(p.get("pares", 0) or 0)
                            for p in d.get("puntos", []))
            prog_det = self.prog.pares_programados_detalle(d["id"])
            rest_det = max(0, det_total - prog_det)
            self._restante[d["id"]] = rest_det
            self.table.setItem(i, 0, QTableWidgetItem(d.get("modelo", "")))
            self.table.setItem(i, 1, QTableWidgetItem(d.get("piel", "") or ""))
            self.table.setItem(i, 2, QTableWidgetItem(d.get("color", "") or ""))
            self.table.setItem(i, 3, QTableWidgetItem(str(det_total)))
            self.table.setItem(i, 4, QTableWidgetItem(str(prog_det)))
            self.table.setItem(i, 5, QTableWidgetItem(str(rest_det)))
            btn = QPushButton("Programar corrida...")
            btn.setObjectName("btnSecondary")
            btn.setEnabled(rest_det > 0)
            btn.clicked.connect(lambda _=False, r=i, did=d["id"]:
                                self._configurar_corrida(r, did))
            self.table.setCellWidget(i, 6, btn)

        if restante <= 0:
            self.btn_programar.setEnabled(False)
            self.lbl_total_programar.setText(
                "Este pedido ya está completamente programado.")
        self._actualizar_folios()

    def _configurar_corrida(self, row: int, detalle_id: int) -> None:
        d = next((x for x in self.detalle if x["id"] == detalle_id), None)
        if not d:
            return
        programado_por_talla = self.prog.pares_programados_por_talla(detalle_id)
        inicial: dict[int, int] = {}
        for p in d.get("puntos", []):
            talla = p.get("punto", "")
            prog = int(programado_por_talla.get(talla, 0) or 0)
            rest = max(0, int(p.get("pares", 0) or 0) - prog)
            inicial[p["punto_id"]] = rest
        dlg = DialogMatrizTallas(self.clientes, inicial=inicial)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        matriz = dlg.get_matriz()
        tallas = [{"talla": self.punto_str[pid], "pares": n}
                  for pid, n in matriz.items()
                  if n > 0 and pid in self.punto_str]
        total_corrida = sum(t["pares"] for t in tallas)
        restante = self._restante.get(detalle_id, 0)
        if total_corrida > restante:
            QMessageBox.warning(
                self, "Excede el restante",
                f"La corrida ({total_corrida} pares) excede el restante del "
                f"modelo ({restante} pares).")
            return
        self._corridas[detalle_id] = {
            "detalle_id": detalle_id,
            "modelo": d.get("modelo", ""),
            "piel": d.get("piel", "") or "",
            "color": d.get("color", "") or "",
            "tallas": tallas,
        }
        btn = self.table.cellWidget(row, 6)
        if btn:
            btn.setText(f"Editar corrida ({total_corrida} pr)")
        self._actualizar_folios()

    def _actualizar_folios(self) -> None:
        n = sum(1 for c in self._corridas.values() if c["tallas"])
        total = sum(t["pares"] for c in self._corridas.values()
                    for t in c["tallas"])
        self.lbl_total_programar.setText(f"Total a programar: {total} pares")
        if n:
            base = int(self.prog.siguiente_folio_prog())
            folios = ", ".join(str(base + i) for i in range(n))
            self.lbl_folios.setText(f"{folios}  ({n} folio(s))")
        else:
            self.lbl_folios.setText("—")

    def _programar(self) -> None:
        semana_id = self.cmb_semana.currentData()
        if not semana_id:
            QMessageBox.warning(self, "Semana", "Seleccione la semana.")
            return
        corridas = [c for c in self._corridas.values() if c["tallas"]]
        if not corridas:
            QMessageBox.warning(
                self, "Sin corridas",
                "Configure al menos una corrida de pares por modelo.")
            return
        semana = self.prog.obtener_semana(semana_id) or {}
        fecha_prog = semana.get("fecha_inicio", "")
        folios = self.prog.programar_pedido(
            pedido_id=self.pedido_id,
            folio_pedido=self.pedido.get("folio", ""),
            cliente=self.pedido.get("cliente_nombre", ""),
            total_pedido=int(self.pedido.get("total_pares", 0) or 0),
            semana_id=semana_id,
            fecha_prog=fecha_prog,
            corridas=corridas,
        )
        if not folios:
            return
        self.folios_generados = folios
        self.accept()
