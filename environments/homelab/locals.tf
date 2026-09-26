# Claves SSH que se inyectan en todos los CT nuevos via cloud-init. Anadir
# un equipo nuevo es una linea mas aqui.
locals {
  admin_ssh_keys = [
    # Clave literal y no file(): file() leeria la clave del equipo donde se
    # ejecuta Terraform, y un valor distinto recrearia todos los CT.
    "ssh-rsa AAAA_CLAVE_PUBLICA_DE_EJEMPLO usuario@equipo",
    "ssh-rsa AAAA_CLAVE_PUBLICA_DE_EJEMPLO usuario@equipo",
  ]
}
