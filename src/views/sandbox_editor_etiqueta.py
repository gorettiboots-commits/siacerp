"""Sandbox: demo del componente aprobado 'editor de etiquetas'.

Este archivo ya NO es el dueño del código: el editor aprobado vive en
``src/components/editor_etiqueta_widget.py`` (catálogo:
``editor_etiqueta`` / ``editor_etiqueta_dialog``) y aquí solo se expone
como demo dentro del Sandbox.
"""

from src.components.editor_etiqueta_widget import (
    DialogoEditorEtiqueta, EditorEtiquetaWidget,
)

# Alias de compatibilidad: el prototipo del sandbox ES el componente aprobado.
EditorEtiquetaPreview = EditorEtiquetaWidget

__all__ = ["EditorEtiquetaPreview", "DialogoEditorEtiqueta"]
