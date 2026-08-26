"""Controller del Dashboard del sistema.

Delega en `DashboardModel` todas las lecturas agregadas; no contiene SQL ni
lógica de presentación (A-01/A-03).
"""
from src.models.dashboard_model import DashboardModel


class DashboardController:
    def __init__(self) -> None:
        self.dashboard_model = DashboardModel()

    def obtener_resumen(self) -> dict:
        """Indicadores clave de todos los módulos."""
        return self.dashboard_model.obtener_resumen()

    def obtener_ultimas_oc(self, limite: int = 8) -> list[dict]:
        return self.dashboard_model.obtener_ultimas_oc(limite)

    def obtener_ops_en_curso(self, limite: int = 8) -> list[dict]:
        return self.dashboard_model.obtener_ops_en_curso(limite)

    def obtener_stock_bajo(self, limite: int = 10) -> list[dict]:
        return self.dashboard_model.obtener_stock_bajo(limite)

    def obtener_movimientos_recientes(self, limite: int = 10) -> list[dict]:
        return self.dashboard_model.obtener_movimientos_recientes(limite)

    def obtener_compras_por_mes(self, meses: int = 6) -> list[dict]:
        return self.dashboard_model.obtener_compras_por_mes(meses)
