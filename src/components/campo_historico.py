"""Componente aprobado: campo de texto con histórico de capturas.

Un `QLineEdit` habilitado que ya tiene capturas registradas vuelve a
comportarse como captura Y como combo de búsqueda: el histórico se despliega
hasta que el usuario comienza a escribir y, mientras escribe, la lista se
filtra con los valores coincidentes. NO se despliega nada al recibir el foco
ni al hacer clic (navegar con Tab no abre popup ni roba interacciones). Al
salir del campo se registra la nueva captura.

Integración global sin tocar pantallas:
    from src.components.campo_historico import InstaladorHistorico
    InstaladorHistorico.instalar()

La clave del campo se deduce de forma automática (en este orden):
    1. La etiqueta (label) que acompaña al campo en su layout (QFormLayout o
       QGridLayout).
    2. El placeholder del campo (sin el texto entre paréntesis).
    3. El objectName del campo.
    4. La propiedad `_claveCampo` si fue asignada explícitamente (tiene prioridad).

Almacén: tabla `historico_campos` vía `src.models.historico_campos_model`.
"""

from __future__ import annotations

import re

from PySide6.QtCore import QEvent, QObject, QStringListModel, Qt
from PySide6.QtWidgets import (
    QApplication, QCompleter, QDialog, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QMainWindow, QWidget,
)
from shiboken6 import isValid

from src.models.historico_campos_model import HistoricoCamposModel

_MAX_HISTORICO = 50
_EXPRESION_TAGS = re.compile(r"<[^>]+>")


def _limpiar_label(texto: str) -> str:
    """Quita etiquetas HTML y dos puntos finales de una etiqueta de campo."""
    texto = _EXPRESION_TAGS.sub("", texto or "")
    return texto.strip().rstrip(":").strip()


def _clave_desde_layout(edit: QLineEdit) -> str | None:
    """Busca la etiqueta que identifica al campo en el layout del formulario."""
    padre = edit.parentWidget()
    if padre is None or padre.layout() is None:
        return None

    def recorrer(layout) -> str | None:
        if isinstance(layout, QFormLayout):
            label = layout.labelForField(edit)
            if label is not None:
                clave = _limpiar_label(label.text())
                if clave:
                    return clave
        elif isinstance(layout, QGridLayout):
            idx = layout.indexOf(edit)
            if idx >= 0:
                fila, columna, _, _ = layout.getItemPosition(idx)
                if columna > 0:
                    item = layout.itemAtPosition(fila, columna - 1)
                    if item is not None and isinstance(item.widget(), QLabel):
                        clave = _limpiar_label(
                            item.widget().text())  # type: ignore[union-attr]
                        if clave:
                            return clave
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item is not None and item.layout() is not None:
                clave = recorrer(item.layout())
                if clave:
                    return clave
        return None

    return recorrer(padre.layout())


def obtener_clave_campo(edit: QLineEdit) -> str | None:
    """Devuelve la clave que identifica al campo para su histórico, o None."""
    explicita = edit.property("_claveCampo")
    if isinstance(explicita, str) and explicita.strip():
        return explicita.strip()
    clave = _clave_desde_layout(edit)
    if clave:
        return clave
    placeholder = edit.placeholderText().strip()
    if placeholder:
        return placeholder.split("(")[0].strip()
    object_name = edit.objectName().strip()
    if object_name:
        return object_name
    return None


