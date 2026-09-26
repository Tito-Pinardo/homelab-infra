# CT dns-sync: mantiene los registros A de mis dominios apuntando a la IP
# publica dinamica. Es un script con cron, por eso uso Alpine.

resource "proxmox_virtual_environment_container" "dns_sync" {
  node_name    = "main"
  vm_id        = 113
  unprivileged = true
  description  = "Mantiene los registros DNS de mis dominios con la IP publica dinamica. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "dns-sync"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.28/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/alpine-3.24-default_20260714_amd64.tar.xz"
    type             = "alpine"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 2
  }

  cpu { cores = 1 }

  memory {
    dedicated = 128
  }

  network_interface {
    name   = "eth0"
    bridge = "vmbr0"
  }

  started = true
}

output "dns_sync_ip" {
  value = "192.0.2.28"
}
