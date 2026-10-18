# lxc-element.tf: define el CT que alojará Element Web (solo el cliente
# estático de Matrix, sin homeserver propio). Recursos ajustados al mínimo
# real: nginx sirviendo ~140 MB de HTML/JS estático no necesita ni CPU ni
# RAM comparables a Traefik o al clúster OKD.

resource "proxmox_virtual_environment_container" "element" {
  node_name    = "main"
  vm_id        = 110
  unprivileged = true

  initialization {
    hostname = "element"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.253/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 6
  }

  cpu { cores = 1 }

  memory {
    dedicated = 512
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # user_account.keys es ForceNew - este CT se creo antes de anadir la
  # segunda clave SSH (Mac) a locals.tf. Ambas claves ya estan en
  # authorized_keys a mano (mismo patron que el resto de CT viejos, ver
  # providers.tf/locals.tf) - sin esto, cualquier 'terraform apply' intenta
  # "corregir" el desajuste destruyendo y recreando el CT entero.
  # Descubierto 2026-09-19 revisando un 'terraform plan' que iba a borrar
  # 4 CT en produccion.
  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, initialization[0].user_account]
  }

  started = true
}

output "element_ip" {
  value = "192.0.2.253"
}
