from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_web import create_app
from demeter_store import Store
from demeter_review import Inbox


TOKEN='test-only-proxy-token-'*3
ORIGIN='https://demeter.home.example'
HEADERS={'X-Demeter-Proxy':TOKEN,'Remote-User':'usuario'}


class Entorno:
    """Andamiaje compartido: base de datos temporal con un recibo.

    Es un mixin y no un TestCase a proposito: si las clases de prueba
    heredasen unas de otras, cada una volveria a ejecutar las pruebas de la
    otra sobre datos distintos.
    """

    def setUp(self):
        """Prepara el entorno de cada prueba."""
        ...

    def tearDown(self):
        """Limpia el entorno de cada prueba."""
        ...

    def request(self,path,method='get',headers=None,ip='192.0.2.24',**kwargs):
        """Hace una peticion a la web de prueba."""
        ...

    def csrf(self):
        """Devuelve el token CSRF de la sesion."""
        ...

    def decision(self):
        """Construye una decision de aprobacion a partir del candidato."""
        ...


class WebTests(Entorno, unittest.TestCase):
    def test_anonymous_spoofed_user_and_direct_ip_rejected(self):
        """Prueba: se rechazan anonimos, usuarios suplantados y accesos directos."""
        ...

    def test_security_headers_and_cookie(self):
        """Prueba: cabeceras de seguridad y cookie."""
        ...

    def test_csrf_and_cross_origin_do_not_write(self):
        """Prueba: sin CSRF o desde otro origen no se escribe."""
        ...

    def test_approval_updates_summary_and_duplicate_revision_rejected(self):
        """Prueba: aprobar actualiza el resumen y se rechaza una revision duplicada."""
        ...

    def test_search_and_invalid_input(self):
        """Prueba: busqueda y entradas invalidas."""
        ...

    def test_confirmed_detail_and_list_show_reviewers_correction(self):
        """Prueba: detalle y lista muestran la correccion del revisor."""
        ...

    def test_reprocessing_is_audited_and_not_counted(self):
        """Prueba: reprocesar se audita y no cuenta como gasto."""
        ...


class DescarteEnBloqueTests(Entorno, unittest.TestCase):
    """Descarte por remitente: el atajo no puede tocar nada confirmado ni nada
    de otro remitente.
    """

    RUIDO='noreply@creator.patreon.com'

    def setUp(self):
        """Prepara el entorno de cada prueba."""
        ...

    def descartar(self,**payload):
        """Pide descartar un remitente en bloque."""
        ...

    def estado(self, candidato):
        """Devuelve el estado de un candidato."""
        ...

    def test_remitentes_lista_el_ruido_primero_con_su_cuenta(self):
        """Prueba: remitentes lista el ruido primero con su cuenta."""
        ...

    def test_descarta_solo_ese_remitente_y_lo_deja_en_la_auditoria(self):
        """Prueba: descarta solo ese remitente y lo deja en la auditoria."""
        ...

    def test_no_toca_una_compra_ya_confirmada(self):
        """Prueba: no toca una compra ya confirmada."""
        ...

    def test_el_limite_acota_cuantos_se_tocan(self):
        """Prueba: el limite acota cuantos se tocan."""
        ...

    def test_coincide_por_dominio_ademas_de_por_direccion(self):
        """Prueba: coincide por dominio ademas de por direccion."""
        ...

    def test_rechaza_peticiones_incompletas_o_sin_csrf(self):
        """Prueba: rechaza peticiones incompletas o sin csrf."""
        ...


class AutomaticasWebTests(Entorno, unittest.TestCase):
    """La pagina como si/no sobre lo que aprobo la automatica."""

    def setUp(self):
        """Prepara el entorno de cada prueba."""
        ...

    def accion(self,nombre,headers=None):
        """Ejecuta una accion sobre el candidato de prueba."""
        ...

    def test_lista_y_cuenta_lo_que_espera_tu_visto_bueno(self):
        """Prueba: lista y cuenta lo que espera tu visto bueno."""
        ...

    def test_si_la_confirma_y_sigue_contando(self):
        """Prueba: si la confirma y sigue contando."""
        ...

    def test_no_la_quita_de_los_gastos(self):
        """Prueba: no la quita de los gastos."""
        ...

    def en_bloque(self,items,headers=None):
        """Confirma aprobaciones automaticas en bloque."""
        ...

    def test_confirmar_todas_es_una_sola_peticion_y_no_deja_la_lista_a_medias(self):
        """Prueba: confirmar todas es una sola peticion y no deja la lista a medias."""
        ...

    def test_en_bloque_no_pisa_lo_que_cambio(self):
        """Prueba: en bloque no pisa lo que cambio."""
        ...

    def test_en_bloque_exige_csrf_y_una_lista_valida(self):
        """Prueba: en bloque exige csrf y una lista valida."""
        ...

    def test_sin_csrf_no_se_decide_nada(self):
        """Prueba: sin csrf no se decide nada."""
        ...


if __name__=='__main__':unittest.main()
