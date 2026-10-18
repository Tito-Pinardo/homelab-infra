#!/home/lucifer/.local/share/kokoro-tts/venv/bin/python
"""
Envoltorio HTTP de la voz de Hermes con Kokoro (2026-09-24), sustituto de
piper-bridge.py: misma API (POST /speak {"text": ...} -> audio/wav) y mismo
puerto, asi que el bot (voice_client.synthesize, CT ia-asistente) no cambia.

Voz que elegi tras escuchar muestras: mezcla 65 % em_alex
(espanol) + 35 % bm_george (ingles britanico), a velocidad 1.05 (0.95 al
principio; un 10 % mas rapida a peticion del usuario el mismo dia) - mas grave
y con mas aplomo que las voces espanolas solas.

El modelo se carga una vez y se queda en memoria (CPU, ~3 s por cada 14 s
de audio). Si Kokoro falla en una peticion, se genera con Piper como antes,
para que Hermes no se quede mudo. Solo accesible desde el CT ia-asistente
(regla ufw del puerto 8091), igual que antes.
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
    ...


def con_piper(texto: str) -> bytes:
    ...


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        ...

    def log_message(self, fmt, *args):
        ...


def main():
    ...


if __name__ == "__main__":
    main()
