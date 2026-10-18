"""Docker en los CT: caidos, imagenes nuevas y cuando avisar en Hipnos.

Sin red: `docker_estado.py` es logica pura sobre el snapshot.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
import docker_estado  # noqa: E402


def contenedor(nombre, estado='running', proyecto='arr', **extra):
    ...


def ct(nombre, *contenedores, estado_ct='running', **extra):
    ...


class CaidosTests(unittest.TestCase):
    def test_todo_en_marcha(self):
        ...

    def test_parado_con_error(self):
        ...

    def test_unhealthy_y_bucle_de_reinicios(self):
        ...

    def test_un_solo_uso_que_acabo_bien_no_es_fallo(self):
        ...

    def test_amp_se_ignora(self):
        ...

    def test_ct_parado_o_sin_consultar(self):
        ...


class ActualizacionesTests(unittest.TestCase):
    DOCKER = [
        ct('dockge', contenedor('radarr', actualizacion=True), contenedor('caddy', actualizacion=True),
           contenedor('seerr'), contenedor('bazarr', actualizacion=None, error_remoto='429')),
        ct('n8n', contenedor('puppeteer-api', actualizacion=None)),
        ct('amp', contenedor('AMP_David01', proyecto=None, actualizacion=True)),
    ]

    def test_agrupa_por_ct_sin_amp(self):
        ...

    def test_hefesto_da_el_comando(self):
        ...

    def test_pitia_resume(self):
        ...

    def test_pitia_vacio_si_todo_bien(self):
        ...


class TransicionTests(unittest.TestCase):
    def pasar(self, estado, *docker):
        ...

    def test_avisa_tras_dos_pasadas_y_una_sola_vez(self):
        ...

    def test_un_parpadeo_no_avisa(self):
        ...

    def test_reinicio_solo(self):
        ...

    def test_desaparecido_se_avisa_una_vez_y_se_olvida(self):
        ...

    def test_ct_caido_avisa_del_ct_y_no_de_cada_contenedor(self):
        ...

    def test_otros_problemas(self):
        ...

    def test_sin_datos_no_da_nada_por_resuelto(self):
        ...


if __name__ == '__main__':
    unittest.main()
