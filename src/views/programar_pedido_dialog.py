"""Diálogo para programar un pedido de cliente.

Permite elegir la semana (actual y restantes del año), decidir por modelo los
pares que se envían a programación (corrida por punto, con el restante como
máximo) y genera uno o más folios de programación con estatus
'programación incompleta' o 'programado' según el avance del pedido.
"""
from datetime import date, datetime, timedelta

from PySide6.QtWidgets import (
    QComboBox, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout,
)

from src.components.grid_hibrido import GridHibrido
from src.components.tallas_matrix import MatrizTallasDialog


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
        self._corridas: dict[int, dict] = {}
        self._restante: dict[int, int] = {}
        self._detalle_recs: list[dict] = []
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
        self.lbl_folios.setStyleSheet("color: #1F4E79; font-weight: bold;")
        form.addRow("Folios Prog.:", self.lbl_folios)
        self.lbl_folio_pedido = QLabel("")
        form.addRow("Folio Pedido:", self.lbl_folio_pedido)
        layout.addLayout(form)

        self.vista = GridHibrido()
        self.vista.set_buscador_visible(False)
        self.vista.set_agrupar_visible(False)
        self.vista.set_columnas([
            {"key": "modelo", "titulo": "Modelo", "ancho": 200},
            {"key": "corrida", "titulo": "Corrida", "ancho": 150},
            {"key": "piel", "titulo": "Piel", "ancho": 150},
            {"key": "color", "titulo": "Color", "ancho": 150},
            {"key": "det_total", "titulo": "Total", "ancho": 70, "tipo": "numero"},
            {"key": "prog_det", "titulo": "Programado", "ancho": 90, "tipo": "numero"},
            {"key": "rest_det", "titulo": "Restante", "ancho": 80, "tipo": "numero"},
        ])
        self.vista.set_renderers(fila=self._fila, claves=self._claves)
        self.vista.set_acciones([
            {"texto": self._texto_corrida, "icono": "editar",
             "color": "#1F4E79", "ancho_columna": 44,
             "habilitado": self._habilitado_corrida,
             "callback": self._configurar_corrida},
        ])
        layout.addWidget(self.vista)

        self.lbl_total_programar = QLabel("Total a programar: 0 pares")
        self.lbl_total_programar.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #1F4E79;")
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
        self.lbl_folio_pedido.setText(
            self.pedido.get("folio_pedido", "") or self.pedido.get("folio", "") or "—")

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

        self._detalle_recs = []
        for d in self.detalle:
            det_total = sum(int(p.get("pares", 0) or 0)
                            for p in d.get("puntos", []))
            prog_det = self.prog.pares_programados_detalle(d["id"])
            rest_det = max(0, det_total - prog_det)
            self._restante[d["id"]] = rest_det
            self._detalle_recs.append({
                "detalle_id": d["id"],
                "modelo": d.get("modelo", ""),
                "piel": d.get("piel", "") or "",
                "color": d.get("color", "") or "",
                "det_total": det_total,
                "prog_det": prog_det,
                "rest_det": rest_det,
                "corrida_cap": self._rango_corrida_capturada(
                    d.get("puntos", [])),
                "corrida_min": self._minimo_corrida_capturada(
                    d.get("puntos", [])),
            })
        self.vista.set_datos(self._detalle_recs)

        if restante <= 0:
            self.btn_programar.setEnabled(False)
            self.lbl_total_programar.setText(
                "Este pedido ya está completamente programado.")
        self._actualizar_folios()

    @staticmethod
    def _fmt_talla(talla) -> str:
        try:
            v = float(talla)
            return str(int(v)) if v == int(v) else str(v)
        except (TypeError, ValueError):
            return str(talla)

    @staticmethod
    def _valor_talla(talla: str):
        try:
            return (0, float(talla))
        except (TypeError, ValueError):
            return (1, str(talla))

    def _minimo_corrida_capturada(self, puntos: list) -> tuple:
        parejas = sorted(
            (self._valor_talla(p.get("punto", "")), p.get("punto", ""))
            for p in puntos if int(p.get("pares", 0) or 0) > 0)
        return parejas[0][0] if parejas else (1, "")

    def _rango_corrida_capturada(self, puntos: list) -> str:
        parejas = sorted(
            (self._valor_talla(p.get("punto", "")), p.get("punto", ""))
            for p in puntos if int(p.get("pares", 0) or 0) > 0)
        if not parejas:
            return ""
        return (f"del {self._fmt_talla(parejas[0][1])} "
                f"al {self._fmt_talla(parejas[-1][1])}")

    def _texto_corrida_rango(self, d: dict) -> str:
        corrida = self._corridas.get(d["detalle_id"])
        if corrida and corrida["tallas"]:
            parejas = sorted(
                (self._valor_talla(t["talla"]), t["talla"]) for t in corrida["tallas"])
            return (f"del {self._fmt_talla(parejas[0][1])} "
                    f"al {self._fmt_talla(parejas[-1][1])}")
        return d.get("corrida_cap", "")

    def _fila(self, d: dict) -> list[str]:
        return [d.get("modelo", ""), self._texto_corrida_rango(d),
                d.get("piel", ""), d.get("color", ""),
                str(d.get("det_total", 0)), str(d.get("prog_det", 0)),
                str(d.get("rest_det", 0))]

    def _claves(self, d: dict) -> list:
        corrida = self._corridas.get(d["detalle_id"])
        if corrida and corrida["tallas"]:
            mins = min(self._valor_talla(t["talla"]) for t in corrida["tallas"])
        else:
            mins = d.get("corrida_min", (1, ""))
        return [d.get("modelo", "").lower(), mins,
                d.get("piel", "").lower(), d.get("color", "").lower(),
                float(d.get("det_total", 0)), float(d.get("prog_det", 0)),
                float(d.get("rest_det", 0))]

    def _texto_corrida(self, d: dict) -> str:
        corrida = self._corridas.get(d["detalle_id"])
        if corrida and corrida["tallas"]:
            n = sum(t["pares"] for t in corrida["tallas"])
            return f"Editar corrida ({n} pr)"
        return "Programar corrida..."

    @staticmethod
    def _habilitado_corrida(d: dict) -> bool:
        return d.get("rest_det", 0) > 0

    def _configurar_corrida(self, d: dict) -> None:
        detalle_id = d["detalle_id"]
        det = next((x for x in self.detalle if x["id"] == detalle_id), None)
        if not det:
            return
        programado_por_talla = self.prog.pares_programados_por_talla(detalle_id)
        inicial: dict[str, int] = {}
        for p in det.get("puntos", []):
            talla = p.get("punto", "")
            prog = int(programado_por_talla.get(talla, 0) or 0)
            rest = max(0, int(p.get("pares", 0) or 0) - prog)
            inicial[talla] = rest
        puntos = [{"id": p["punto_id"], "punto": p.get("punto", "")}
                  for p in det.get("puntos", [])]
        dlg = MatrizTallasDialog(puntos=puntos, titulo="CORRIDA A PROGRAMAR",
                                 parent=self)
        dlg.establecer_valores(inicial)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return
        matriz = dlg.obtener_valores()
        tallas = [{"talla": talla, "pares": n}
                  for talla, n in matriz.items() if n > 0]
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
            "modelo": det.get("modelo", ""),
            "piel": det.get("piel", "") or "",
            "color": det.get("color", "") or "",
            "tallas": tallas,
        }
        self.vista.set_datos(self._detalle_recs)
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
            folio_pedido=(self.pedido.get("folio_pedido", "")
                          or self.pedido.get("folio", "")),
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
