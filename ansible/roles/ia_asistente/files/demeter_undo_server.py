#!/usr/bin/env python3
"""Socket Unix de la papelera de Element. Una sola accion: deshacer una
aprobacion automatica.

Va aparte del socket de consultas para que aquel siga siendo de solo
lectura. Aqui solo se deshace lo que decidio la automatica;
Inbox.undo_auto se niega si la ultima aprobacion la hizo una persona.
"""
import json
import os
import socketserver
import traceback

from demeter_review import Inbox
from demeter_store import Store

USUARIOS = ('usuario',)
MOTIVO = 'Papelera en Element: la automatica se equivoco'


def deshacer(database, peticion):
    """Valida una peticion de deshacer y la aplica."""
    ...


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        """Atiende una peticion de deshacer por el socket local."""
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
