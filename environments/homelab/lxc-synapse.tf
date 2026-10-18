# lxc-synapse.tf: CT dedicado al homeserver Matrix (Synapse + PostgreSQL
# locales, sin Docker - mismo criterio que Traefik/Element). Separado del CT
# de Element aposta: Synapse tiene estado (base de datos, media) y consume
# bastante mas que un sitio estatico - mezclarlos ensuciaria backups/recursos
# de un CT que hoy es minimo. Ver conversacion en el runbook de Obsidian.

resource "proxmox_virtual_environment_container" "synapse" {
  node_name    = "main"
  vm_id        = 111
  unprivileged = true
  description  = "Homeserver Matrix (Synapse + PostgreSQL) - privado, sin federacion. Backend de Element (CT 110). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "synapse"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.254/24"
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
    size         = 20
  }

  cpu { cores = 4 }

  memory {
    dedicated = 4096
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

output "synapse_ip" {
  value = "192.0.2.254"
}
