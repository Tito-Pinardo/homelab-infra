"""Reglas por comercio, con el formato REAL de cada correo.

Los cuerpos reproducen la maquetación tal y como llega (etiqueta en una
línea, cifra en la siguiente, señuelos incluidos), porque ahí es donde
fallaban: el 2026-09-23 ninguno de los 431 mensajes atascados tenía los
datos completos. Los datos personales están sustituidos.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'))
from demeter_tiendas import extract_tienda

RESGUARDO = """© Sociedad Estatal Loterías y Apuestas del Estado, S.M.E, S.A.
Hola Fulano, tu saldo actual es: 0,00€
1 apuesta(s)
02
04
46
15 SEP 26 - 18 SEP 26
FZM80984
15 SEP 2026 - 18 SEP 2026
5,00 EUR
13223-0702-13439-50364-66644-96870-17538
No hace falta que compruebes tu apuesta.
"""

PREMIO = """Hola Fulano! ¡Has conseguido un premio de 3,45€ en tu apuesta ! Ya
está disponible en tu saldo.
"""

ALIEXPRESS = """Actualización del pedido
Tu pedido 3075898032385620 se marcará como completado pronto.
Protector de pantalla para móvil
no frame black
x1
Total del pedido
13,84€
Ver detalles
"""

ALIEXPRESS_ENTREGA = """Package 800000000000000001 has been delivered
Gracias por comprar en AliExpress.
"""

# El correo real separa cada etiqueta de su cifra con dos lineas en blanco.
POE_PEDIDO = """THANK YOU FOR YOUR ORDER!
We have received your order.
Order No:


POE1781538162425S
Date:2026-06-15 07:42
Path Of Exile 2 Divine Orb(100+5 Free)
QTY:1.0
€9.50
Character Name:
Fulano
Total:


€9.50
Payment Fee:


€0.53
Discount:


€0.95
Subtotal:


€9.08
"""

POE_ENTREGA = """Hello,
We have fulfilled your order, please check it in the game!
Please contact us by email or Live Chat within 3 days.
"""


def pieza(sender, subject, body, received_on=None):
    ...


class LoteriasTests(unittest.TestCase):
    REMITENTE = 'Loterias del Estado <envios@loteriasyapuestas.es>'

    def test_el_resguardo_da_importe_referencia_y_fecha_del_correo(self):
        ...

    def test_no_confunde_el_saldo_con_el_importe_de_la_apuesta(self):
        ...

    def test_sin_fecha_del_correo_lo_dice_en_vez_de_inventarla(self):
        ...

    def test_un_premio_no_es_un_gasto_ni_un_reembolso(self):
        ...


class AliExpressTests(unittest.TestCase):
    REMITENTE = 'AliExpress <transaction@notice.aliexpress.com>'

    def test_saca_el_total_de_la_linea_siguiente_y_el_pedido_del_asunto(self):
        ...

    def test_deja_la_fecha_en_blanco_porque_el_aviso_llega_despues(self):
        ...

    def test_los_avisos_de_seguimiento_son_envio_y_no_compras_vacias(self):
        ...

    def test_un_aviso_de_entrega_no_se_cuenta_como_compra(self):
        ...


class PoecurrencyTests(unittest.TestCase):
    REMITENTE = 'Support POECURRENCY <support@poecurrency.com>'

    def test_cobra_el_subtotal_porque_es_el_cargo_final(self):
        ...

    def test_si_la_cuenta_no_cuadra_lo_marca_en_vez_de_elegir(self):
        ...

    def test_el_aviso_de_entrega_no_repite_el_importe_y_no_es_compra(self):
        ...


class EvidenciaLiteralTests(unittest.TestCase):
    """La aprobacion exige que cada evidencia aparezca LITERAL en el correo.

    El 2026-09-23 las reglas pasaban sus pruebas pero ninguna compra se
    habria aprobado sola: la fecha de Loterias citaba un texto inventado
    ("Fecha del correo del resguardo") y el importe de poecurrency era una
    cita compuesta y con los saltos de linea aplanados. Esta prueba es la
    que lo habria detectado: comprueba el mismo invariante que la aprobacion.
    """

    CASOS = [
        ('Loterias del Estado <envios@loteriasyapuestas.es>', 'Tu resguardo virtual', RESGUARDO, '2026-09-15'),
        ('Loterias del Estado <envios@loteriasyapuestas.es>', 'Tu resguardo virtual',
         RESGUARDO.replace('\n', '\r\n'), '2026-09-15'),
        ('Support POECURRENCY <support@poecurrency.com>', 'POE - POE1781538162425S', POE_PEDIDO, None),
    ]

    def test_cada_cita_de_una_compra_completa_esta_en_el_correo(self):
        ...

    def test_las_compras_que_se_pueden_aprobar_solas_constan_como_pagadas(self):
        ...

    def test_una_fecha_de_correo_posterior_al_sorteo_no_se_da_por_buena(self):
        ...


class SaltosDeLineaTests(unittest.TestCase):
    """Los correos reales llegan con CRLF; el \\r sobrante rompía la lectura."""

    def test_un_cuerpo_con_crlf_se_lee_igual(self):
        ...

    def test_miles_de_lineas_en_blanco_no_atascan_el_extractor(self):
        ...


class AjenosTests(unittest.TestCase):
    def test_un_remitente_que_no_toca_se_deja_para_las_demas_reglas(self):
        ...


if __name__ == '__main__':
    unittest.main()
