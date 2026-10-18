# lxc-dockge.tf: sustituye al CT 106 "dockge" (Tautulli, Seerr,
# battlepros-status, Obsidian, y el stack grande Caddy+Authelia+arr).
# Migracion por fases completada 2026-09-19 - ver el runbook de Obsidian
# para el detalle completo de cada fase (0: CT base con bind-mounts+TUN;
# 1: Tautulli/Seerr/battlepros-status; 2: Obsidian; 3: Caddy+Authelia+arr;
# 4: cutover).
#
# Tamano reducido respecto al CT106 original (16 cores/64GB, ~4GB RAM
# activa medida en real) - decision mia.
#
# Firewall Proxmox propio activado desde el principio (a diferencia del
# CT106 original, que nunca lo tuvo - decision deliberada de una auditoria
# anterior, revertida a peticion del usuario al migrar).

resource "proxmox_virtual_environment_container" "dockge" {
  node_name    = "main"
  vm_id        = 122
  unprivileged = true
  description  = "Media stack (Caddy/Authelia/arr/Tautulli/Seerr/Obsidian/battlepros-status) en 192.0.2.243, sustituye al CT 106 (parado, red de seguridad). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "dockge"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.243/24"
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
    size         = 150
  }

  cpu { cores = 8 }

  memory {
    dedicated = 24576
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # mount_point (bind de directorios del host) y device_passthrough
  # (/dev/net/tun, necesario para Gluetun/WireGuard dentro de Docker)
  # requieren root@pam - mismo 403 ya documentado en Plex/AMP. Se aplican
  # a mano via 'pct set' tras crear el CT, e ignorados aqui.
  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, mount_point, device_passthrough]
  }

  features {
    nesting = true
  }

  started = true
}

output "dockge_ip" {
  value = "192.0.2.243"
}
