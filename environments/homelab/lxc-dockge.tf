# CT dockge: Tautulli, Seerr, battlepros-status, Obsidian y el stack de
# Caddy + Authelia + arr.

resource "proxmox_virtual_environment_container" "dockge" {
  node_name    = "main"
  vm_id        = 122
  unprivileged = true
  description  = "Stack multimedia (Caddy, Authelia, arr, Tautulli, Seerr, Obsidian). Gestionado por Terraform + Ansible."

  initialization {
    hostname = "dockge"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.24/24"
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
    size         = 150
  }

  cpu { cores = 8 }

  memory {
    dedicated = 24576
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # Los mount points de tipo bind y el passthrough de /dev/net/tun (para
  # WireGuard dentro de Docker) requieren root@pam. Los aplico a mano con
  # 'pct set' tras crear el CT y los ignoro aqui.
  lifecycle {
    ignore_changes = [mount_point, device_passthrough]
  }

  features {
    nesting = true
  }

  started = true
}

output "dockge_ip" {
  value = "192.0.2.24"
}
