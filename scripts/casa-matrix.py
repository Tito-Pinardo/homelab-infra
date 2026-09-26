#!/usr/bin/python3
# Script de Zabbix para enviar incidencias criticas a Element cifradas. No
# habla con Matrix directamente: le pasa el mensaje al relay (matrix_relay.py).
import json, sys, urllib.request, urllib.error, pathlib, time


def send(subject: str, message: str) -> None:
    """Envia una alerta de Zabbix a la sala de Matrix a traves del relay."""
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
