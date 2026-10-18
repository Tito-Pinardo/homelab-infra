"""Cliente minimo (requests puro) para las busquedas semanticas del bot."""
import os

import requests

EMBED_URL = os.environ["EMBED_URL"]
EMBED_MODEL = os.environ["EMBED_MODEL"]
QDRANT_URL = os.environ["QDRANT_URL"]
QDRANT_API_KEY = os.environ["QDRANT_API_KEY"]
VECTOR_SIZE = 768

_known_collections: set[str] = set()


def _headers() -> dict:
    ...


def _embed(text: str) -> list[float]:
    ...


def ensure_collection(collection: str):
    ...


def search(collection: str, query: str, limit: int = 5, filter_: dict | None = None) -> list[dict]:
    ...


def scroll(collection: str, filter_: dict, limit: int = 50) -> list[dict]:
    """Lista puntos por FILTRO de payload (sin busqueda semantica) - lo usa
    el vigilante de notificaciones proactivas de ia_bot.py para encontrar
    correos nuevos por timestamp, no por significado."""
    ...


def index(collection: str, point_id: str, text: str, payload: dict):
    ...
