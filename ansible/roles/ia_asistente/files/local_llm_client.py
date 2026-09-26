"""Cliente del modelo de chat local (Ollama).

El razonamiento corre en mi PC y nada sale de mi red. Si el PC esta
apagado el bot no puede responder, por eso el tiempo de conexion es corto y
el de lectura largo.
"""
import os

import requests

LLM_URL = os.environ["LLM_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
# Contexto suficiente para el catalogo de herramientas y el razonamiento.
LLM_NUM_CTX = int(os.environ.get("LLM_NUM_CTX", "8192"))

CONNECT_TIMEOUT = 4
READ_TIMEOUT = 180

# Una carga del modelo en la GPU tarda del orden de segundos; por debajo de
# este umbral Ollama solo esta reutilizando el modelo que ya tenia cargado.
CARGA_SIGNIFICATIVA_S = 1.0


class ModeloNoDisponible(Exception):
    """El PC con el modelo local no esta encendido o no responde."""


def reparto_gpu() -> str:
    """Devuelve que parte del modelo esta cargada en la GPU."""
    ...


def is_available() -> bool:
    """Indica si el modelo local esta disponible."""
    ...


def chat(messages: list[dict], tools: list[dict] | None = None, think: bool = True) -> dict:
    """Envia una conversacion al modelo local y devuelve su respuesta."""
    ...


def metricas(data: dict) -> str:
    """Devuelve una linea de log con las metricas de una respuesta."""
    ...
