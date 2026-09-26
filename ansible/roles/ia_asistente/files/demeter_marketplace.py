"""Extracción de pedidos de tiendas online (dominios y formato en el inventario privado)."""

DOMAINS = ()  # se definen en el inventario privado


def extract_marketplace(sender, subject, body):
    """Extrae referencia, fecha e importe de la confirmación de un pedido."""
