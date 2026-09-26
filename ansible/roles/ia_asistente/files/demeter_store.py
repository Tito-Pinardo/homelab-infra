"""Registro local de compras. Importes en unidades mínimas, nunca floats.

Sin correo, red o LLM: este módulo solo recibe registros ya validados.
El directorio de la base debe ser privado y quedar fuera del vault/Git.
"""
import sqlite3
from contextlib import contextmanager
from datetime import date


SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
 id INTEGER PRIMARY KEY,
 account TEXT NOT NULL, merchant TEXT NOT NULL, reference TEXT NOT NULL,
 purchased_on TEXT NOT NULL, currency TEXT NOT NULL,
 total_minor INTEGER NOT NULL CHECK(total_minor >= 0),
 UNIQUE(account, merchant, reference)
);
CREATE TABLE IF NOT EXISTS evidence (
 account TEXT NOT NULL, message_id TEXT NOT NULL,
 order_id INTEGER NOT NULL REFERENCES orders(id),
 kind TEXT NOT NULL CHECK(kind IN ('purchase','shipment','delivery','refund')),
 PRIMARY KEY(account, message_id)
);
CREATE TABLE IF NOT EXISTS refunds (
 order_id INTEGER NOT NULL REFERENCES orders(id),
 reference TEXT NOT NULL, received_on TEXT NOT NULL,
 amount_minor INTEGER NOT NULL CHECK(amount_minor > 0),
 PRIMARY KEY(order_id, reference)
);
"""

# Cada migración se aplica dentro de la misma transacción que user_version.
# La versión 0 también admite la base inicial, todavía sin versionar.
MIGRATIONS = (
    tuple(statement for statement in SCHEMA.split(';') if statement.strip()),
    (
        '''CREATE TABLE candidates (
            id INTEGER PRIMARY KEY, account TEXT NOT NULL, message_id TEXT NOT NULL,
            sender TEXT NOT NULL, subject TEXT NOT NULL, body TEXT NOT NULL,
            received_on TEXT NOT NULL, source_hash TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','review','validated','discarded','error')),
            revision INTEGER NOT NULL DEFAULT 0, attempts INTEGER NOT NULL DEFAULT 0,
            extraction TEXT, extractor_version TEXT, error_code TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            UNIQUE(account,message_id)
        )''',
        '''CREATE TABLE candidate_audit (
            id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
            revision INTEGER NOT NULL, actor TEXT NOT NULL, action TEXT NOT NULL,
            details TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )''',
        '''CREATE TABLE candidate_orders (
            candidate_id INTEGER NOT NULL REFERENCES candidates(id),
            order_id INTEGER NOT NULL REFERENCES orders(id),
            PRIMARY KEY(candidate_id,order_id)
        )''',
        'CREATE INDEX candidates_status ON candidates(status,id)',
    ),
    (
        'ALTER TABLE evidence RENAME TO evidence_single_order',
        '''CREATE TABLE evidence (
            account TEXT NOT NULL, message_id TEXT NOT NULL,
            order_id INTEGER NOT NULL REFERENCES orders(id),
            kind TEXT NOT NULL CHECK(kind IN ('purchase','shipment','delivery','refund')),
            PRIMARY KEY(account,message_id,order_id)
        )''',
        'INSERT INTO evidence SELECT * FROM evidence_single_order',
        'DROP TABLE evidence_single_order',
    ),
    (
        '''CREATE TABLE mail_cursors (
            account TEXT NOT NULL, mailbox TEXT NOT NULL, query_hash TEXT NOT NULL,
            uidvalidity TEXT NOT NULL, last_uid INTEGER NOT NULL DEFAULT 0,
            since_date TEXT NOT NULL,
            PRIMARY KEY(account,mailbox,query_hash)
        )''',
        '''CREATE TABLE mail_captures (
            id INTEGER PRIMARY KEY, account TEXT NOT NULL, mailbox TEXT NOT NULL,
            uidvalidity TEXT NOT NULL, uid INTEGER NOT NULL,
            candidate_id INTEGER REFERENCES candidates(id),
            gmail_id TEXT, raw BLOB, raw_hash TEXT, size INTEGER NOT NULL,
            status TEXT NOT NULL CHECK(status IN ('captured','quarantine')),
            error_code TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            UNIQUE(account,mailbox,uidvalidity,uid)
        )''',
    ),
    (
        '''CREATE TABLE candidate_documents (
            id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
            digest TEXT NOT NULL, filename TEXT NOT NULL, text TEXT NOT NULL,
            error_code TEXT, UNIQUE(candidate_id,digest)
        )''',
    ),
    (
        """CREATE TABLE order_details (
            order_id INTEGER PRIMARY KEY REFERENCES orders(id),
            description TEXT NOT NULL DEFAULT '', category TEXT NOT NULL DEFAULT 'Otros',
            origin TEXT NOT NULL DEFAULT 'manual',
            delivery_override TEXT, revision INTEGER NOT NULL DEFAULT 0
        )""",
        """CREATE TABLE order_events (
            id INTEGER PRIMARY KEY, candidate_id INTEGER NOT NULL REFERENCES candidates(id),
            account TEXT NOT NULL, merchant TEXT NOT NULL, reference TEXT NOT NULL,
            kind TEXT NOT NULL, observed_on TEXT NOT NULL, expected_on TEXT,
            description TEXT NOT NULL DEFAULT '', evidence TEXT NOT NULL,
            UNIQUE(candidate_id,reference)
        )""",
        """CREATE TABLE imported_messages (
            candidate_id INTEGER PRIMARY KEY REFERENCES candidates(id), raw BLOB NOT NULL, digest TEXT NOT NULL
        )""",
        'CREATE INDEX events_reference ON order_events(account,merchant,reference,observed_on)',
        """CREATE TABLE order_changes (
            id INTEGER PRIMARY KEY, order_id INTEGER NOT NULL REFERENCES orders(id),
            actor TEXT NOT NULL, details TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )""",
        """CREATE TABLE capture_runs (
            id INTEGER PRIMARY KEY, success INTEGER NOT NULL, remaining INTEGER NOT NULL,
            completed_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )""",
    ),
)


def required(*values):
    """Valida que los identificadores no esten vacios."""
    ...


def amount(value, minimum=0):
    """Valida un importe entero en unidades minimas."""
    ...


def day(value):
    """Valida una fecha en formato YYYY-MM-DD."""
    ...


class Store:
    def __init__(self, path):
        """Abre la base de datos y aplica las migraciones pendientes."""
        ...

    def close(self):
        """Cierra la base de datos."""
        ...

    @contextmanager
    def transaction(self):
        """Contexto de transaccion, admite anidamiento."""
        ...

    def _evidence(self, account, message_id, order_id, kind, allow_multiple=False):
        """Registra un correo como evidencia de un pedido."""
        ...

    def purchase(self, *, account, merchant, reference, purchased_on,
                 currency, total_minor, message_id, allow_multiple=False):
        """Registra una compra."""
        ...

    def delivery_evidence(self, *, account, message_id, order_id, kind):
        """Registra una evidencia de envio o entrega de un pedido."""
        ...

    def refund(self, *, account, message_id, order_id, reference, received_on, amount_minor):
        """Registra una devolucion."""
        ...

    def summary(self, start, end):
        """Devuelve el gasto de un periodo: compras menos devoluciones."""
        ...
