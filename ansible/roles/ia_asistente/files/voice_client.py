"""
Cliente STT/TTS - igual que el modelo de chat, corre en el PC lucifer
(whisper.cpp para transcribir, Piper para sintetizar), NUNCA en un servicio
de terceros ("nada sale de mi red"). Si el PC esta apagado, ambas llamadas
fallan igual que local_llm_client - el bot debe tratarlo como lo mismo:
"modelo local no disponible".
"""
import os

import requests

PC_HOST = os.environ.get("VOICE_PC_HOST", "192.0.2.30")
WHISPER_URL = f"http://{PC_HOST}:8090"
PIPER_URL = f"http://{PC_HOST}:8091"

CONNECT_TIMEOUT = 4


class VozNoDisponible(Exception):
    pass


def transcribe(audio_bytes: bytes, filename: str = "audio.ogg") -> str:
    ...


def synthesize(text: str) -> bytes:
    ...
