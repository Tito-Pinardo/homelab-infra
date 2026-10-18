# lxc-agents.tf: CT de control + agentes de IA (Claude Code, Gemini CLI,
# Codex, OpenCode->Ollama de lucifer) con Codeman como panel web.
#
# Es el "LXC de control" previsto en el runbook "Terraform en Proxmox":
# el flujo de trabajo vive aqui en vez de en lucifer/Mac, y desde aqui se
# puede tocar TODO el homelab (clave SSH propia autorizada como root en
# cada CT + host Proxmox, ver playbooks/agents-access.yml). Por eso:
#   - panel solo por Caddy+Authelia 2FA en agents.home.arpa (nunca Traefik
#     ni Cloudflare, no es publico a proposito)
#   - los agentes corren como usuario 'agent', no root, dentro del CT
#
# Sin nesting/Docker a proposito: los CLI y Codeman son binarios/npm
# normales, no hace falta y reduce superficie.

resource "proxmox_virtual_environment_container" "agents" {
  node_name    = "main"
  vm_id        = 123
  unprivileged = true
  description  = "CT de control + agentes IA (Claude/Gemini/Codex/OpenCode) con Codeman en agents.home.arpa (Caddy+Authelia, solo LAN/VPN). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "agents"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.237/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Worktrees de varios agentes en paralelo + node_modules + caches de los
  # CLI: 40 GB con margen (pve-data al 60% el 2026-09-22).
  disk {
    datastore_id = "local-lvm"
    size         = 40
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

  started = true

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "agents_ip" {
  value = "192.0.2.237"
}
