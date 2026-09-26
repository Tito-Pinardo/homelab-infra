resource "proxmox_virtual_environment_container" "traefik" {
  node_name    = "main"
  vm_id        = 209
  unprivileged = true
  description  = "Reverse proxy publico con TLS de Let's Encrypt. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "traefik"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.12/24"
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
    size         = 50
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

  # Las claves SSH de este CT las gestiono fuera de Terraform: user_account.keys
  # es ForceNew y cualquier diferencia recrearia el CT entero.
  lifecycle {
    ignore_changes = [initialization[0].user_account]
  }

  started = true
}

output "traefik_prod_ip" {
  value = "192.0.2.12"
}
