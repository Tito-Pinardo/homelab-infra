"""Reglas de extracción para tiendas concretas (se definen en el inventario privado)."""

REGLAS = ()


def extract_tienda(sender, subject, body, received_on):
    """Aplica la primera regla que reconozca el remitente y devuelve la compra."""
