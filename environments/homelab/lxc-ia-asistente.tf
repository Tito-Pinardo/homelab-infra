# CT del asistente: bot de Matrix, conectores (notas, correo, calendario,
# monitorizacion) y el modelo de embeddings por CPU. El modelo de chat corre
# en mi PC con GPU.
#
# Bot y conectores comparten vault y ciclo de vida, por eso van juntos.

resource "proxmox_virtual_environment_container" "ia_asistente" {
  node_name    = "main"
  vm_id        = 118
  unprivileged = true
  description  = "Asistente IA (Matrix) con sus conectores y el modelo de embeddings. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "ia-asistente"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.27/24"
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

  cpu { cores = 8 }

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

output "ia_asistente_ip" {
  value = "192.0.2.27"
}
