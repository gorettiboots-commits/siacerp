"""Componente aprobado: selector de fecha con calendario emergente.

API pública
-----------
- ``DatePicker`` (QDateEdit): selector de fecha con popup de calendario y
  formato de visualización `dd/MM/yyyy`.
    - ``fecha_bd() -> str``: fecha en formato ISO (`yyyy-MM-dd`) lista para
      guardar en la base de datos.
    - ``establecer_fecha_bd(valor: str)``: carga una fecha guardada en BD
      (ISO `yyyy-MM-dd`, con o sin hora) ignorando valores vacíos.

Reemplaza la captura manual de fechas en los módulos: el calendario
emergente evita errores de captura y el formato queda uniforme en todo el
sistema. Para usar el estilo del prototipo WinForms basta con asignar el
objectName ``ctlInput`` al crear la instancia.
"""

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit

FORMATO_ISO = "yyyy-MM-dd"
FORMATO_VISTA = "dd/MM/yyyy"


class DatePicker(QDateEdit):
    """Selector de fecha con calendario emergente (aprobado)."""

    def __init__(self, fecha: QDate | None = None,
                 parent=None) -> None:
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat(FORMATO_VISTA)
        self.setDate(fecha or QDate.currentDate())

    def fecha_bd(self) -> str:
        """Fecha en formato ISO (yyyy-MM-dd) para guardar en BD."""
        return self.date().toString(FORMATO_ISO)

    def establecer_fecha_bd(self, valor: str | None) -> None:
        """Carga una fecha de BD (ISO) sin modificar si viene vacía."""
        if not valor:
            return
        texto = str(valor).strip().split(" ")[0]
        for fmt in (FORMATO_ISO, "yyyy/MM/dd", FORMATO_VISTA):
            fecha = QDate.fromString(texto, fmt)
            if fecha.isValid():
                self.setDate(fecha)
                return
