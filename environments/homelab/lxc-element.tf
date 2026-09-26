# CT de Element Web: solo el cliente estatico de Matrix, servido con nginx.
# Recursos minimos.

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
        address = "192.0.2.31/24"
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

  # Las claves SSH de este CT las gestiono fuera de Terraform: user_account.keys
  # es ForceNew y cualquier diferencia recrearia el CT entero.
  lifecycle {
    ignore_changes = [initialization[0].user_account]
  }

  started = true
}

output "element_ip" {
  value = "192.0.2.31"
}
