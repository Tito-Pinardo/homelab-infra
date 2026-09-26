"""Amazon: extrae evidencia explícita; no visita enlaces ni infiere cobros."""
import re
from email.utils import parseaddr
from demeter_invoices import invoice_date, invoice_money, MONEY_TOKEN

DOMAINS = ('amazon.es', 'amazon.com', 'amazon.co.uk', 'amazon.de', 'amazon.fr', 'amazon.it')
REFERENCE = re.compile(r'(?<!\d)\d{3}-\d{7}-\d{7}(?!\d)')
MONTHS = dict(zip(('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre'),range(1,13)))
DATE_TEXT = r'(?:\d{4}-\d{2}-\d{2}|\d{2}/\d{2}/\d{4}|\d{1,2} de [a-z]+ de \d{4})'


def amazon_date(text):
    """Interpreta una fecha de un correo de Amazon."""
    ...


def extract_amazon(sender, subject, body):
    """Extrae los datos de pedido de un correo de Amazon."""
    ...
