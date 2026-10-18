"""Composicion de los avisos que Hermes manda a las salas de Element.

Cada funcion devuelve `(texto, html)`: Matrix manda las dos versiones en el
mismo evento (`body` y `formatted_body`), asi que Element muestra el formato
y cualquier cliente que no lo soporte - o la notificacion del movil - sigue
leyendose bien. Por eso el texto plano no es un descarte: se cuida igual.

TODO lo que venga de fuera (asunto de un correo, titulo de un evento creado
desde una reserva, nombre de un contenedor) pasa por `html.escape`: son
datos, no marcado. Un asunto con `<b>` o con una etiqueta rara no debe poder
cambiar como se ve un aviso, y mucho menos inyectar nada en el cliente.
"""
import html
import re
import unicodedata
from datetime import datetime

DIAS = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


def fecha_bonita(iso: str) -> str:
    """'2026-09-25T19:00:00+02:00' -> 'jueves 25 sep, 19:00'.

    Si no se puede interpretar se devuelve tal cual: un aviso con la fecha
    en crudo es feo, pero perder el dato es peor.
    """
    ...


def falta_para(iso: str, ahora: datetime | None = None) -> str:
    """'2026-09-25T19:00:00+02:00' -> 'dentro de 2 dias' (el miercoles 23).

    Restar dos fechas es aritmetica, no razonamiento, y el modelo la hace
    mal: el 2026-09-23 a las 18:15, para una pelicula del viernes 25 a las
    19:00, contesto "faltan 2 dias y 18 horas" una vez y "falta 1 hora y 46
    minutos" otra. Lo correcto eran 2 dias y 45 minutos. Se calcula aqui y
    el modelo se limita a leerlo, igual que con el dia de la semana.

    Por debajo de un dia se dan horas o minutos, porque es lo util para algo
    que pasa hoy; por encima, dias de calendario, que es como habla la gente
    ("pasado manana" son dos dias aunque falten 47 horas).
    """
    ...


def _bloque(titulo: str, campos: list[tuple[str, str]] | None = None,
            lineas: list[str] | None = None, nota: str | None = None) -> tuple[str, str]:
    """Estructura comun: titulo, pares etiqueta/valor, lista y nota al pie."""
    ...


def evento_creado(titulo: str, inicio: str, lugar: str = "", categoria: str = "",
                  origen: str = "", emoji_deshacer: str = "🗑️") -> tuple[str, str]:
    ...


COMERCIOS = {
    "loteriasyapuestas.es": "Loterías y Apuestas", "poecurrency.com": "poecurrency",
    "aliexpress.com": "AliExpress", "amazon.es": "Amazon", "anthropic.com": "Anthropic",
    "openai.com": "OpenAI",
}


def importe(minor: int, moneda: str = "EUR") -> str:
    """1234567 -> '12.345,67 €'. En enteros: el dinero no pasa por float."""
    ...


def compra_registrada(comercio: str, total_minor: int, moneda: str, fecha: str = "",
                      descripcion: str = "", categoria: str = "",
                      emoji_deshacer: str = "🗑️") -> tuple[str, str]:
    """Deméter ha aprobado una compra sola. Mismo contrato que un evento
    creado desde un correo: aviso con el dato y papelera para deshacerlo."""
    ...


def compra_quitada(conservado: bool = False) -> tuple[str, str]:
    ...


def compras_atrasadas(resumen: list[tuple[str, int, int, str]]) -> tuple[str, str]:
    """Un solo aviso para lo acumulado, en vez de uno por compra.

    `resumen` son tuplas (comercio, numero, total_minor, moneda). Sin esto,
    activar la automatica con 38 compras pendientes habria llenado la sala
    con 38 mensajes seguidos.
    """
    ...


def recordatorio(minutos: int, titulo: str, inicio: str = "", lugar: str = "") -> tuple[str, str]:
    ...


def correo_importante(de: str, cuenta: str, asunto: str, motivo: str) -> tuple[str, str]:
    ...


