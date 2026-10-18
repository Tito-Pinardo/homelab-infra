# lxc-n8n.tf: sustituye al CT 102 "n8n" (community-script, gestionado a
# mano). Investigacion previa (ver runbook): de los 17 workflows guardados
# solo 1 esta realmente vivo y en uso - "divxtotal + qbitorent" (336
# ejecuciones/7 dias via el histerico de n8n). El otro que aparecia
# "activo", "Readarr Kindle", tiene 0 ejecuciones en toda su historia y
# Readarr ya ni existe en el stack (sustituido por LazyLibrarian, que ya
# manda los libros al Kindle por su propio email nativo) - no se migra.
#
# Arquitectura real: 3 contenedores Docker (n8n + puppeteer-api -scraper
# Chromium a medida para divxtotal- + socket-proxy para que n8n pueda
# reiniciar puppeteer-api solo). Dimensionado muy por debajo del CT 102
# original (10 vCPU/32GB RAM/48GB disco asignados, uso real ~770MB RAM).

resource "proxmox_virtual_environment_container" "n8n" {
  node_name    = "main"
  vm_id        = 114
  unprivileged = true
  description  = "n8n (solo el workflow real: divxtotal + qBittorrent, cada 30 min via puppeteer-api). Sustituye al CT 102 (community-script). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "n8n"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.251/24"
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

  features {
    nesting = true
  }

  started = true

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "n8n_ip" {
  value = "192.0.2.251"
}
