# lxc-ia-asistente.tf: CT que agrupa el bot conversacional de Matrix, todos
# los conectores (Obsidian/AMP/Zabbix-Wazuh/correo) y el Ollama de
# EMBEDDINGS (headless, CPU, nomic-embed-text, siempre encendido - distinto
# del Ollama de CHAT, que vive en el PC lucifer con GPU y solo esta
# disponible mientras ese PC este encendido, ver runbook en Obsidian).
#
# No se separa en mas CT: bot y conectores comparten vault y ciclo de vida.
# Mas cores que Qdrant porque la generacion de embeddings por CPU se
# beneficia de paralelismo (el host tiene 48 cores reales de sobra).

resource "proxmox_virtual_environment_container" "ia_asistente" {
  node_name    = "main"
  vm_id        = 118
  unprivileged = true
  description  = "Bot IA (Matrix) + conectores (Obsidian/AMP/Zabbix-Wazuh/correo) + Ollama embeddings. Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "ia-asistente"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.247/24"
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

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "ia_asistente_ip" {
  value = "192.0.2.247"
}
