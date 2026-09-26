"""Composicion de los avisos que Hermes manda a las salas de Element.

Cada funcion devuelve (texto, html): Matrix manda las dos versiones en el
mismo evento, asi que el texto plano se cuida igual.

Todo lo que viene de fuera (asuntos, titulos, nombres de contenedores) se
escapa: son datos, no marcado.
"""
import html
import re
import unicodedata
from datetime import datetime

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_bonita(iso: str) -> str:
    """Formatea una fecha ISO de forma legible."""
    ...


def falta_para(iso: str, ahora: datetime | None = None) -> str:
    """Describe cuanto falta hasta una fecha."""
    ...


def _bloque(titulo: str, campos: list[tuple[str, str]] | None = None,
            lineas: list[str] | None = None, nota: str | None = None) -> tuple[str, str]:
    """Compone un mensaje con titulo, pares etiqueta/valor, lista y nota al pie, en texto y HTML."""
    ...


def evento_creado(titulo: str, inicio: str, lugar: str = "", categoria: str = "",
                  origen: str = "", emoji_deshacer: str = "🗑️") -> tuple[str, str]:
    """Mensaje de evento de calendario creado automaticamente."""
    ...


COMERCIOS = {
    "loteriasyapuestas.es": "Loterías y Apuestas", "poecurrency.com": "poecurrency",
    "aliexpress.com": "AliExpress", "amazon.es": "Amazon", "anthropic.com": "Anthropic",
    "openai.com": "OpenAI",
}


def importe(minor: int, moneda: str = "EUR") -> str:
    """Formatea un importe en centimos como euros."""
    ...


def compra_registrada(comercio: str, total_minor: int, moneda: str, fecha: str = "",
                      descripcion: str = "", categoria: str = "",
                      emoji_deshacer: str = "🗑️") -> tuple[str, str]:
    """Mensaje de compra registrada automaticamente."""
    ...


def compra_quitada(conservado: bool = False) -> tuple[str, str]:
    """Mensaje de compra retirada."""
    ...


def compras_atrasadas(resumen: list[tuple[str, int, int, str]]) -> tuple[str, str]:
    """Mensaje unico con las compras acumuladas pendientes de anunciar."""
    ...


def recordatorio(minutos: int, titulo: str, inicio: str = "", lugar: str = "") -> tuple[str, str]:
    """Mensaje de recordatorio de un evento proximo."""
    ...


def correo_importante(de: str, cuenta: str, asunto: str, motivo: str) -> tuple[str, str]:
    """Mensaje de aviso de correo importante."""
    ...


def avisos_tema(encabezado: str, avisos: list[str]) -> tuple[str, str]:
    """Mensaje con los avisos de un tema de vigilancia."""
    ...


def digest_diario(eventos: list[dict] | None, servidores: list[str],
                  incidencias: list[str], docker: list[str] | None = None) -> tuple[str, str]:
    """Mensaje del resumen diario."""
    ...


def respuesta_en_cola(pregunta: str, respuesta: str) -> tuple[str, str]:
    """Mensaje con la respuesta a una pregunta que estaba en cola."""
    ...


_FILA_TABLA = re.compile(r"^\s*\|(.+)\|\s*$")
_SEPARADOR_TABLA = re.compile(r"^[\s|:-]+$")


def _celdas(linea: str) -> list[str]:
    """Separa las celdas de una fila de tabla Markdown."""
    ...


def _inline(texto_escapado: str) -> str:
    """Convierte el formato en linea de Markdown a HTML."""
    ...


def a_html(texto: str) -> str:
    """Convierte una respuesta en Markdown a HTML para Element."""
    ...


_FIN_DE_FRASE = (".", ",", ":", ";", "!", "?", "…")


def _inline_voz(texto: str) -> str:
    """Quita el formato en linea de Markdown para leerlo en voz alta."""
    ...


def _frase(texto: str) -> str:
    """Asegura que un texto termina como una frase."""
    ...


def a_voz(texto: str) -> str:
    """Convierte una respuesta en Markdown a texto para leer en voz alta."""
    ...


def documento_recibido(nombre: str, caracteres: int) -> tuple[str, str]:
    """Mensaje de documento recibido pendiente de confirmacion."""
    ...


def problema(que_fallo: str, detalle: str = "") -> tuple[str, str]:
    """Mensaje de fallo interno del bot."""
    ...


def servidor_juego(nombre: str, encendido: bool) -> tuple[str, str]:
    """Mensaje de servidor de juego encendido o apagado."""
    ...


def descripcion_evento(origen: str = "", asunto: str = "", categoria: str = "",
                       emoji_deshacer: str = "🗑️") -> str:
    """Texto de la descripcion de un evento creado automaticamente."""
    ...
