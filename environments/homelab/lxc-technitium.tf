# lxc-technitium.tf: sustituye al CT 116 "technitium" (instalado a mano
# 2026-09-13, sustituyo a Pi-hole). DNS de TODA la LAN.
#
# Se creo en paralelo con IP temporal (.248), se verifico a fondo (zonas
# reales restauradas desde el CT116, resolucion interna+recursiva
# confirmada, DNAT 53->5300 sano) y se promovio el 2026-09-18 - mismo
# patron que traefik-test -> traefik: terraform state mv (technitium_new ->
# technitium) + hostname "technitium" + IP .45. El CT 116 original queda
# PARADO (no destruido) como red de seguridad.
#
# Debian 13/trixie (no bookworm como el CT116 original) - sin motivo para
# quedarse en bookworm aqui, el runtime .NET de Technitium es autocontenido
# (se descarga aparte, no via apt) y no depende de ninguna libreria de
# sistema con el pin que si tiene Plex (CUDA de NVIDIA).

resource "proxmox_virtual_environment_container" "technitium" {
  node_name    = "main"
  vm_id        = 120
  unprivileged = true
  description  = "DNS EN PRODUCCION: Technitium en 192.0.2.45. Sustituye al CT 116 (parado, red de seguridad). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "technitium"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.45/24"
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
    size         = 6
  }

  cpu { cores = 2 }

  memory {
    dedicated = 1024
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # Arranca el primero: tras un corte de luz el resto de CT necesita DNS.
  # Lo puso playbooks/pve-dns.yml (10-10) con pct set; aqui para que el plan
  # no lo quite. -1 en los retardos = "sin valor" en Proxmox (lo que leia el
  # provider del CT real).
  startup {
    order      = 1
    up_delay   = -1
    down_delay = -1
  }

  started = true

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "technitium_ip" {
  value = "192.0.2.45"
}
