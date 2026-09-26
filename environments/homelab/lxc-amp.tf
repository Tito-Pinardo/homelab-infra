# CT de AMP (CubeCoders Application Management Panel), que gestiona los
# servidores de juego con Docker.

resource "proxmox_virtual_environment_container" "amp" {
  node_name    = "main"
  vm_id        = 121
  unprivileged = true
  description  = "AMP, panel de servidores de juego. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "amp"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.17/24"
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
    size         = 80
  }

  cpu { cores = 12 }

  memory {
    dedicated = 24576
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # Los mount points de tipo bind solo los puede crear root@pam por la API; el
  # token del provider recibe un 403. Los aplico a mano con 'pct set' tras
  # crear el CT y los ignoro aqui para que Terraform no intente corregirlos
  # destruyendo el CT.
  lifecycle {
    ignore_changes = [mount_point]
  }

  features {
    nesting = true
  }

  started = true
}

output "amp_ip" {
  value = "192.0.2.17"
}
