"""La papelera de Element y el aviso de compras automaticas (2026-09-23).

Dos piezas que se prueban sin red: la consulta de solo lectura que dice que
anunciar, y la validacion del socket que deshace. Lo importante es lo que NO
pueden hacer: anunciar lo ya deshecho, deshacer lo que aprobo una persona o
aceptar una peticion que no sea exactamente la esperada.
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
        ...

    def tearDown(self):
        ...

    def compra(self, actor, message_id='m1'):
        ...

    def recientes(self, desde=0):
        ...

    def test_anuncia_lo_automatico_con_su_importe_y_no_lo_manual(self):
        ...

    def test_ultimo_permite_empezar_sin_anunciar_el_historico(self):
        ...

    def test_lo_deshecho_ya_no_se_anuncia(self):
        ...

    def test_el_socket_solo_acepta_la_peticion_exacta(self):
        ...

    def test_el_socket_no_deshace_lo_que_aprobo_una_persona(self):
        ...

    def test_una_consulta_con_desde_invalido_se_rechaza(self):
        ...

    # La pagina como "si o no" sobre lo que decidio la automatica.
    def revision(self, candidato):
        ...

    def test_la_lista_de_aprobadas_solas_no_incluye_lo_manual(self):
        ...

    def test_confirmar_la_saca_de_la_lista_sin_tocar_el_gasto(self):
        ...

    def test_decir_que_no_la_quita_de_la_lista_y_de_los_gastos(self):
        ...

    def test_no_se_confirma_como_automatica_lo_que_aprobo_una_persona(self):
        ...

    def test_un_doble_clic_no_pisa_la_primera_decision(self):
        ...


if __name__ == '__main__':
    unittest.main()
