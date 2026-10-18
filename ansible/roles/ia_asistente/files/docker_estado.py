"""
Estado de Docker de los CT a partir de la seccion "docker" del snapshot de
monitorizacion (scripts/sync_monitoring_snapshot.py, get_docker_status).

Logica pura, sin red ni Matrix, para poder probarla: la usan Pitia (una
linea en el resumen diario), Hefesto (detalle de imagenes nuevas) e Hipnos
(avisos al momento cuando algo se cae).

Solo cuentan los contenedores de docker compose: los AMP_* los crea y apaga
el propio AMP al encender o apagar un servidor de juego (eso ya lo avisa la
sala de AMP), y no se actualizan con Ansible. Paperless (CT 119) ni
siquiera llega aqui: esta aislado y el snapshot no entra en el (CT_AISLADOS
en sync_monitoring_snapshot.py).
"""

# Pasadas seguidas (una cada 5 min) que tiene que durar un problema antes de
# avisar: un "docker compose up" que recrea un contenedor no debe despertar
# a nadie.
CONFIRMACIONES = 2

COMANDO_ACTUALIZAR = "ansible-playbook playbooks/update-containers.yml --limit {ct}"


def _de_compose(c: dict) -> bool:
    ...


def _consultables(docker: list[dict]):
    """CT en marcha y cuya consulta de Docker funciono."""
    ...


def caidos(docker: list[dict]) -> dict[str, str]:
    """Problemas actuales, clave estable -> texto para el usuario."""
    ...


def con_actualizacion(docker: list[dict]) -> list[dict]:
    """Por CT, los contenedores cuya imagen tiene una version publicada mas
    nueva. Sin los CT en los que no hay ninguno."""
    ...


def sin_comprobar(docker: list[dict]) -> list[str]:
    """Contenedores cuyo registro no respondio en la ultima consulta (no
    los construidos en local: esos no tienen registro que consultar)."""
    ...


def lineas_hefesto(docker: list[dict]) -> list[str]:
    ...


def lineas_pitia(docker: list[dict]) -> list[str]:
    """Resumen de una o dos lineas; el detalle va a Hefesto e Hipnos."""
    ...


def _reinicios(docker: list[dict]) -> dict[str, int]:
    ...


def transicion(estado: dict, docker: list[dict], otros: dict[str, str] | None = None) -> tuple[dict, list[str]]:
    """Hipnos al momento: que avisar desde la ultima pasada.

    `estado` es lo que devolvio la llamada anterior (vacio la primera vez).
    Avisa cuando un problema dura CONFIRMACIONES pasadas, cuando se resuelve,
    cuando un contenedor se reinicia solo y cuando uno que existia
    desaparece sin que su CT este caido (un "docker compose down" a mano, o
    se quito del compose: se avisa una vez y se olvida). `otros` son
    problemas ajenos a Docker con el mismo trato (p. ej. el snapshot sin
    actualizar: entonces no se sabe nada de los contenedores).
    """
    ...


def transicion_sin_datos(estado: dict, motivo: str) -> tuple[dict, list[str]]:
    """Snapshot ausente o viejo: se avisa de eso (con la misma confirmacion)
    y lo ya avisado sigue vigente, porque no se sabe si se ha resuelto. Sin
    CT consultables, transicion conserva reinicios y contenedores conocidos."""
    ...
