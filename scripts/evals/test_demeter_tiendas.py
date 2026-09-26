"""Reglas por comercio con el formato real de cada correo.

Los cuerpos reproducen la maquetacion tal como llega (etiqueta en una
linea, cifra en la siguiente, senuelos incluidos). Los datos personales
estan sustituidos.
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
ABC12345
15 SEP 2026 - 18 SEP 2026
5,00 EUR
00000-0000-00000-00000-00000-00000-00000
No hace falta que compruebes tu apuesta.
"""

PREMIO = """Hola Fulano! ¡Has conseguido un premio de 3,45€ en tu apuesta ! Ya
está disponible en tu saldo.
"""

ALIEXPRESS = """Actualización del pedido
Tu pedido 1000000000000001 se marcará como completado pronto.
Protector de pantalla para móvil
no frame black
x1
Total del pedido
13,84€
Ver detalles
"""

ALIEXPRESS_ENTREGA = """Package 100000000000000002 has been delivered
Gracias por comprar en AliExpress.
"""

# El correo real separa cada etiqueta de su cifra con dos lineas en blanco.
POE_PEDIDO = """THANK YOU FOR YOUR ORDER!
We have received your order.
Order No:


POE1000000000000X
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
    """Extrae una compra y su primer articulo de un correo de prueba."""
    ...


class LoteriasTests(unittest.TestCase):
    REMITENTE = 'Loterias del Estado <envios@loteriasyapuestas.es>'

    def test_el_resguardo_da_importe_referencia_y_fecha_del_correo(self):
        """Prueba: el resguardo da importe referencia y fecha del correo."""
        ...

    def test_no_confunde_el_saldo_con_el_importe_de_la_apuesta(self):
        """Prueba: no confunde el saldo con el importe de la apuesta."""
        ...

    def test_sin_fecha_del_correo_lo_dice_en_vez_de_inventarla(self):
        """Prueba: sin fecha del correo lo dice en vez de inventarla."""
        ...

    def test_un_premio_no_es_un_gasto_ni_un_reembolso(self):
        """Prueba: un premio no es un gasto ni un reembolso."""
        ...


class AliExpressTests(unittest.TestCase):
    REMITENTE = 'AliExpress <transaction@notice.aliexpress.com>'

    def test_saca_el_total_de_la_linea_siguiente_y_el_pedido_del_asunto(self):
        """Prueba: saca el total de la linea siguiente y el pedido del asunto."""
        ...

    def test_deja_la_fecha_en_blanco_porque_el_aviso_llega_despues(self):
        """Prueba: deja la fecha en blanco porque el aviso llega despues."""
        ...

    def test_los_avisos_de_seguimiento_son_envio_y_no_compras_vacias(self):
        """Prueba: los avisos de seguimiento son envio y no compras vacias."""
        ...

    def test_un_aviso_de_entrega_no_se_cuenta_como_compra(self):
        """Prueba: un aviso de entrega no se cuenta como compra."""
        ...


class PoecurrencyTests(unittest.TestCase):
    REMITENTE = 'Support POECURRENCY <support@poecurrency.com>'

    def test_cobra_el_subtotal_porque_es_el_cargo_final(self):
        """Prueba: cobra el subtotal porque es el cargo final."""
        ...

    def test_si_la_cuenta_no_cuadra_lo_marca_en_vez_de_elegir(self):
        """Prueba: si la cuenta no cuadra lo marca en vez de elegir."""
        ...

    def test_el_aviso_de_entrega_no_repite_el_importe_y_no_es_compra(self):
        """Prueba: el aviso de entrega no repite el importe y no es compra."""
        ...


class EvidenciaLiteralTests(unittest.TestCase):
    """La aprobacion exige que cada evidencia aparezca literal en el correo.
    Comprueba que las citas de fecha e importe de cada regla existen tal cual
    en el cuerpo.
    """

    CASOS = [
        ('Loterias del Estado <envios@loteriasyapuestas.es>', 'Tu resguardo virtual', RESGUARDO, '2026-09-15'),
        ('Loterias del Estado <envios@loteriasyapuestas.es>', 'Tu resguardo virtual',
         RESGUARDO.replace('\n', '\r\n'), '2026-09-15'),
        ('Support POECURRENCY <support@poecurrency.com>', 'POE - POE1000000000000X', POE_PEDIDO, None),
    ]

    def test_cada_cita_de_una_compra_completa_esta_en_el_correo(self):
        """Prueba: cada cita de una compra completa esta en el correo."""
        ...

    def test_las_compras_que_se_pueden_aprobar_solas_constan_como_pagadas(self):
        """Prueba: las compras que se pueden aprobar solas constan como pagadas."""
        ...

    def test_una_fecha_de_correo_posterior_al_sorteo_no_se_da_por_buena(self):
        """Prueba: una fecha de correo posterior al sorteo no se da por buena."""
        ...


class SaltosDeLineaTests(unittest.TestCase):
    """Los correos reales llegan con CRLF; el \\r sobrante rompía la lectura."""

    def test_un_cuerpo_con_crlf_se_lee_igual(self):
        """Prueba: un cuerpo con crlf se lee igual."""
        ...

    def test_miles_de_lineas_en_blanco_no_atascan_el_extractor(self):
        """Prueba: miles de lineas en blanco no atascan el extractor."""
        ...


class AjenosTests(unittest.TestCase):
    def test_un_remitente_que_no_toca_se_deja_para_las_demas_reglas(self):
        """Prueba: un remitente que no toca se deja para las demas reglas."""
        ...


if __name__ == '__main__':
    unittest.main()