class _ControlHistorico(QObject):
    """Mecanismo de histórico acoplado a un `QLineEdit` (vida igual al campo)."""

    def __init__(self, edit: QLineEdit, modelo: HistoricoCamposModel,
                 clave: str) -> None:
        super().__init__(edit)
        self._edit = edit
        self._modelo = modelo
        self._clave = clave
        self._baseline = ""

        self._lista = QStringListModel(edit)
        self._completer = QCompleter(self._lista, edit)
        self._completer.setCompletionMode(QCompleter.PopupCompletion)
        self._completer.setFilterMode(Qt.MatchContains)
        self._completer.setCaseSensitivity(Qt.CaseInsensitive)
        self._completer.setMaxVisibleItems(8)
        edit.setCompleter(self._completer)

        popup = self._completer.popup()
        popup.setStyleSheet(
            "QListView { background-color: #FFFFFF; color: #000000;"
            " border: 1px solid #7A7A7A; outline: none; }"
            "QListView::item { padding: 4px 8px; }"
            "QListView::item:hover { background-color: #EAF3FF; }"
            "QListView::item:selected { background-color: #3399FF;"
            " color: #FFFFFF; }")

        edit.installEventFilter(self)
        edit.editingFinished.connect(self._registrar)
        self._actualizar()

    def _actualizar(self) -> None:
        valores = [fila["valor"] for fila in
                   self._modelo.listar_por_campo(self._clave, _MAX_HISTORICO)]
        self._lista.setStringList(valores)

    def _registrar(self) -> None:
        valor = self._edit.text().strip()
        if not valor or valor == self._baseline:
            return
        self._baseline = valor
        self._modelo.registrar(self._clave, valor)
        self._actualizar()

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if not isValid(self._edit):
            return False
        if (self._edit.isEnabled() and not self._edit.isReadOnly()
                and event.type() == QEvent.FocusIn):
            # Solo guarda el valor inicial: el histórico se despliega hasta
            # que el usuario comienza a escribir (nada al enfocar ni al clic).
            self._baseline = self._edit.text().strip()
        return False


def habilitar_campo(edit: QLineEdit,
                    modelo: HistoricoCamposModel | None = None) -> str | None:
    """Activa el histórico en un `QLineEdit` habilitado.

    Regresa la clave de campo aplicada o None si el campo no aplica
    (deshabilitado, de solo lectura, de contraseña o sin clave identificable).
    """
    if not isinstance(edit, QLineEdit):
        return None
    if not edit.isEnabled() or edit.isReadOnly():
        return None
    if edit.echoMode() != QLineEdit.Normal:
        return None
    ya = edit.property("_campoHistoricoAplicado")
    if isinstance(ya, str) and ya:
        return ya
    clave = obtener_clave_campo(edit)
    if not clave:
        return None
    if modelo is None:
        modelo = HistoricoCamposModel()
    _ControlHistorico(edit, modelo, clave)
    edit.setProperty("_campoHistoricoAplicado", clave)
    return clave


def aplicar_historico(widget: QWidget,
                      modelo: HistoricoCamposModel | None = None) -> int:
    """Aplica el histórico a todos los campos de texto habilitados de un widget.

    Regresa la cantidad de campos activados.
    """
    aplicados = 0
    for edit in widget.findChildren(QLineEdit):
        if habilitar_campo(edit, modelo) is not None:
            aplicados += 1
    return aplicados


class InstaladorHistorico(QObject):
    """Aplica el histórico de forma global y automática.

    Instala un filtro de eventos en la aplicación: cuando se muestra la ventana
    principal o un diálogo, recorre sus campos una sola vez.
    """

    _instancia: 'InstaladorHistorico | None' = None

    def __init__(self) -> None:
        super().__init__(QApplication.instance())
        app = QApplication.instance()
        if app is not None:
            app.installEventFilter(self)
        self._procesados: set[int] = set()

    @classmethod
    def instalar(cls) -> 'InstaladorHistorico':
        if cls._instancia is None:
            cls._instancia = cls()
        return cls._instancia

    def eventFilter(self, obj, event) -> bool:  # type: ignore[override]
        if (event.type() == QEvent.Show
                and isinstance(obj, (QMainWindow, QDialog))
                and id(obj) not in self._procesados):
            self._procesados.add(id(obj))
            aplicar_historico(obj)
        return False


class CampoHistorico(QLineEdit):
    """QLineEdit con histórico activado desde su creación.

    Acepta una clave opcional (`clave`) para fijar explícitamente el histórico
    que comparte (si no se pasa, la clave se deduce automáticamente).
    """

    def __init__(self, clave: str | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if clave:
            self.setProperty("_claveCampo", clave)
        habilitar_campo(self)