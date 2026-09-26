"""Cliente de transcripcion y sintesis de voz. Igual que el modelo de chat,
corre en mi PC. Si esta apagado, se trata como modelo local no disponible.
"""
import os

import requests

PC_HOST = os.environ.get("VOICE_PC_HOST", "192.0.2.13")
WHISPER_URL = f"http://{PC_HOST}:8090"
PIPER_URL = f"http://{PC_HOST}:8091"

CONNECT_TIMEOUT = 4


class VozNoDisponible(Exception):
    pass


def transcribe(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    """Transcribe un audio a texto."""
    ...


def synthesize(text: str) -> bytes:
    """Genera audio a partir de un texto."""
    ...
