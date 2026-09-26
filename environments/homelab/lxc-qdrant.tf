# CT de Qdrant (base de datos vectorial del asistente). Va aparte del CT del
# asistente porque es el unico componente con estado persistente importante.
#
# Sin Docker: binario oficial de una release fijada con systemd.

resource "proxmox_virtual_environment_container" "qdrant" {
  node_name    = "main"
  vm_id        = 115
  unprivileged = true
  description  = "Qdrant, base de datos vectorial del asistente IA. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "qdrant"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.26/24"
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

  started = true
}

output "qdrant_ip" {
  value = "192.0.2.26"
}
