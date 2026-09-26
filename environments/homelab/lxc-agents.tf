# CT de control: agentes de IA para programar con Codeman como panel web.
# Desde aqui gestiono el homelab, por eso:
#   - el panel solo es accesible desde la red local, con doble factor
#   - los agentes corren como un usuario sin privilegios dentro del CT

resource "proxmox_virtual_environment_container" "agents" {
  node_name    = "main"
  vm_id        = 123
  unprivileged = true
  description  = "CT de control con agentes de IA y Codeman. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "agents"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.21/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Espacio para worktrees en paralelo, dependencias y caches.
  disk {
    datastore_id = "local-lvm"
    size         = 40
  }

  cpu { cores = 4 }

  memory {
    dedicated = 8192
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  started = true
}

output "agents_ip" {
  value = "192.0.2.21"
}
