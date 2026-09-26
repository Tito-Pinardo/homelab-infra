"""Docker en los CT: caidos, imagenes nuevas y cuando avisar en Hipnos.

Sin red: `docker_estado.py` es logica pura sobre el snapshot.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
import docker_estado  # noqa: E402


def contenedor(nombre, estado='running', proyecto='arr', **extra):
    """Construye un contenedor de prueba."""
    ...


def ct(nombre, *contenedores, estado_ct='running', **extra):
    """Construye un CT de prueba con sus contenedores."""
    ...


class CaidosTests(unittest.TestCase):
    def test_todo_en_marcha(self):
        """Prueba: todo en marcha."""
        ...

    def test_parado_con_error(self):
        """Prueba: parado con error."""
        ...

    def test_unhealthy_y_bucle_de_reinicios(self):
        """Prueba: unhealthy y bucle de reinicios."""
        ...

    def test_un_solo_uso_que_acabo_bien_no_es_fallo(self):
        """Prueba: un solo uso que acabo bien no es fallo."""
        ...

    def test_amp_se_ignora(self):
        """Prueba: amp se ignora."""
        ...

    def test_ct_parado_o_sin_consultar(self):
        """Prueba: ct parado o sin consultar."""
        ...


class ActualizacionesTests(unittest.TestCase):
    DOCKER = [
        ct('dockge', contenedor('radarr', actualizacion=True), contenedor('caddy', actualizacion=True),
           contenedor('seerr'), contenedor('bazarr', actualizacion=None, error_remoto='429')),
        ct('n8n', contenedor('app-local', actualizacion=None)),
        ct('amp', contenedor('AMP_Servidor01', proyecto=None, actualizacion=True)),
    ]

    def test_agrupa_por_ct_sin_amp(self):
        """Prueba: agrupa por ct sin amp."""
        ...

    def test_hefesto_da_el_comando(self):
        """Prueba: hefesto da el comando."""
        ...

    def test_pitia_resume(self):
        """Prueba: pitia resume."""
        ...

    def test_pitia_vacio_si_todo_bien(self):
        """Prueba: pitia vacio si todo bien."""
        ...


class TransicionTests(unittest.TestCase):
    def pasar(self, estado, *docker):
        """Ejecuta una pasada de la vigilancia de Docker."""
        ...

    def test_avisa_tras_dos_pasadas_y_una_sola_vez(self):
        """Prueba: avisa tras dos pasadas y una sola vez."""
        ...

    def test_un_parpadeo_no_avisa(self):
        """Prueba: un parpadeo no avisa."""
        ...

    def test_reinicio_solo(self):
        """Prueba: reinicio solo."""
        ...

    def test_desaparecido_se_avisa_una_vez_y_se_olvida(self):
        """Prueba: desaparecido se avisa una vez y se olvida."""
        ...

    def test_ct_caido_avisa_del_ct_y_no_de_cada_contenedor(self):
        """Prueba: ct caido avisa del ct y no de cada contenedor."""
        ...

    def test_otros_problemas(self):
        """Prueba: otros problemas."""
        ...

    def test_sin_datos_no_da_nada_por_resuelto(self):
        """Prueba: sin datos no da nada por resuelto."""
        ...


if __name__ == '__main__':
    unittest.main()
