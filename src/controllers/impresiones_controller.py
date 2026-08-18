"""Controller de la cola de impresión de etiquetas.

Une la API de Supabase (cola) con el histórico local: lista las
solicitudes pendientes del móvil, las imprime, las marca como impresas
en Supabase y las conserva en el histórico local.
"""
from typing import Any

from src.models.impresiones_model import ImpresionesModel
from src.utils import supabase_api


class ImpresionesController:
    def __init__(self) -> None:
        self.modelo = ImpresionesModel()

    def configurado(self) -> bool:
        return supabase_api.configurado()

    def listar_cola(self) -> list[dict]:
        return supabase_api.listar_pendientes()

    def marcar_impresa(self, supabase_id: Any) -> None:
        supabase_api.marcar_impresa(supabase_id)

    def guardar_historico(self, supabase_id: Any, tipo: str, payload: dict,
                          solicitado_en: str, usuario: str | None) -> int:
        return self.modelo.guardar_historico(
            supabase_id, tipo, payload, solicitado_en, usuario)

    def listar_historicos(self) -> list[dict]:
        return self.modelo.listar_historicos()

    def obtener_historico(self, id_historico: int) -> dict | None:
        return self.modelo.obtener_historico(id_historico)

    def registrar_reimpresion(self, id_historico: int) -> None:
        self.modelo.registrar_reimpresion(id_historico)
