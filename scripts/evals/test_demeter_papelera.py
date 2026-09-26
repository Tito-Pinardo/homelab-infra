"""La papelera de Element y el aviso de compras automaticas.

Pruebo sin red la consulta de solo lectura que decide que anunciar y la
validacion del socket que deshace. Lo importante es lo que no pueden hacer:
anunciar lo ya deshecho, deshacer lo que aprobo una persona o aceptar una
peticion distinta de la esperada.
"""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from demeter_queries import query
from demeter_review import Inbox, StaleRevision
from demeter_store import Store
from demeter_undo_server import deshacer
from test_demeter_review import BODY, EVIDENCE, PURCHASE


class PapeleraTests(unittest.TestCase):
    def setUp(self):
        """Prepara el entorno de cada prueba."""
        ...

    def tearDown(self):
        """Limpia el entorno de cada prueba."""
        ...

    def compra(self, actor, message_id='m1'):
        """Crea una compra de prueba aprobada automaticamente."""
        ...

    def recientes(self, desde=0):
        """Consulta las aprobaciones automaticas recientes."""
        ...

    def test_anuncia_lo_automatico_con_su_importe_y_no_lo_manual(self):
        """Prueba: anuncia lo automatico con su importe y no lo manual."""
        ...

    def test_ultimo_permite_empezar_sin_anunciar_el_historico(self):
        """Prueba: ultimo permite empezar sin anunciar el historico."""
        ...

    def test_lo_deshecho_ya_no_se_anuncia(self):
        """Prueba: lo deshecho ya no se anuncia."""
        ...

    def test_el_socket_solo_acepta_la_peticion_exacta(self):
        """Prueba: el socket solo acepta la peticion exacta."""
        ...

    def test_el_socket_no_deshace_lo_que_aprobo_una_persona(self):
        """Prueba: el socket no deshace lo que aprobo una persona."""
        ...

    def test_una_consulta_con_desde_invalido_se_rechaza(self):
        """Prueba: una consulta con desde invalido se rechaza."""
        ...

    # La pagina como "si o no" sobre lo que decidio la automatica.
    def revision(self, candidato):
        """Devuelve la revision actual de un candidato."""
        ...

    def test_la_lista_de_aprobadas_solas_no_incluye_lo_manual(self):
        """Prueba: la lista de aprobadas solas no incluye lo manual."""
        ...

    def test_confirmar_la_saca_de_la_lista_sin_tocar_el_gasto(self):
        """Prueba: confirmar la saca de la lista sin tocar el gasto."""
        ...

    def test_decir_que_no_la_quita_de_la_lista_y_de_los_gastos(self):
        """Prueba: decir que no la quita de la lista y de los gastos."""
        ...

    def test_no_se_confirma_como_automatica_lo_que_aprobo_una_persona(self):
        """Prueba: no se confirma como automatica lo que aprobo una persona."""
        ...

    def test_un_doble_clic_no_pisa_la_primera_decision(self):
        """Prueba: un doble clic no pisa la primera decision."""
        ...


if __name__ == '__main__':
    unittest.main()
