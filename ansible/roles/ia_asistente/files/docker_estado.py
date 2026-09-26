"""Estado de Docker de los CT a partir de la instantanea de monitorizacion.

Logica pura, sin red ni Matrix, para poder probarla. La usan el resumen
diario, Hefesto (imagenes nuevas) e Hipnos (avisos al momento).

Solo cuentan los contenedores de docker compose.
"""

# Pasadas seguidas que tiene que durar un problema antes de avisar, para que
# recrear un contenedor no genere avisos.
CONFIRMACIONES = 2

COMANDO_ACTUALIZAR = "ansible-playbook playbooks/update-containers.yml --limit {ct}"


def _de_compose(c: dict) -> bool:
    """Indica si un contenedor pertenece a un proyecto de Compose."""
    ...


def _consultables(docker: list[dict]):
    """Devuelve los CT en marcha cuya consulta de Docker funciono."""
    ...


def caidos(docker: list[dict]) -> dict[str, str]:
    """Devuelve los problemas actuales de los contenedores."""
    ...


def con_actualizacion(docker: list[dict]) -> list[dict]:
    """Devuelve, por CT, los contenedores con una version nueva disponible."""
    ...


def sin_comprobar(docker: list[dict]) -> list[str]:
    """Devuelve los contenedores cuya version no se pudo comprobar."""
    ...


def lineas_hefesto(docker: list[dict]) -> list[str]:
    """Redacta las lineas de aviso de actualizaciones de contenedores."""
    ...


def lineas_pitia(docker: list[dict]) -> list[str]:
    """Redacta el resumen breve de Docker para el aviso diario."""
    ...


def _reinicios(docker: list[dict]) -> dict[str, int]:
    """Devuelve el numero de reinicios de cada contenedor."""
    ...


def transicion(estado: dict, docker: list[dict], otros: dict[str, str] | None = None) -> tuple[dict, list[str]]:
    """Decide que avisar comparando con la pasada anterior."""
    ...


def transicion_sin_datos(estado: dict, motivo: str) -> tuple[dict, list[str]]:
    """Decide que avisar cuando no hay datos recientes."""
    ...