def avisos_tema(encabezado: str, avisos: list[str]) -> tuple[str, str]:
    """Mnemosine, Argos, Atlas, Hefesto, Hipnos, Nemesis, Jano.

    Estas salas solo hablan cuando hay algo anormal, asi que el mensaje va
    directo a la lista de lo que pasa, sin preambulo.
    """
    ...


def digest_diario(eventos: list[dict] | None, servidores: list[str],
                  incidencias: list[str], docker: list[str] | None = None) -> tuple[str, str]:
    """Pitia: el unico aviso que se manda todos los dias, haya algo o no.

    `eventos`: None si no se pudo consultar el calendario; se avisa en vez
    de decir que no hay nada.

    `docker`: resumen de contenedores caidos o con imagen nueva
    (docker_estado.lineas_pitia); None omite la seccion."""
    ...


def respuesta_en_cola(pregunta: str, respuesta: str) -> tuple[str, str]:
    """La respuesta a una pregunta que quedo encolada con el PC apagado.

    Se recuerda la pregunta porque puede haber pasado mucho tiempo, pero en
    formato de cita, para que lo que destaque sea la respuesta.
    """
    ...


_FILA_TABLA = re.compile(r"^\s*\|(.+)\|\s*$")
_SEPARADOR_TABLA = re.compile(r"^[\s|:-]+$")


def _celdas(linea: str) -> list[str]:
    ...


def _inline(texto_escapado: str) -> str:
    """Negritas, cursivas y `codigo` dentro de una linea ya escapada."""
    ...


def a_html(texto: str) -> str:
    """Respuestas del modelo: Markdown -> HTML que Element sabe pintar.

    El modelo escribe listas con guiones, negritas, `codigo` y hasta tablas
    de forma natural, y Element los mostraba en crudo (`- item`, `**esto**`)
    porque solo se convertian las negritas. Aqui se convierten listas,
    numeradas, tablas y codigo.

    El texto se escapa ANTES de cualquier conversion: lo unico que puede
    generar marcado es este codigo, nunca lo que escriba el modelo (que a su
    vez puede venir de un correo).
    """
    ...


_FIN_DE_FRASE = (".", ",", ":", ";", "!", "?", "…")


def _inline_voz(texto: str) -> str:
    """Quita el marcado inline de una linea, dejando solo lo que se dice."""
    ...


def _frase(texto: str) -> str:
    ...


def a_voz(texto: str) -> str:
    """Respuestas del modelo: Markdown -> texto para leer en voz alta.

    El mismo texto que Element pinta con a_html iba tal cual a Piper, que
    leia los asteriscos, almohadillas y barras de las tablas (peticion del
    usuario, 2026-09-24). Aqui solo queda lo que se dice: cada linea, cada
    elemento de lista y cada fila de tabla acaba en punto para que la voz
    haga la pausa, y una tabla se lee fila a fila como "cabecera: valor".
    """
    ...


def documento_recibido(nombre: str, caracteres: int) -> tuple[str, str]:
    """Un archivo subido al chat espera confirmacion antes de indexarse."""
    ...


def problema(que_fallo: str, detalle: str = "") -> tuple[str, str]:
    """Un fallo del bot (no del modelo): descarga, cifrado, voz, calendario.

    Se separa el "que" del "detalle tecnico" para que se lea de un vistazo
    sin perder la informacion que hace falta para depurarlo.
    """
    ...


def servidor_juego(nombre: str, encendido: bool) -> tuple[str, str]:
    ...


def descripcion_evento(origen: str = "", asunto: str = "", categoria: str = "",
                       emoji_deshacer: str = "🗑️") -> str:
    """Descripcion del evento tal y como se vera DENTRO de Google Calendar.

    Google renderiza un subconjunto de HTML en este campo, asi que las
    etiquetas van en negrita y cada dato en su linea, en vez de la frase
    corrida de antes ("Creado automaticamente desde un correo de X. Lugar:
    Y."). El lugar ya no va aqui: tiene su propio campo `location`.

    Se escapa todo lo que viene del correo, igual que en los avisos.
    """
    ...
