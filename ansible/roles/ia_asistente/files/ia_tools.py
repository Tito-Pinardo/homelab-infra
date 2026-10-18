"""
Definicion de las tools que el modelo puede invocar, y su ejecucion real.
Fase 2: busqueda semantica en Obsidian. Fase 3: estado en vivo de AMP.
Fase 4: snapshot de Zabbix/Wazuh. Fase 5: busqueda de correo. Fase 7:
Cronos (Google Calendar).
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

# Documentos personales subidos por chat (2026-09-22): distinto de Paperless
# (aparcado a proposito por ser documentos oficiales/confidenciales) - este
# es contenido personal que el propio usuario decide pasarle al bot para que
# lo conozca (conversaciones exportadas de otras IAs, apuntes, etc.), nunca
# indexado sin que el usuario lo confirme explicitamente turno a turno.
DOCUMENTOS_COLLECTION = "documentos_personales"
PENDING_DOCUMENT_PATH = Path("/var/lib/ia-bot/pending_documento.json")
DOCUMENT_CHUNK_CHARS = 1500  # mismo limite que sync_obsidian.py (fisico de llama.cpp/Ollama, no negociable)

# Jano (2026-09-18): usuario de solo lectura dedicado en el MikroTik (grupo
# "read" nativo de RouterOS, sin permiso de escritura). Certificado local
# autofirmado del router - se desactiva la verificacion TLS a proposito
# (misma LAN, sin exposicion externa), no hay CA publica que lo firme.
requests.packages.urllib3.disable_warnings()  # noqa: E402
MIKROTIK_HOST = os.environ.get("MIKROTIK_HOST", "")
MIKROTIK_USER = os.environ.get("MIKROTIK_USER", "")
MIKROTIK_PASSWORD = os.environ.get("MIKROTIK_PASSWORD", "")

# Mnemosine (2026-09-17): mirror local (solo lectura, git-shell del otro
# lado no permite nada mas) del repo bare de respaldo, para poder leer la
# fecha del ultimo commit sin necesitar mas permiso que git-upload-pack.
BACKUP_CHECK_SSH_KEY = "/var/lib/ia-bot/.ssh/id_ed25519_backup_check"
BACKUP_REPO_URL = "ssh://git-backup@192.0.2.249/home/git-backup/infra-tf-backup.git"
BACKUP_CHECK_MIRROR = "/var/lib/ia-bot/backup_check_mirror"

# Argos (2026-09-17): dominios reales del homelab (mismos que
# dns_sync_domains en el repo) - el registro NO se renueva solo (a
# diferencia del certificado TLS, que si lo hace Let's Encrypt/Traefik).
ARGOS_DOMINIOS = ["example.org", "titopinardogutierrez.com", "example.net"]
ARGOS_WHOIS_SERVER_OVERRIDE = {
    # El cliente whois de Debian no trae la referencia correcta para .co -
    # sin esto devuelve "Name or service not known" (whois.nic.co no existe,
    # el servidor real es whois.registry.co, confirmado via whois.iana.org).
    "example.org": "whois.registry.co",
}
ARGOS_TLS_HOST = "traefik.example.org"
# Me conecto directamente a Traefik para ver su certificado de Let's Encrypt:
# por el dominio publico responderia el certificado de Cloudflare.
ARGOS_TLS_CONNECT = "192.0.2.6"

# Tools cuya invocacion debe ser visible en la sala ANTES de responder -
# decision explicita del usuario (transparencia sobre correo, y sobre
# cualquier escritura real como crear un evento). ia_bot.py usa este dict
# para formatear el aviso; cada entrada recibe los argumentos de la
# llamada y devuelve el texto del eco.
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
                "correo indexado del usuario (admin@example.org y "
                "admin@example.org). Sin cuenta consulta ambas "
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
                        "enum": ["admin@example.org", "admin@example.org"],
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
                "del homelab (example.org, titopinardogutierrez.com, "
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
    """Excluir encabezados vacíos y diversificar notas sin perder datos breves."""
    ...


def _buscar_obsidian(query: str) -> str:
    ...


def _get_game_servers_status(_args: dict) -> str:
    ...


def _load_snapshot() -> dict | None:
    ...


_CACHE: dict[str, tuple[float, str]] = {}


def cacheado(clave: str, ttl_segundos: int, fn):
    """Reutiliza el resultado de una tool lenta durante `ttl_segundos`.

    Medido el 2026-09-22: get_backup_status tarda 1,9s (git ls-remote contra
    el CT de respaldo), get_hefesto_status 1,4s (una llamada a la API de
    GitHub por servicio fijado) y get_cert_status 1,1s (handshake TLS + whois
    de tres dominios). Son datos que cambian en horas o dias, no entre dos
    preguntas seguidas, asi que pagar esos segundos en cada turno solo hace
    esperar al usuario.

    Deliberadamente en memoria del proceso: si el bot se reinicia, se vuelve
    a consultar. Y TTL corto, para que un cambio real (un commit nuevo, un
    certificado renovado) se vea enseguida.
    """
    ...


def _get_server_health(_args: dict) -> str:
    ...


def _get_ct_info(args: dict) -> str:
    ...


def _buscar_conversaciones(args: dict) -> str:
    ...


def _con_euros(dato):
    """Añade el importe en euros junto a cada campo en centimos de Demeter.

    Demeter habla en centimos ("net_minor": 3300) y el modelo tiene que
    dividir entre 100. Lo hacia mal: el 2026-09-23 respondio "3.300 €" por
    unos gastos de 33,00 €. Dividir es aritmetica; la hace Python y el
    modelo se limita a leer el campo ya formateado.
    """
    ...


def _aclarar_demeter(datos):
    """Nombres inequivocos para dos cosas que el modelo mezclaba.

    En el JSON de Demeter conviven `pending_count` (pedidos que aun no han
    llegado) y `coverage.review_count` (mensajes de correo capturados que
    nadie ha revisado todavia). Son cosas distintas y el 2026-09-23 Hermes
    respondio "0 pendientes de revision" habiendo 431, porque leyo el
    primero.

    Las claves ambiguas se SUSTITUYEN, no se duplican. Dejar las dos no
    bastaba: con los dos nombres delante, 3 de 6 respuestas seguian diciendo
    "0 pendientes de revision" en la misma frase en que avisaban de 146
    mensajes sin revisar (medido el 2026-09-23). Si el nombre ambiguo no
    viaja, no se puede leer mal.
    """
    ...


def _demeter(args: dict, accion: str) -> str:
    ...


def _search_purchases(args: dict) -> str:
    """Compras de Demeter y, si no tiene nada, el correo como respaldo.

    Demeter solo conoce lo que ha capturado (compras online). Una entrada de
    cine comprada en la web del cine llega por correo y no esta ahi. Medido
    en real el 2026-09-23 con "¿cuanto pague por las entradas de cine?":
    Demeter devolvia cero resultados y el modelo zanjaba con "revisa tu
    correo", teniendo el dato (22,50 €) en el correo ya indexado.

    Se intento antes por las dos vias que suelen funcionar y ninguna basto:
    la regla ya estaba en el SYSTEM_PROMPT, se probo un aviso pegado al
    resultado vacio, y se probo dejar el razonamiento activo para que
    encadenara. Con razonamiento encadena a veces (1 de 2); sin el, nunca.
    Asi que el respaldo se hace aqui, por codigo: deja de depender de que el
    modelo se acuerde. Mismo patron que el arreglo del 22-09, cuando
    `buscar_conversaciones` empezo a incluir documentos por codigo.

    Las dos fuentes van etiquetadas por separado: el importe de un correo no
    es un registro de Demeter y no debe confundirse con el.
    """
    ...


def _search_email(args: dict) -> str:
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


# Filtro de agenda por palabras con significado (2026-09-23). "¿Cuanto
# costo la entrada de la pelicula que tengo esta semana?" solo tiene una
# palabra que diga de que evento se habla: pelicula. Y el evento no la
# contiene: dice "Cine con ...". De ahi los sinonimos.
_SINONIMOS_EVENTO = {"pelicula": "cine", "peliculas": "cine", "peli": "cine", "pelis": "cine"}
_PALABRAS_VACIAS = frozenset("""
    cuanto cuanta cuantos cuantas costo cuesta costaron cuestan precio pague pagado importe
    entrada entradas que tengo tienes tiene tenemos esta este estos estas semana mes dia dias
    hoy manana cuando donde como cual cuales quien proxima proximo proximas proximos calendario
    evento eventos agenda algo hay para con por del los las una uno unos unas mis tus sus sobre
    desde hasta hora horas ver voy vamos
