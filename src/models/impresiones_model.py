"""Modelo del histórico de etiquetas impresas (cola de impresión).

Las solicitudes que llegan de la app móvil se imprimen desde la cola; al
imprimirse salen de Supabase (estatus 'impresa') y se conservan localmente
en `impresiones_historico` para poder reimprimirse sin volver a consultar
Supabase.
"""
import json
from typing import Any

from src.database.db_manager import DatabaseManager


class ImpresionesModel:
    def __init__(self) -> None:
        self.db = DatabaseManager()

    def guardar_historico(self, supabase_id: Any, tipo: str, payload: dict,
                          solicitado_en: str, usuario: str | None) -> int:
        """Guarda una solicitud impresa en el histórico. Devuelve su id."""
        cursor = self.db.execute(
            "INSERT INTO impresiones_historico "
            "(supabase_id, tipo, payload, solicitado_en, usuario) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(supabase_id) if supabase_id is not None else None,
             tipo,
             json.dumps(payload, ensure_ascii=False),
             solicitado_en,
             usuario),
        )
        return int(cursor.lastrowid)

    def listar_historicos(self) -> list[dict]:
        filas = self.db.fetch_all(
            "SELECT * FROM impresiones_historico ORDER BY id DESC")
        for fila in filas:
            try:
                fila["payload"] = json.loads(fila["payload"] or "{}")
            except (ValueError, TypeError):
                fila["payload"] = {}
        return filas

    def obtener_historico(self, id_historico: int) -> dict | None:
        fila = self.db.fetch_one(
            "SELECT * FROM impresiones_historico WHERE id = ?", (id_historico,))
        if not fila:
            return None
        try:
            fila["payload"] = json.loads(fila["payload"] or "{}")
        except (ValueError, TypeError):
            fila["payload"] = {}
        return fila

    def registrar_reimpresion(self, id_historico: int) -> None:
        self.db.execute(
            "UPDATE impresiones_historico SET reimpresiones = reimpresiones + 1 "
            "WHERE id = ?",
            (id_historico,),
        )
