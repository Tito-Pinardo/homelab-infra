# CT de Paperless-ngx: documentos personales.
#
# A diferencia del resto de CT, no tiene acceso SSH: se administra desde el
# host Proxmox.

resource "proxmox_virtual_environment_container" "paperless" {
  node_name    = "main"
  vm_id        = 119
  unprivileged = true
  description  = "Paperless-ngx (documentos personales). Gestionado por Terraform + Ansible."

  initialization {
    hostname = "paperless"

    # Sin bloque user_account: sin claves SSH.

    ip_config {
      ipv4 {
        address = "192.0.2.25/24"
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

  features {
    nesting = true
  }

  started = true
}

output "paperless_ip" {
  value = "192.0.2.25"
}
