#!/home/usuario/.local/share/kokoro-tts/venv/bin/python
"""Servidor HTTP de la voz de Hermes con Kokoro. Misma API que el servidor de
Piper al que sustituye (POST /speak con texto, devuelve audio/wav). Si
Kokoro falla, usa Piper como respaldo.
"""
import io
import json
import os
import subprocess
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

KOKORO_DIR = Path.home() / ".local/share/kokoro-tts"
MEZCLA = [("em_alex", 0.65), ("bm_george", 0.35)]
VELOCIDAD = 1.05
PIPER_BIN = str(Path.home() / ".local/share/piper/piper")
PIPER_VOZ = str(Path.home() / ".local/share/piper-voices/es_ES-sharvard-medium.onnx")
LISTEN_PORT = int(os.environ.get("HERMES_VOZ_PORT", "8091"))

kokoro = Kokoro(str(KOKORO_DIR / "kokoro-v1.0.onnx"), str(KOKORO_DIR / "voices-v1.0.bin"))
VOZ = sum(peso * kokoro.get_voice_style(nombre) for nombre, peso in MEZCLA)
# Una sintesis a la vez: onnxruntime ya usa todos los nucleos.
cerrojo = threading.Lock()


def con_kokoro(texto: str) -> bytes:
    """Sintetiza voz con Kokoro."""
    ...


def con_piper(texto: str) -> bytes:
    """Sintetiza voz con Piper."""
    ...


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Recibe un texto y devuelve el audio sintetizado."""
        ...

    def log_message(self, fmt, *args):
        """Silencia el log por peticion."""
        ...


def main():
    """Punto de entrada: arranca el servidor HTTP de voz."""
    ...


if __name__ == "__main__":
    main()
