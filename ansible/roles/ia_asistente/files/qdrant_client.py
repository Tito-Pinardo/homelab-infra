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
    """Devuelve las cabeceras para llamar a Qdrant."""
    ...


def _embed(text: str) -> list[float]:
    """Calcula el vector de embedding de un texto."""
    ...


def ensure_collection(collection: str):
    """Crea una coleccion si no existe."""
    ...


def search(collection: str, query: str, limit: int = 5, filter_: dict | None = None) -> list[dict]:
    """Busca por similitud en una coleccion."""
    ...


def scroll(collection: str, filter_: dict, limit: int = 50) -> list[dict]:
    """Lista puntos de una coleccion segun un filtro."""
    ...


def index(collection: str, point_id: str, text: str, payload: dict):
    """Indexa un texto en una coleccion."""
    ...
