"""Pruebas del util de impresora virtual SIAC (simulación en pantalla).

Cubre:
    - Guardado y lectura de la preferencia en `configuracion_sistema`.
    - Comportamiento del diálogo con la preferencia DESACTIVADA: delega en
      QPrintDialog nativo (sin el diálogo propio), por lo que no depende de
      impresoras instaladas ni abre ventanas en CI.
    - El diálogo propio con la virtual activa se construye correctamente con
      la opción "Impresora virtual SIAC (simulación)".

Se ejecutan headless (QT_QPA_PLATFORM=offscreen, ver conftest.py).
"""

import sqlite3

import pytest

import src.utils.impresion_virtual as mod
from src.utils.impresion_virtual import (
    CLAVE_IMPRESION_VIRTUAL,
    NOMBRE_VIRTUAL,
    _DialogoImpresion,
    guardar_impresora_virtual,
    impresora_virtual_habilitada,
)

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class _BDTemporal:
    """Mini DatabaseManager sobre una BD sqlite temporal (mismos métodos)."""

    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute(
            "CREATE TABLE configuracion_sistema ("
            "clave TEXT PRIMARY KEY, valor TEXT NOT NULL DEFAULT '', "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')))")

    def execute(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        self.conn.commit()
        return c

    def fetch_one(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        row = c.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: tuple = ()):
        c = self.conn.cursor()
        c.execute(query, params)
        return [dict(r) for r in c.fetchall()]


@pytest.fixture
def bd(monkeypatch, tmp_path):
    """Apunta el util a una BD temporal para no tocar la BD del proyecto."""
    bd_tmp = _BDTemporal(str(tmp_path / "impresion_test.db"))
    monkeypatch.setattr(mod, "DatabaseManager", lambda: bd_tmp)
    return bd_tmp


# ------------------------------------------------------- Preferencia
class TestPreferencia:
    def test_por_defecto_impresora_virtual_deshabilitada(self, bd):
        assert impresora_virtual_habilitada() is False

    def test_guardar_activa_y_vuelve_a_leer(self, bd):
        guardar_impresora_virtual(True)
        assert impresora_virtual_habilitada() is True
        fila = bd.fetch_one(
            "SELECT valor FROM configuracion_sistema WHERE clave = ?",
            (CLAVE_IMPRESION_VIRTUAL,))
        assert fila["valor"] == "1"

    def test_guardar_desactiva_sobreescribe(self, bd):
        guardar_impresora_virtual(True)
        guardar_impresora_virtual(False)
        assert impresora_virtual_habilitada() is False
        fila = bd.fetch_one(
            "SELECT valor FROM configuracion_sistema WHERE clave = ?",
            (CLAVE_IMPRESION_VIRTUAL,))
        assert fila["valor"] == "0"


# --------------------------------------------------------- Diálogo propio
class TestDialogoVirtual:
    def test_dialogo_ofrece_opcion_virtual(self, qapp, bd):
        from PySide6.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        dlg = _DialogoImpresion(printer)
        opciones = [dlg.cmb_printer.itemText(i)
                    for i in range(dlg.cmb_printer.count())]
        assert NOMBRE_VIRTUAL in opciones
        dlg.close()
        dlg.deleteLater()


# --------------------------------------------------- diálogo_impresion()
class TestDialogoImpresion:
    def test_con_preferencia_desactivada_usa_qprintdialog(self, qapp, bd,
                                                          monkeypatch):
        """Delega en QPrintDialog nativo (sin diálogo propio) y respeta la
        cancelación sin abrir ventanas de impresión real."""
        ejecutados = []

        class _StubQPrintDialog:
            def __init__(self, printer, parent=None):
                self._padre = parent

            def exec(self):
                return 0  # QDialog.Rejected

        monkeypatch.setattr(mod, "QPrintDialog", _StubQPrintDialog)
        from PySide6.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        estado = mod.dialogo_impresion(printer, None,
                                       lambda p: ejecutados.append(True))
        assert estado == "cancelado"
        assert ejecutados == []

    def test_con_preferencia_desactivada_ejecuta_pintar(self, qapp, bd,
                                                        monkeypatch):
        ejecutados = []

        class _StubQPrintDialog:
            def __init__(self, printer, parent=None):
                self._padre = parent

            def exec(self):
                return 1  # QDialog.Accepted

        monkeypatch.setattr(mod, "QPrintDialog", _StubQPrintDialog)
        from PySide6.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        estado = mod.dialogo_impresion(printer, None,
                                       lambda p: ejecutados.append(True))
        assert estado == "impreso"
        assert ejecutados == [True]

    def test_con_virtual_activa_cancelado_no_pinta(self, qapp, bd,
                                                   monkeypatch):
        guardar_impresora_virtual(True)
        ejecutados = []

        class _StubDialogo:
            def __init__(self, printer, parent=None):
                pass

            def exec(self):
                return 0  # Rejected

        monkeypatch.setattr(mod, "_DialogoImpresion", _StubDialogo)
        from PySide6.QtPrintSupport import QPrinter
        printer = QPrinter(QPrinter.HighResolution)
        estado = mod.dialogo_impresion(printer, None,
                                       lambda p: ejecutados.append(True))
        assert estado == "cancelado"
        assert ejecutados == []