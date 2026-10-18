"""
Cliente del modelo de CHAT (razonamiento + tool-use). Deliberadamente NO es
Claude API: decidi que el razonamiento corra 100% local, en mi
PC (Ollama + RTX 2070S) - "nada sale de mi red" (ver runbook "Asistente IA +
base semantica"). Consecuencia aceptada: si ese PC esta apagado, el bot no
puede responder - por eso el timeout de CONEXION es corto (se detecta
"apagado" en segundos), aunque el de LECTURA es largo (generar una
respuesta con tool-use puede tardar).

Sin SDK de terceros (igual que el resto del repo): habla HTTP puro contra
el endpoint /api/chat de Ollama, que acepta "tools" en el mismo formato de
function-calling que usa la API de OpenAI.
"""
import os

import requests

LLM_URL = os.environ["LLM_URL"]
LLM_MODEL = os.environ["LLM_MODEL"]
# 4096 agotaba el contexto con 18 herramientas y el razonamiento (eval 2026-09-20).
LLM_NUM_CTX = int(os.environ.get("LLM_NUM_CTX", "8192"))

CONNECT_TIMEOUT = 4
READ_TIMEOUT = 180

# Una carga del modelo en la GPU tarda del orden de segundos; por debajo de
# este umbral Ollama solo esta reutilizando el modelo que ya tenia cargado.
CARGA_SIGNIFICATIVA_S = 1.0


class ModeloNoDisponible(Exception):
    """El PC con el modelo local no esta encendido o no responde."""


def reparto_gpu() -> str:
    """Que parte del modelo esta realmente en la GPU, segun /api/ps.

    lucifer es el PC personal del usuario: si esta jugando, el juego ocupa
    VRAM y Ollama reparte el modelo entre GPU y CPU. Medido el 2026-09-22
    con Dragon's Dogma 2 abierto: 4,32 de 6,12 GiB en GPU (71%) y 17,5
    tokens/s, con la latencia del eval disparada (mediana 20s, maximo 50s)
    y un caso de eleccion de tool que pasaba por la mañana fallando 8 de 8
    por la tarde. Sin este dato en el log no hay forma de distinguir "el
    modelo razona mal" de "el modelo iba a medias en CPU".

    Nunca lanza: es telemetria, no puede romper una respuesta real.
    """
    ...


def is_available() -> bool:
    """Comprobacion barata (sin generar nada) para el vigilante de la cola
    de mensajes pendientes - solo mira si el PC/Ollama responden, no gasta
    una llamada de chat completa solo para preguntar "¿estas ahi?"."""
    ...


def chat(messages: list[dict], tools: list[dict] | None = None, think: bool = True) -> dict:
    ...


def metricas(data: dict) -> str:
    """Linea de log con lo que Ollama ya devuelve en cada respuesta.

    Sin esto, un "Hermes va lento" no se puede atribuir: puede ser la carga
    del modelo (se descarga solo tras 5 min sin uso, decision mia de
    no dejarlo residente), un prompt que crece, un razonamiento largo, o el
    reparto a CPU por VRAM ocupada. Cada una tiene un arreglo distinto.
    """
    ...
