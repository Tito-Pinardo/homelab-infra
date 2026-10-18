"""
Cronos - Google Calendar (cuenta admin@example.org), lectura y
escritura de eventos. OAuth "TV y dispositivos de entrada limitada"
(device flow): sin URL de callback, encaja con un CT sin navegador. La
autorizacion inicial es un paso manual UNICO (cronos_authorize.py, el
usuario visita una URL y teclea un codigo desde cualquier navegador -
este script nunca ve ni pide la contrasena de Google). Despues, el
access token se renueva solo con el refresh_token guardado en disco.

Todas las fechas/horas que create_event recibe se asumen hora local de
Madrid - se le pasa el nombre de la zona horaria a la API de Google en
vez de convertir nosotros mismos a UTC, para no arriesgar un calculo de
offset (DST) mal hecho.
"""
import json
import os
import time
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import requests

CLIENT_ID = os.environ["GOOGLE_CALENDAR_CLIENT_ID"]
CLIENT_SECRET = os.environ["GOOGLE_CALENDAR_CLIENT_SECRET"]
CALENDAR_ID = os.environ.get("GOOGLE_CALENDAR_ID", "primary")
TIMEZONE = "Europe/Madrid"
MADRID_TZ = ZoneInfo(TIMEZONE)
_BYDAY = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"]

TOKEN_PATH = "/var/lib/ia-bot/cronos_token.json"
SCOPE = "https://www.googleapis.com/auth/calendar"
DEVICE_CODE_URL = "https://oauth2.googleapis.com/device/code"
TOKEN_URL = "https://oauth2.googleapis.com/token"
API_BASE = "https://www.googleapis.com/calendar/v3"


class CronosNoAutorizado(Exception):
    """Aun no se ha hecho la autorizacion inicial (correr cronos_authorize.py una vez)."""


def load_token() -> dict:
    ...


def save_token(data: dict):
    ...


def _access_token() -> str:
    ...


def _headers() -> dict:
    ...


def list_events(dias_adelante: int = 7) -> list[dict]:
    ...


def _to_utc_z(dt_local: datetime) -> str:
    """dt_local: naive, se asume hora de Madrid - localizado con zoneinfo (no
    a mano) para que el DST no lo estropee, mismo motivo que TIMEZONE arriba."""
    ...


def find_overlapping(inicio_dt: datetime, fin_dt: datetime, exclude_event_id: str | None = None) -> list[dict]:
    """Eventos ya existentes que se solapan con [inicio_dt, fin_dt). Los
    eventos de todo el dia (sin "dateTime", solo "date") no cuentan como
    solape de horario."""
    ...


def limpiar_titulo(titulo: str, maximo: int = 200) -> str:
    """Un titulo sacado de un correo puede traer saltos de linea, dobles
    espacios o venir enorme. En el calendario eso se ve mal (y Google lo
    corta donde le parece), asi que se normaliza aqui: una sola linea,
    espacios simples y un corte limpio si se pasa de largo."""
    ...


def create_event(
    titulo: str,
    inicio_local: str,
    duracion_minutos: int = 60,
    descripcion: str = "",
    forzar: bool = False,
    categoria: str | None = None,
    lugar: str = "",
) -> dict:
    """inicio_local: "YYYY-MM-DDTHH:MM:SS" en hora de Madrid (sin offset -
    lo pone Google al indicarle timeZone explicitamente).

    Antes de crear comprueba solapamiento con eventos existentes - si hay y
    no se pide forzar=True, no crea nada y devuelve el conflicto para que
    quien llame (el modelo) se lo plantee al usuario en vez de decidir solo.

    `categoria` (cine/restaurante/viaje/...) se guarda en extendedProperties
    - metadata estructurada para poder buscar despues ("mi proxima
    pelicula") sin depender de que el titulo/descripcion contenga esa
    palabra literal. De momento solo la rellena extract_calendar_event
    (creacion automatica desde correo, que ya hace una llamada de LLM
    dedicada y puede pedirla sin coste extra) - ver runbook Fase 11/12."""
    ...


def create_recurring_event(
    titulo: str,
    primer_inicio_local: str,
    hasta_fecha: str,
    duracion_minutos: int = 60,
    descripcion: str = "",
    forzar: bool = False,
) -> dict:
    """Serie semanal de verdad (RRULE nativa de Google Calendar), no N
    eventos sueltos - mismo dia de la semana que primer_inicio_local, cada
    semana, hasta hasta_fecha ("YYYY-MM-DD", inclusive). Solo se comprueba
    solapamiento de la PRIMERA ocurrencia (comprobar todas seria una
    llamada por semana sin mucho valor real)."""
    ...


def update_event(
    event_id: str,
    titulo: str | None = None,
    inicio_local: str | None = None,
    duracion_minutos: int | None = None,
    descripcion: str | None = None,
    forzar: bool = False,
) -> dict:
    """Actualiza SOLO los campos indicados (PATCH) - el resto del evento no
    se toca. Bug real (2026-09-17): sin esto, "pedir una actualizacion" del
    mismo evento acababa creando uno nuevo casi identico en vez de tocar
    el que ya existia."""
    ...


def delete_event(event_id: str) -> None:
    ...
