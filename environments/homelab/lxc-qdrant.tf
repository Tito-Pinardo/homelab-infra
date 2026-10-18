# lxc-qdrant.tf: CT dedicado a Qdrant (base de datos vectorial), parte del
# proyecto "asistente IA + base semantica" (ver runbook en Obsidian).
# Separado del CT ia-asistente aposta: Qdrant es el unico componente con
# estado persistente critico de todo el proyecto (todos los embeddings
# viven aqui) - mezclarlo con el bot/conectores (que no tienen estado que
# de verdad duela perder) complicaria backups sin necesidad.
#
# Sin Docker: mismo patron binario+systemd que Traefik (el role instala el
# binario oficial de una release de GitHub fijada, no ":latest").

resource "proxmox_virtual_environment_container" "qdrant" {
  node_name    = "main"
  vm_id        = 115
  unprivileged = true
  description  = "Qdrant (base de datos vectorial) - backend del asistente IA. Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "qdrant"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.246/24"
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

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "qdrant_ip" {
  value = "192.0.2.246"
}
