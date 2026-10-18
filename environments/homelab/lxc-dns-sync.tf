# lxc-dns-sync.tf: sustituye al CT 105 "Scripts". Se investigo su contenido
# real antes de migrar (ver runbook) - de todo lo que habia, lo UNICO
# realmente en uso son los 3 scripts que sincronizan el registro A de
# example.org/titopinardogutierrez.com/example.net con la IP WAN
# dinamica cada 5 min. Todo lo demas (endurecer-base.py, inspeccionar-
# sistemas.py, manual/, Postfix, un contenedor Docker muerto) confirmado
# sin uso por el propio usuario - no se migra.
#
# Alpine en vez de Debian (primera vez en este repo) - carga de trabajo real
# es un script + cron, Alpine no necesita nada de lo que trae Debian para
# esto. Coste: primer role de Ansible con apk/OpenRC en vez de apt/systemd.

resource "proxmox_virtual_environment_container" "dns_sync" {
  node_name    = "main"
  vm_id        = 113
  unprivileged = true
  description  = "Sincroniza el registro A de example.org/titopinardogutierrez.com/example.net con la IP WAN dinamica cada 5 min (cron). Sustituye al CT 105 'Scripts' (el resto de su contenido estaba sin usar). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "dns-sync"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.249/24"
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

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory]
  }
}

output "dns_sync_ip" {
  value = "192.0.2.249"
}
