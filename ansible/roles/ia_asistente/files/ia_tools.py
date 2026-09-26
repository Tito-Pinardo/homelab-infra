"""Herramientas que el modelo puede invocar y su ejecucion: notas, servidores
de juego, monitorizacion, correo, calendario, compras y documentos.
"""
import json
import os
import re
import unicodedata
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

import demeter_client
import docker_estado
import amp_client
import mensajes
import cronos_client
import qdrant_client
import requests
from local_llm_client import ModeloNoDisponible, chat

MONITORING_SNAPSHOT_PATH = Path("/var/lib/monitoring-push/monitoring_snapshot.json")
VERSIONES_PINNED_PATH = Path("/var/lib/ia-bot/versiones_pinned.json")

# Documentos personales que yo decido pasarle al bot por chat. Nunca se
# indexan sin mi confirmacion explicita.
DOCUMENTOS_COLLECTION = "documentos_personales"
PENDING_DOCUMENT_PATH = Path("/var/lib/ia-bot/pending_documento.json")
DOCUMENT_CHUNK_CHARS = 1500  # mismo limite que sync_obsidian.py (limite fisico del modelo de embeddings)

# Acceso al router con un usuario dedicado de solo lectura.
requests.packages.urllib3.disable_warnings()  # noqa: E402
MIKROTIK_HOST = os.environ.get("MIKROTIK_HOST", "")
MIKROTIK_USER = os.environ.get("MIKROTIK_USER", "")
MIKROTIK_PASSWORD = os.environ.get("MIKROTIK_PASSWORD", "")

# Copia local de solo lectura del repositorio de respaldo, para leer la
# fecha del ultimo commit.
BACKUP_CHECK_SSH_KEY = "/var/lib/ia-bot/.ssh/id_ed25519_backup_check"
BACKUP_REPO_URL = "ssh://git-backup@192.0.2.28/home/git-backup/infra-tf-backup.git"
BACKUP_CHECK_MIRROR = "/var/lib/ia-bot/backup_check_mirror"

# Dominios cuyo registro vigilo: el registro no se renueva solo, a
# diferencia del certificado TLS.
ARGOS_DOMINIOS = ["example.org", "example.com", "example.net"]
# Servidor whois por dominio cuando el cliente de Debian no trae el correcto
# para su TLD. Se define en la configuracion privada.
ARGOS_WHOIS_SERVER_OVERRIDE: dict[str, str] = {}
ARGOS_TLS_HOST = "traefik.example.org"

# Herramientas cuya invocacion se muestra en la sala antes de responder,
# por transparencia (consultas de correo y cualquier escritura real). Cada
# entrada recibe los argumentos y devuelve el texto del aviso.
ECHO_TOOLS = {
    "search_email": lambda args: f"🔍 Consultando correo: \"{args.get('query', '?')}\"",
    "create_calendar_event": lambda args: f"📅 Creando en el calendario: \"{args.get('titulo', '?')}\" ({args.get('inicio_local', '?')})",
    "create_recurring_calendar_event": lambda args: f"📅 Creando serie semanal: \"{args.get('titulo', '?')}\" desde {args.get('primer_inicio_local', '?')} hasta {args.get('hasta_fecha', '?')}",
    "update_calendar_event": lambda args: f"📅 Modificando evento {args.get('event_id', '?')}: {', '.join(k for k in ('titulo', 'inicio_local', 'duracion_minutos', 'descripcion') if k in args)}",
    "delete_calendar_event": lambda args: f"📅 Borrando evento {args.get('event_id', '?')}",
    "indexar_documento_pendiente": lambda args: "📄 Guardando el documento en tu memoria personal (puede tardar si es largo)...",
}

