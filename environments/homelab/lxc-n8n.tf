# CT de n8n para automatizaciones.

resource "proxmox_virtual_environment_container" "n8n" {
  node_name    = "main"
  vm_id        = 114
  unprivileged = true
  description  = "n8n para automatizaciones. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "n8n"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.30/24"
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

  cpu { cores = 2 }

  memory {
    dedicated = 4096
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  features {
    nesting = true
  }

  started = true
}

output "n8n_ip" {
  value = "192.0.2.30"
}
