#!/usr/bin/env python3
"""Socket Unix de la papelera de Element. Una sola accion: deshacer una
aprobacion AUTOMATICA.

Por que un socket aparte y no una accion mas en demeter-query: aquel es de
solo lectura por construccion (base abierta con mode=ro, PRAGMA query_only y
su propio sandbox), y esa garantia vale mas que ahorrarse un servicio. Aqui
la superficie de escritura es minima y no crece: no aprueba, no edita, no
descarta mensajes por revisar; solo deshace lo que decidio la automatica, y
`Inbox.undo_auto` se niega si la ultima aprobacion la hizo una persona.

Solo lo usa el manejador de reacciones de Hermes, que es codigo sin modelo:
el modelo de lenguaje no tiene ninguna herramienta que llegue hasta aqui.
"""
import json
import os
import socketserver
import traceback

from demeter_review import Inbox
from demeter_store import Store

USUARIOS = ('tito',)
MOTIVO = 'Papelera en Element: la automatica se equivoco'


def deshacer(database, peticion):
    """Valida la peticion y deshace. Separado del socket para poder probarlo."""
    ...


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        ...


class Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True


if __name__ == '__main__':
    path = '/run/demeter-undo/undo.sock'
    if os.path.exists(path):
        os.unlink(path)
    os.umask(0o117)
    with Server(path, Handler) as server:
        server.database = os.environ.get('DEMETER_DB', '/var/lib/demeter/queue.sqlite')
        print('demeter-undo: escuchando', flush=True)
        server.serve_forever()
