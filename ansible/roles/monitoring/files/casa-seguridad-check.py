#!/usr/bin/python3
# Comprobaciones de seguridad locales que consulta el agente de monitorizacion.
import pathlib,subprocess,stat,sys,xml.etree.ElementTree as E
def text(p):
    """Lee un fichero como texto."""
    ...
def secure(p,mask):
    """Comprueba propietario y permisos de un fichero."""
    ...
def ssh():
    """Devuelve la configuracion efectiva de SSH."""
    ...
def xml():
    """Devuelve la configuracion del agente de seguridad."""
    ...
def auth():
    """Comprueba la configuracion de autenticacion de SSH."""
    ...
def limits():
    """Comprueba los limites de intentos de SSH."""
    ...
def macs():
    """Comprueba los algoritmos MAC de SSH."""
    ...
def remote_commands():
    """Comprueba que los comandos remotos del agente estan desactivados."""
    ...
# Comprobaciones disponibles (se pasa el nombre como argumento):
#   shadowed, empty_passwords, uid0, gid0  - cuentas y contrasenas del sistema
#   shadow_permissions, ssh_permissions, cron_permissions - permisos de ficheros sensibles
#   pam_nullok                              - PAM no admite contrasenas vacias
#   ssh_auth, ssh_limits, ssh_macs          - configuracion de SSH
#   active_response, remote_commands, fim   - configuracion del agente de seguridad
# Imprime PASS o FAIL, o ERROR si no se pudo verificar.
checks = {}


def main():
    """Ejecuta la comprobacion pedida e imprime su resultado."""
    ...


main()
