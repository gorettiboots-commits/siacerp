"""Impresora virtual SIAC: simulación de impresión en pantalla.

Cuando la preferencia 'impresion_virtual' está habilitada (sección Impresión
de Configuración), los flujos de impresión del sistema ofrecen, además de las
impresoras reales, la opción "Impresora virtual SIAC (simulación)". Al
elegirla, el trabajo NO se envía a la impresora física: se abre una vista
previa en pantalla (QPrintPreviewDialog) que reproduce exactamente la salida
que se habría impreso.

Uso:
    printer = QPrinter(QPrinter.HighResolution)
    ... configurar página ...
    estado = dialogo_impresion(printer, self, lambda p: _renderizar(p))
    # estado: 'impreso' | 'simulado' | 'cancelado'
"""
from collections.abc import Callable

from PySide6.QtPrintSupport import QPrintDialog, QPrintPreviewDialog, QPrinter, QPrinterInfo
from PySide6.QtWidgets import QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QVBoxLayout

from src.database.db_manager import DatabaseManager

CLAVE_IMPRESION_VIRTUAL = "impresion_virtual"
NOMBRE_VIRTUAL = "Impresora virtual SIAC (simulación)"


def impresora_virtual_habilitada() -> bool:
    """Devuelve True si la impresora virtual está activada en Configuración."""
    db = DatabaseManager()
    row = db.fetch_one(
        "SELECT valor FROM configuracion_sistema WHERE clave = ?",
        (CLAVE_IMPRESION_VIRTUAL,),
    )
    return bool(row) and str(row["valor"]) == "1"


def guardar_impresora_virtual(habilitada: bool) -> None:
    """Guarda la preferencia de impresora virtual (1 = activa, 0 = inactiva)."""
    db = DatabaseManager()
    db.execute(
        "INSERT INTO configuracion_sistema (clave, valor) VALUES (?, ?) "
        "ON CONFLICT(clave) DO UPDATE SET valor = excluded.valor, "
        "updated_at = datetime('now')",
        (CLAVE_IMPRESION_VIRTUAL, "1" if habilitada else "0"),
    )


def _impresoras_disponibles() -> list[str]:
    return [p.printerName() for p in QPrinterInfo.availablePrinters()]


class _DialogoImpresion(QDialog):
    """Selección de impresora: las reales del sistema + la impresora virtual.

    Aparece SOLO cuando la impresora virtual está habilitada. Si el usuario
    elige la virtual, `es_virtual` será True.
    """

    def __init__(self, printer: QPrinter, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("dlgImpresionVirtual")
        self.setWindowTitle("Impresión")
        self.setModal(True)
        self.setMinimumWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("Seleccione la impresora de destino:"))

        form = QFormLayout()
        self.cmb_printer = QComboBox(self)
        opciones = _impresoras_disponibles() + [NOMBRE_VIRTUAL]
        self.cmb_printer.addItems(opciones)
        nombre_actual = printer.printerName()
        if not nombre_actual and opciones:
            # Preselecciona la virtual si no hay impresoras reales; en otro
            # caso deja la primera (la del sistema/no seleccionada es la
            # impresora por defecto en QPrinter).
            self.cmb_printer.setCurrentIndex(0)
        elif nombre_actual and nombre_actual in opciones:
            self.cmb_printer.setCurrentText(nombre_actual)
        form.addRow("Impresora:", self.cmb_printer)
        layout.addLayout(form)

        hint = QLabel("La \"Impresora virtual SIAC\" muestra el resultado en "
                      "pantalla sin enviar el trabajo a una impresora física.")
        hint.setObjectName("cfgHint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        botones = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        botones.button(QDialogButtonBox.StandardButton.Ok).setText("Aceptar")
        botones.button(QDialogButtonBox.StandardButton.Cancel).setText("Cancelar")
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

    @property
    def es_virtual(self) -> bool:
        return self.cmb_printer.currentText() == NOMBRE_VIRTUAL

    @property
    def nombre_impresora(self) -> str:
        return self.cmb_printer.currentText()


def dialogo_impresion(printer: QPrinter, parent=None,
                      pintar: Callable[[QPrinter], None] | None = None) -> str:
    """Muestra el diálogo de impresión correspondiente.

    - Sin impresora virtual: QPrintDialog nativo; si se acepta, ejecuta
      `pintar(printer)` y devuelve 'impreso'.
    - Con impresora virtual activa: diálogo propio con las impresoras reales
      más la virtual. Si se elige una impresora real, la asigna, ejecuta
      `pintar(printer)` y devuelve 'impreso'. Si se elige la virtual, abre la
      simulación en pantalla (QPrintPreviewDialog) y devuelve 'simulado'.

    Devuelve 'impreso', 'simulado' o 'cancelado'.
    """
    if not impresora_virtual_habilitada():
        dlg = QPrintDialog(printer, parent)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return "cancelado"
        if pintar:
            pintar(printer)
        return "impreso"

    dlg = _DialogoImpresion(printer, parent)
    if dlg.exec() != QDialog.DialogCode.Accepted:
        return "cancelado"

    if dlg.es_virtual:
        if pintar:
            preview = QPrintPreviewDialog(printer, parent)
            preview.paintRequested.connect(lambda p: pintar(p))
            preview.exec()
        return "simulado"

    printer.setPrinterName(dlg.nombre_impresora)
    if pintar:
        pintar(printer)
    return "impreso"