""".split())


def _normalizar(texto: str) -> str:
    ...


def _palabras_de_busqueda(query: str) -> set[str]:
    ...


def _por_palabras(query: str, eventos: list[dict]) -> list[dict]:
    """Eventos cuyo titulo, descripcion o categoria contienen alguna palabra
    con significado de la pregunta. Vacio si la pregunta no nombra nada."""
    ...


def _filtrar_eventos_por_relevancia(query: str, eventos: list[dict]) -> list[dict] | None:
    """Reduce una lista de eventos a los que responden a `query`. None si no
    se pudo decidir (fallo el LLM o el parseo) - en ese caso quien llame
    debe devolver la lista sin filtrar, nunca ocultar eventos por un fallo
    tecnico. Tres pasadas (ver runbook Fase 11/12; la segunda, 2026-09-23):

    1. Substring literal case-insensitive sobre titulo+descripcion+categoria
       - determinista y gratis, y cubre mas de lo que parece: "cine" SI es
       substring de "OCINE QUADERNILLOS" aunque Google Calendar (que separa
       por palabras completas) no lo encontrara con su propio filtro "q".
    2. Palabras con significado de la pregunta (con sinonimos: pelicula ->
       cine), tambien determinista. Ver _por_palabras.
    3. Si nada de eso encuentra algo, sub-prompt de LLM AISLADO (sin
       tools, sin el resto de contexto/instrucciones del bot) dedicado solo
       a esta pregunta. Bug real que motivo esto: el modelo principal, con
       las 18 tools y sus descripciones de gestion CRUD/conflictos en el
       prompt, confundia "aqui hay una lista de eventos" con "hay que
       verificar conflictos" en vez de simplemente identificar cual
       responde a la pregunta - probado que aislar la tarea en una llamada
       limpia lo arregla (15/15 y 8/8 en pruebas reales, ver runbook)."""
    ...


def _con_dia_de_la_semana(eventos: list[dict]) -> list[dict]:
    """Añade "cuando" y "falta" ya escritos a cada evento.

    Medido el 2026-09-23: preguntando "¿que tengo esta semana?" el modelo
    respondio "martes 28 de septiembre" cuando el 28 es lunes, y se salto un
    evento de ese mismo dia. Calcular el dia de la semana a partir de una
    fecha ISO es aritmetica, no razonamiento: la hace Python, que no se
    equivoca, y el modelo se limita a leerla. Mismo criterio que la tabla de
    los proximos siete dias del prompt.

    El campo `inicio` original se conserva: hace falta para los calculos de
    la propia herramienta y para responder en formato tecnico si se pide.
    """
    ...


def _get_calendar_events(args: dict) -> str:
    ...


def _create_calendar_event(args: dict) -> str:
    ...


def _create_recurring_calendar_event(args: dict) -> str:
    ...


def _update_calendar_event(args: dict) -> str:
    ...


def _delete_calendar_event(args: dict) -> str:
    ...


def _git_backup_freshness() -> dict:
    ...


def _get_backup_status(_args: dict) -> str:
    ...


def _whois_expiry(domain: str) -> str | None:
    ...


def _tls_cert_expiry(host: str, connect: str | None = None) -> str | None:
    ...


def _fecha_y_dias(texto: str | None) -> dict:
    """Normaliza un vencimiento a ISO y cuantos dias faltan.

    Las dos fuentes hablan distinto: openssl devuelve "Dec 12 23:23:50 2026
    GMT" y whois un ISO con zona. Dejarlo asi obliga al modelo a interpretar
    formatos y a restar fechas, y el 2026-09-23 confundio el vencimiento del
    REGISTRO de un dominio con el del certificado wildcard. Convertir y
    restar es aritmetica: la hace Python.
    """
    ...


def _get_cert_status(_args: dict) -> str:
    ...


def _get_storage_health(_args: dict) -> str:
    ...


def docker_del_snapshot() -> tuple[list[dict], dict | None]:
    """Seccion "docker" del snapshot (estado e imagenes nuevas de cada CT,
    2026-09-23) y el snapshot entero, para saber su antiguedad."""
    ...


def _get_hefesto_status(_args: dict) -> str:
    ...


HIPNOS_UMBRAL_CPU_PCT = 90
HIPNOS_UMBRAL_RAM_PCT = 90


def _get_hipnos_status(_args: dict) -> str:
    ...


def _mikrotik_get(path: str):
    ...


def _get_jano_status(_args: dict) -> str:
    ...


def _get_nemesis_status(_args: dict) -> str:
    ...


class DocumentoNoSoportado(Exception):
    pass


def extract_document_text(raw: bytes, filename: str) -> str:
    """Extrae texto de un archivo recibido por chat. PDF via pdftotext
    (poppler-utils, mismo criterio "sin libreria de PDF en Python" que
    _pdf_attachments_text en sync_correo.py) - texto plano/Markdown se
    decodifica directo. Cualquier otro tipo se rechaza a proposito: no hay
    OCR ni parser de Office aqui todavia."""
    ...


def save_pending_document(filename: str, texto: str):
    ...


def load_pending_document() -> dict | None:
    ...


def clear_pending_document():
    ...


def _split_document(text: str, max_len: int = DOCUMENT_CHUNK_CHARS) -> list[str]:
    """Trocea por parrafo, nunca deja un chunk mas largo que max_len (limite
    fisico del batch de embeddings de Ollama, ver DOCUMENT_CHUNK_CHARS)."""
    ...


def _buscar_documentos(args: dict) -> str:
    ...


def _indexar_documento_pendiente(_args: dict) -> str:
    ...


def _descartar_documento_pendiente(_args: dict) -> str:
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

# Tools con efecto real fuera del bot (crear/editar/borrar en el calendario,
# indexar un documento). Nunca se invocan por iniciativa propia del codigo:
# ver `ia_bot.tool_a_reintentar`, que solo reintenta las de lectura.
TOOLS_ESCRITURA = {
    "create_calendar_event",
    "create_recurring_calendar_event",
    "update_calendar_event",
    "delete_calendar_event",
    "indexar_documento_pendiente",
    "descartar_documento_pendiente",
}


def _corregir_tipo(valor, tipo: str):
    """Convierte lo que manda el modelo al tipo que declara el esquema.

    Los modelos pequeños mandan numeros y booleanos como TEXTO: `"7"` en vez
    de `7`, `"false"` en vez de `false`. Es un fallo documentado de varios
    candidatos de la comparativa del 2026-09-18 (`llama3.1:8b` quedo
    descartado por esto) y qwen3 tampoco esta libre. Sin corregirlo, el
    codigo de la tool revienta con TypeError y el usuario recibe un
    "Error ejecutando ..." en vez de una respuesta.

    Devuelve el valor original si no se puede convertir: prefiero que falle
    la tool con su propio mensaje a inventarme un valor.
    """
    ...


def validar_argumentos(name: str, arguments: dict) -> tuple[dict, str | None]:
    """(argumentos corregidos, error para el modelo si falta algo obligatorio).

    El error se devuelve COMO RESULTADO de la tool, no como excepcion: asi el
    modelo lo lee y puede reintentar con los campos que faltan, en vez de que
    el usuario reciba un fallo tecnico.
    """
    ...


def run_tool(name: str, arguments: dict) -> str:
    ...
