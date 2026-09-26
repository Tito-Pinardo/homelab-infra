# CT de Technitium, el DNS de la LAN.

resource "proxmox_virtual_environment_container" "technitium" {
  node_name    = "main"
  vm_id        = 120
  unprivileged = true
  description  = "DNS de la LAN (Technitium). Gestionado por Terraform + Ansible."

  initialization {
    hostname = "technitium"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.15/24"
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

  cpu { cores = 2 }

  memory {
    dedicated = 1024
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  started = true
}

output "technitium_ip" {
  value = "192.0.2.15"
}