TOOLS = [
    {"type":"function","function":{
        "name":"get_expenses_summary",
        "description":"Consulta Deméter local: gastos de un mes, totales exactos por moneda, categorías y comercios, historial mensual. Usar para cuánto gasté este mes o el mes pasado. Solo compras registradas; devuelve cobertura y pendientes de revisión. No consultar correo para sumar gastos.",
        "parameters":{"type":"object","properties":{"month":{"type":"string","description":"Mes YYYY-MM; omitir para este mes en Madrid."}},"additionalProperties":False}}},
    {"type":"function","function":{
        "name":"search_purchases",
        "description":"Busca en Deméter local compras por producto, comercio o referencia. Usar para cuánto costó algo, facturas Anthropic y compras Amazon. El importe es total del pedido, no precio unitario. Si faltan resultados puede consultarse search_email después.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Producto o comercio concreto, sin añadir precio ni palabras como compra."},"month":{"type":"string","description":"Mes YYYY-MM opcional; omitir para todo el historial."}},"required":["query"],"additionalProperties":False}}},
    {"type":"function","function":{
        "name":"get_pending_orders",
        "description":"Consulta pedidos Amazon pendientes de comprobar o recibir en Deméter local, con avisos de envío/entrega y fecha prevista si consta. Sin acceso en vivo a Amazon. Una entrega de paquete no confirma todo el pedido. No usa calendario ni correo semántico.",
        "parameters":{"type":"object","properties":{"query":{"type":"string","description":"Producto o referencia opcional; omitir para todos los pedidos pendientes."}},"additionalProperties":False}}},
    {
        "type": "function",
        "function": {
            "name": "buscar_obsidian",
            "description": (
                "Busca en las notas del vault de Obsidian del usuario por "
                "significado (busqueda semantica), no por texto literal. "
                "Usalo para cualquier pregunta sobre el homelab, proyectos, "
                "procedimientos o historial documentado en el vault."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "La pregunta o tema a buscar, en lenguaje natural.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_game_servers_status",
            "description": (
                "Devuelve el estado EN VIVO (ahora mismo, no historico) de "
                "los servidores de juego gestionados por AMP (Minecraft, "
                "Velocity, etc.): si estan encendidos, uso de CPU/RAM, y "
                "jugadores activos ahora mismo. Usalo siempre que pregunten "
                "por el estado, rendimiento o jugadores conectados de un "
                "servidor de juego - nunca respondas eso solo con buscar_obsidian."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_server_health",
            "description": (
                "Devuelve problemas activos de Zabbix, agentes Wazuh no "
                "activos, y el uso GENERAL de recursos del host Proxmox "
                "entero (CPU, RAM, almacenamiento totales). NO uses esta "
                "tool si preguntan por UN contenedor concreto (su IP, su "
                "estado, cuanta RAM usa) - para eso usa get_ct_info, que "
                "devuelve solo ese contenedor en vez de la lista completa. "
                "Usa get_server_health solo para problemas/alertas o para "
                "el estado GENERAL de todo el host. NO es en vivo al "
                "segundo - es un snapshot que se actualiza cada 5-10 min "
                "(la respuesta indica su antiguedad)."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_ct_info",
            "description": (
                "Devuelve la info de UN contenedor (CT) concreto por "
                "nombre: IP, si esta encendido o apagado, y cuanto CPU/"
                "RAM/disco usa. Usala siempre que pregunten por un "
                "servicio o contenedor especifico (plex, synapse, amp, "
                "n8n, etc) en vez de get_server_health, que devuelve TODOS "
                "los contenedores a la vez."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nombre": {
                        "type": "string",
                        "description": "Nombre (o parte del nombre) del contenedor, ej. 'plex'.",
                    }
                },
                "required": ["nombre"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_conversaciones",
            "description": (
                "Busca en el HISTORICO de conversaciones pasadas con el "
                "usuario (todo lo que se ha hablado antes en este chat, no "
                "solo el contexto reciente) - usalo SOLO para preguntas "
                "sobre lo que se hablo o decidio antes (ej. 'que hice la "
                "semana pasada con X', 'que nota te dije que guardaras'). "
                "NUNCA la uses para preguntas sobre datos en vivo del "
                "homelab (IPs, estado de un CT, problemas del servidor, "
                "recursos) aunque encuentres una respuesta previa que "
                "parezca encajar - una respuesta tuya de otra vez puede "
                "haber sido incorrecta, y citarte a ti mismo no la hace "
                "mas fiable. Para eso usa get_ct_info para un CT o get_server_health para el estado general, de "
                "nuevo, cada vez, aunque ya lo hayas preguntado antes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "El tema o pregunta a buscar en conversaciones pasadas.",
                    },
                    "dias_atras": {
                        "type": "integer",
                        "description": "Opcional: limitar la busqueda a los ultimos N dias (ej. 7 para 'la semana pasada').",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_email",
            "description": (
                "Busca por significado en el INBOX de las dos cuentas de "
                "correo indexado del usuario (cuenta1@example.com y "
                "cuenta2@example.com). Sin cuenta consulta ambas "
                "en una sola llamada. Incluye los mensajes conservados en el indice, "
                "sin un limite de antiguedad en esta busqueda. Usala por iniciativa propia (no hace falta que el "
                "usuario diga la palabra 'correo') siempre que la pregunta "
                "pueda responderse con algo que normalmente llega por "
                "email: horarios o confirmaciones de clases/actividades, "
                "reservas, facturas, pagos, citas, billetes, inscripciones, "
                "etc. Cada uso queda siempre visible en la sala antes de "
                "responder, asi que usala con normalidad cuando pueda "
                "ayudar - no hay que ser conservador por privacidad, eso "
                "ya lo cubre el aviso visible."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "El tema o pregunta a buscar en los correos.",
                    },
                    "cuenta": {
                        "type": "string",
                        "enum": ["cuenta1@example.com", "cuenta2@example.com"],
                        "description": "Opcional: limitar la busqueda a una sola cuenta.",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": (
                "Devuelve los proximos eventos del calendario de Google del "
                "usuario (Cronos). Usala para preguntas sobre que tiene "
                "planeado, citas, o para comprobar si ya existe algo antes "
                "de crear un evento nuevo. Si buscas algo CONCRETO entre "
                "varios eventos (ej. 'la pelicula', 'la cita con el "
                "dentista') usa el parametro query - te devuelve solo lo "
                "que encaja en vez de la lista entera."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "dias_adelante": {
                        "type": "integer",
                        "description": "Cuantos dias hacia adelante mirar (por defecto 7).",
                    },
                    "query": {
                        "type": "string",
                        "description": "Opcional: palabra clave para filtrar (ej. 'cine', 'dentista') cuando buscas un evento concreto, no toda la agenda.",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_calendar_event",
            "description": (
                "Crea un evento NUEVO en el calendario (Cronos). Sirve "
                "tambien para 'recordatorios' (un recordatorio es un "
                "evento corto). Si el usuario quiere completar/corregir un "
                "evento QUE YA EXISTE, usa update_calendar_event en vez de "
                "esta (evita duplicados). Para varios eventos sueltos en un "
                "mismo mensaje, llama a esta tool una vez por cada uno. "
                "Para una serie semanal ('todos los domingos...') usa "
                "create_recurring_calendar_event. Si la respuesta trae "
                "'conflicto': true, hay un evento que se solapa - pregunta "
                "al usuario antes de repetir la llamada con forzar=true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Titulo corto del evento/recordatorio."},
                    "inicio_local": {
                        "type": "string",
                        "description": "Fecha y hora de inicio en hora de Madrid, formato 'YYYY-MM-DDTHH:MM:SS'.",
                    },
                    "duracion_minutos": {
                        "type": "integer",
                        "description": "Duracion en minutos (por defecto 60; para un recordatorio simple usa algo corto como 5-15).",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Opcional: detalles adicionales.",
                    },
                    "forzar": {
                        "type": "boolean",
                        "description": "true SOLO si el usuario ya confirmo crear el evento pese al conflicto avisado antes.",
                    },
                },
                "required": ["titulo", "inicio_local"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_recurring_calendar_event",
            "description": (
                "Crea una SERIE semanal (mismo dia de la semana que "
                "primer_inicio_local) hasta una fecha limite - usala para "
                "'todos los domingos de tal hora a tal hora hasta X'. Es "
                "una sola serie real en el calendario, no N eventos "
                "sueltos. Para eventos SIN patron semanal usa "
                "create_calendar_event una vez por cada uno en vez de "
                "esta. Si la respuesta trae 'conflicto': true, pregunta al "
                "usuario antes de repetir la llamada con forzar=true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "titulo": {"type": "string", "description": "Titulo corto del evento."},
                    "primer_inicio_local": {
                        "type": "string",
                        "description": (
                            "Fecha y hora de la PRIMERA ocurrencia en hora "
                            "de Madrid, 'YYYY-MM-DDTHH:MM:SS' - el dia de "
                            "la semana de esta fecha es el que se repite."
                        ),
                    },
                    "hasta_fecha": {
                        "type": "string",
                        "description": "Ultimo dia (inclusive) en que puede caer una ocurrencia, formato 'YYYY-MM-DD'.",
                    },
                    "duracion_minutos": {
                        "type": "integer",
                        "description": "Duracion de cada ocurrencia en minutos (por defecto 60).",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Opcional: detalles adicionales.",
                    },
                    "forzar": {
                        "type": "boolean",
                        "description": "true SOLO si el usuario ya confirmo crear la serie pese al conflicto avisado antes.",
                    },
                },
                "required": ["titulo", "primer_inicio_local", "hasta_fecha"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_calendar_event",
            "description": (
                "Modifica un evento QUE YA EXISTE (Cronos) - solo cambia "
                "los campos indicados. Usala para corregir/completar un "
                "evento en vez de crear uno nuevo. Necesitas su ID - si no "
                "lo tienes, busca con get_calendar_events (amplia "
                "dias_adelante si no aparece en los 7 dias por defecto). Si "
                "cambias inicio_local sin indicar duracion_minutos, se "
                "mantiene la duracion original (el evento se desplaza, no "
                "se alarga). Si la respuesta trae 'conflicto': true, "
                "pregunta al usuario antes de repetir con forzar=true."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID del evento a modificar."},
                    "titulo": {"type": "string", "description": "Opcional: nuevo titulo."},
                    "inicio_local": {
                        "type": "string",
                        "description": "Opcional: nueva fecha/hora en hora de Madrid, 'YYYY-MM-DDTHH:MM:SS'.",
                    },
                    "duracion_minutos": {
                        "type": "integer",
                        "description": "Opcional: nueva duracion en minutos - si se omite se mantiene la que ya tenia el evento.",
                    },
                    "descripcion": {
                        "type": "string",
                        "description": "Opcional: nueva descripcion (sustituye a la anterior por completo).",
                    },
                    "forzar": {
                        "type": "boolean",
                        "description": "true SOLO si el usuario ya confirmo el cambio pese al conflicto avisado antes.",
                    },
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_calendar_event",
            "description": "Borra un evento del calendario (Cronos) por su ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "event_id": {"type": "string", "description": "ID del evento a borrar."},
                },
                "required": ["event_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_backup_status",
            "description": (
                "Mnemosine: estado de las copias de seguridad del homelab. "
                "Dice cuando fue el ultimo commit respaldado del repositorio "
                "infra-tf (bare repo en un CT distinto), y si Proxmox tiene "
                "algun job de backup automatico (vzdump) configurado para "
                "los contenedores/VMs. Usala para preguntas del tipo "
                "'¿estan los backups al dia?' o '¿hay copia de seguridad de "
                "X?'."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_cert_status",
            "description": (
                "Argos: vencimiento de certificados TLS y de los dominios "
                "del homelab (example.org, example.com, "
                "example.net). Usala para preguntas sobre si un "
                "certificado o un dominio esta a punto de caducar."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_storage_health",
            "description": (
                "Atlas: salud del almacenamiento del servidor - estado de "
                "los pools ZFS (raiz5, games: capacidad, salud, ultimo "
                "scrub), salud SMART de cada disco fisico, y uso de cada "
                "storage de Proxmox. Usala para preguntas sobre espacio en "
                "disco, discos duros, o si el almacenamiento esta bien."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hefesto_status",
            "description": (
                "Hefesto: actualizaciones pendientes del homelab - paquetes "
                "apt sin instalar en cada contenedor, y si alguna version "
                "fijada en el repo (Traefik, Qdrant, Element, Homepage, "
                "Ollama) esta desfasada respecto a la ultima release, y que "
                "contenedores Docker tienen imagen nueva publicada. Usala "
                "para preguntas sobre si hay que actualizar algo."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_hipnos_status",
            "description": (
                "Hipnos: contenedores con uso de CPU o RAM anormalmente "
                "alto ahora mismo (por encima de un umbral fijo, no hay "
                "historico de comparacion), y contenedores Docker caidos, "
                "reiniciandose o con el healthcheck fallando. Usala para "
                "preguntas sobre servidores lentos, colgados, caidos o con "
                "fugas de recursos."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nemesis_status",
            "description": (
                "Nemesis: recuento de intentos de login fallidos detectados "
                "hoy por Wazuh (posible fuerza bruta), agregados por "
                "servidor. Usala para preguntas sobre intentos de acceso "
                "sospechosos o ataques."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_jano_status",
            "description": (
                "Jano: estado de la red/WAN de casa - IP publica actual, "
                "si la conexion a internet (PPPoE) esta activa, y los "
                "peers de WireGuard con su ultimo handshake. Usala para "
                "preguntas sobre si hay internet, la IP publica, o la VPN."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "buscar_documentos",
            "description": (
                "Busca por significado en documentos personales que el "
                "usuario ha subido por el chat y decidido guardar "
                "(conversaciones exportadas de otras IAs, apuntes, etc.). "
                "Distinto de buscar_obsidian (procedimientos del homelab) y "
                "buscar_conversaciones (lo hablado con Hermes)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "El tema o pregunta a buscar, en lenguaje natural.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "indexar_documento_pendiente",
            "description": (
                "Guarda en la memoria personal el ultimo documento que el "
                "usuario acaba de subir por el chat y sigue sin decision. "
                "Llamar SOLO si el usuario confirma que quiere guardarlo."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "descartar_documento_pendiente",
            "description": (
                "Descarta sin guardar el ultimo documento subido por el "
                "chat que sigue sin decision. Llamar si el usuario dice que "
                "no lo guarde."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _select_obsidian_hits(hits: list[dict], query: str, limit: int = 5) -> list[dict]:
    """Filtra y diversifica los resultados de busqueda en las notas."""
    ...


def _buscar_obsidian(query: str) -> str:
    """Herramienta: busca en las notas de Obsidian."""
    ...


def _get_game_servers_status(_args: dict) -> str:
    """Herramienta: devuelve el estado de los servidores de juego."""
    ...


def _load_snapshot() -> dict | None:
    """Devuelve la ultima instantanea de monitorizacion con su antiguedad, o None si no existe."""
    ...


_CACHE: dict[str, tuple[float, str]] = {}


def cacheado(clave: str, ttl_segundos: int, fn):
    """Decorador que reutiliza el resultado de una herramienta lenta durante un tiempo."""
    ...


def _get_server_health(_args: dict) -> str:
    """Herramienta: devuelve el estado general de los servidores."""
    ...


def _get_ct_info(args: dict) -> str:
    """Herramienta: devuelve la informacion de un contenedor concreto."""
    ...


def _buscar_conversaciones(args: dict) -> str:
    """Herramienta: busca en las conversaciones anteriores."""
    ...


def _con_euros(dato):
    """Anade el importe en euros junto a cada importe en centimos."""
    ...


def _aclarar_demeter(datos):
    """Renombra campos ambiguos de las respuestas de Demeter."""
    ...


def _demeter(args: dict, accion: str) -> str:
    """Consulta a Demeter una accion y devuelve la respuesta ya preparada para el modelo."""
    ...


def _search_purchases(args: dict) -> str:
    """Herramienta: busca compras en Demeter y, si no hay nada, en el correo."""
    ...


def _search_email(args: dict) -> str:
    """Herramienta: busca en el correo indexado."""
    ...


FILTRO_EVENTOS_PROMPT = (
    "Se te da la pregunta/palabra clave de un usuario y una lista numerada "
    "de eventos de su calendario. Devuelve SOLO los indices de los eventos "
    "que responden a la pregunta (por titulo, descripcion o categoria, con "
    "sentido comun - ej. una pregunta sobre 'la pelicula' la responde un "
    "evento de cine aunque no contenga literalmente la palabra pelicula). "
    "Si NINGUN evento encaja, devuelve una lista vacia - no inventes ni "
    "fuerces una coincidencia. Responde EXCLUSIVAMENTE con JSON: "
    '{"indices": [..]}. Nada mas, sin explicaciones.'
)


# Filtro de agenda por palabras con significado, con sinonimos para cuando
# la pregunta y el evento usan palabras distintas ("pelicula" y "cine").
_SINONIMOS_EVENTO = {"pelicula": "cine", "peliculas": "cine", "peli": "cine", "pelis": "cine"}
_PALABRAS_VACIAS = frozenset("""
    cuanto cuanta cuantos cuantas costo cuesta costaron cuestan precio pague pagado importe
    entrada entradas que tengo tienes tiene tenemos esta este estos estas semana mes dia dias
    hoy manana cuando donde como cual cuales quien proxima proximo proximas proximos calendario
    evento eventos agenda algo hay para con por del los las una uno unos unas mis tus sus sobre
    desde hasta hora horas ver voy vamos
""".split())


def _normalizar(texto: str) -> str:
    """Pasa un texto a minusculas y sin tildes."""
    ...


def _palabras_de_busqueda(query: str) -> set[str]:
    """Devuelve las palabras significativas de una busqueda, con sus sinonimos."""
    ...


def _por_palabras(query: str, eventos: list[dict]) -> list[dict]:
    """Devuelve los eventos que contienen alguna palabra de la busqueda."""
    ...


def _filtrar_eventos_por_relevancia(query: str, eventos: list[dict]) -> list[dict] | None:
    """Reduce una lista de eventos a los relacionados con la busqueda."""
    ...


def _con_dia_de_la_semana(eventos: list[dict]) -> list[dict]:
    """Anade a cada evento cuando es y cuanto falta, ya redactado."""
    ...


def _get_calendar_events(args: dict) -> str:
    """Herramienta: devuelve los proximos eventos del calendario."""
    ...


def _create_calendar_event(args: dict) -> str:
    """Herramienta: crea un evento en el calendario."""
    ...


def _create_recurring_calendar_event(args: dict) -> str:
    """Herramienta: crea un evento periodico en el calendario."""
    ...


def _update_calendar_event(args: dict) -> str:
    """Herramienta: modifica un evento del calendario."""
    ...


def _delete_calendar_event(args: dict) -> str:
    """Herramienta: borra un evento del calendario."""
    ...


def _git_backup_freshness() -> dict:
    """Devuelve la fecha del ultimo commit del repositorio de respaldo."""
    ...


def _get_backup_status(_args: dict) -> str:
    """Herramienta: devuelve el estado de las copias de seguridad."""
    ...


def _whois_expiry(domain: str) -> str | None:
    """Devuelve la fecha de vencimiento del registro de un dominio."""
    ...


def _tls_cert_expiry(host: str) -> str | None:
    """Devuelve la fecha de caducidad del certificado TLS de un host."""
    ...


def _fecha_y_dias(texto: str | None) -> dict:
    """Normaliza una fecha de vencimiento y calcula los dias que faltan."""
    ...


def _get_cert_status(_args: dict) -> str:
    """Herramienta: devuelve la caducidad de certificados y dominios."""
    ...


def _get_storage_health(_args: dict) -> str:
    """Herramienta: devuelve el estado del almacenamiento."""
    ...


def docker_del_snapshot() -> tuple[list[dict], dict | None]:
    """Devuelve la parte de Docker de la instantanea de monitorizacion."""
    ...


def _get_hefesto_status(_args: dict) -> str:
    """Herramienta: devuelve las actualizaciones pendientes y las versiones desfasadas."""
    ...


HIPNOS_UMBRAL_CPU_PCT = 90
HIPNOS_UMBRAL_RAM_PCT = 90


def _get_hipnos_status(_args: dict) -> str:
    """Herramienta: devuelve los contenedores con consumo anomalo."""
    ...


def _mikrotik_get(path: str):
    """Consulta un recurso de la API del router."""
    ...


def _get_jano_status(_args: dict) -> str:
    """Herramienta: devuelve el estado de la conexion a internet."""
    ...


def _get_nemesis_status(_args: dict) -> str:
    """Herramienta: devuelve los eventos de seguridad recientes."""
    ...


class DocumentoNoSoportado(Exception):
    pass


def extract_document_text(raw: bytes, filename: str) -> str:
    """Extrae el texto de un fichero recibido por chat."""
    ...


def save_pending_document(filename: str, texto: str):
    """Guarda un documento recibido a la espera de decidir si se indexa."""
    ...


def load_pending_document() -> dict | None:
    """Devuelve el documento pendiente de decision, o None."""
    ...


def clear_pending_document():
    """Borra el documento pendiente de decision."""
    ...


def _split_document(text: str, max_len: int = DOCUMENT_CHUNK_CHARS) -> list[str]:
    """Trocea un documento en fragmentos para indexarlo."""
    ...


def _buscar_documentos(args: dict) -> str:
    """Herramienta: busca en los documentos personales guardados."""
    ...


def _indexar_documento_pendiente(_args: dict) -> str:
    """Herramienta: indexa el documento pendiente."""
    ...


def _descartar_documento_pendiente(_args: dict) -> str:
    """Herramienta: descarta el documento pendiente sin guardarlo."""
    ...


DISPATCH = {
    "get_expenses_summary": lambda args: _demeter(args, "summary"),
    "search_purchases": _search_purchases,
    "get_pending_orders": lambda args: _demeter(args, "pending"),
    "buscar_obsidian": lambda args: _buscar_obsidian(args["query"]),
    "get_game_servers_status": _get_game_servers_status,
    "get_server_health": _get_server_health,
    "get_ct_info": _get_ct_info,
    "buscar_conversaciones": _buscar_conversaciones,
    "search_email": _search_email,
    "get_calendar_events": _get_calendar_events,
    "create_calendar_event": _create_calendar_event,
    "create_recurring_calendar_event": _create_recurring_calendar_event,
    "update_calendar_event": _update_calendar_event,
    "delete_calendar_event": _delete_calendar_event,
    "get_backup_status": lambda args: cacheado("backup", 300, lambda: _get_backup_status(args)),
    "get_cert_status": lambda args: cacheado("cert", 3600, lambda: _get_cert_status(args)),
    "get_storage_health": _get_storage_health,
    "get_hefesto_status": lambda args: cacheado("hefesto", 3600, lambda: _get_hefesto_status(args)),
    "get_hipnos_status": _get_hipnos_status,
    "get_nemesis_status": _get_nemesis_status,
    "get_jano_status": _get_jano_status,
    "buscar_documentos": _buscar_documentos,
    "indexar_documento_pendiente": _indexar_documento_pendiente,
    "descartar_documento_pendiente": _descartar_documento_pendiente,
}


ESQUEMAS = {t["function"]["name"]: t["function"].get("parameters", {}) for t in TOOLS}

# Herramientas con efecto real fuera del bot. El codigo nunca las invoca por
# su cuenta: `ia_bot.tool_a_reintentar` solo reintenta las de lectura.
TOOLS_ESCRITURA = {
    "create_calendar_event",
    "create_recurring_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
    "indexar_documento_pendiente",
    "descartar_documento_pendiente",
}


def _corregir_tipo(valor, tipo: str):
    """Convierte un argumento del modelo al tipo que declara el esquema."""
    ...


def validar_argumentos(name: str, arguments: dict) -> tuple[dict, str | None]:
    """Valida los argumentos de una herramienta y devuelve los corregidos y el error si falta algo."""
    ...


def run_tool(name: str, arguments: dict) -> str:
    """Ejecuta una herramienta por nombre y devuelve su resultado como texto."""
    ...
