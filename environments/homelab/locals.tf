# locals.tf: claves SSH inyectadas en todos los CT nuevos via cloud-init.
# Dos equipos autorizados a gestionar el homelab: este PC (lucifer) y el Mac
# (siempre entra por el WireGuard del MikroTik, el WiFi de casa esta
# aislado). Anadir un tercero algun dia = una linea mas aqui, no tocar cada
# lxc-*.tf por separado.
locals {
  admin_ssh_keys = [
    # lucifer (PC). Literal, no file("~/.ssh/id_rsa.pub"): ese file() leia la
    # clave del equipo DONDE se ejecuta terraform - desde el CT 123 (agents)
    # fallaba, y con otra clave cambiaria el valor (ForceNew = recrear todos
    # los CT). Mismo valor exacto que ya estaba en el state (2026-09-22).
    "ssh-rsa AAAA...clave-publica usuario@equipo",
    "ssh-rsa AAAA...clave-publica usuario@equipo",
  ]
}
