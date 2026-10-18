#!/usr/bin/python3
# Media type "Script" de Zabbix para enviar incidencias criticas a Element
# (Matrix), CIFRADAS de verdad (E2EE). No habla con Matrix directamente -
# el cifrado real lo hace el demonio matrix-relay (CT Synapse, 192.0.2.254
# puerto 8009 solo-loopback-de-esa-red-interna) que mantiene el dispositivo
# y las sesiones Megolm vivas. Este script solo le pasa el mensaje.
import json, sys, urllib.request, urllib.error, pathlib, time


def send(subject: str, message: str) -> None:
    ...


if __name__ == "__main__":
    try:
        value, severity, subject, message = sys.argv[1:]
        if value == "0":
            subject = "[RESUELTO] " + subject
        send(subject, message)
    except Exception as e:
        print(str(e) if isinstance(e, RuntimeError) else "Invalid notification parameters", file=sys.stderr)
        sys.exit(1)
