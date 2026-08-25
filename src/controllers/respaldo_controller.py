"""Controlador de respaldos: exportación e importación de conjuntos de datos.

Delega en `src.utils.respaldo_bd_utils` (helpers puros + DatabaseManager) y
expone la API que consume la sección "Base de Datos" de Configuración.
"""
from __future__ import annotations

from src.utils.respaldo_bd_utils import (
    importar_conjuntos, inspeccionar_archivo, listar_conjuntos,
    exportar_conjuntos,
)


class RespaldoController:
    """Operaciones de respaldo parcial de la base de datos."""

    def listar_conjuntos(self) -> list[dict]:
        """Conjuntos disponibles con su cantidad de filas actual."""
        return listar_conjuntos()

    def exportar(self, claves: list[str], ruta: str) -> dict:
        """Exporta los conjuntos indicados a un archivo JSON."""
        return exportar_conjuntos(claves, ruta)

    def inspeccionar(self, ruta: str) -> dict:
        """Describe el contenido de un archivo de respaldo sin importarlo."""
        return inspeccionar_archivo(ruta)

    def importar(self, ruta: str, claves: list[str],
                 reemplazar: bool) -> dict:
        """Importa los conjuntos indicados (reemplazando o agregando)."""
        return importar_conjuntos(ruta, claves, reemplazar)
