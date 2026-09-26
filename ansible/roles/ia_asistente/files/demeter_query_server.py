#!/usr/bin/env python3
"""Socket Unix de consultas de Hermes. Sin TCP, sin escrituras ni texto de correo."""
import json
import os
from pathlib import Path
import socketserver
import sqlite3
import traceback

from demeter_queries import query


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        """Atiende una consulta por el socket local."""
        ...


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads=True


if __name__=='__main__':
    path='/run/demeter-query/query.sock'
    if os.path.exists(path):os.unlink(path)
    os.umask(0o117)
    with Server(path,Handler) as server:
        server.database=os.environ.get('DEMETER_DB','/var/lib/demeter/queue.sqlite')
        # Comprobacion al arrancar: si el modulo de consultas no casa con la base,
        # lo registro en el journal. No aborta: el socket sigue respondiendo con un
        # error controlado.
        try:
            db=sqlite3.connect(Path(server.database).resolve().as_uri()+'?mode=ro',uri=True)
            try:query(db,{'action':'summary'})
            finally:db.close()
            print('demeter-query: comprobacion inicial correcta',flush=True)
        except Exception:
            print('demeter-query: LA COMPROBACION INICIAL FALLA, las consultas de Hermes no funcionaran',flush=True)
            traceback.print_exc()
        server.serve_forever()
