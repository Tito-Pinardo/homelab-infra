# lxc-landing.tf: CT 125 "landing" - mi web personal titopinardogutierrez.com
# (binario de Rust + PostgreSQL, codigo en github.com/Tito-Pinardo/landing).
#
# CT propio y sin Docker a proposito: es lo unico de este homelab que se
# publica en internet con datos que escribe cualquiera (el formulario de
# contacto), asi que no comparte nada con el resto. Sin nesting ni
# privilegios; PostgreSQL escucha solo en el socket local.
# Ver docs/landing.md.

resource "proxmox_virtual_environment_container" "landing" {
  node_name    = "main"
  vm_id        = 125
  unprivileged = true
  description  = "Web personal titopinardogutierrez.com: binario Rust (Axum) + PostgreSQL local, detras de Traefik. Gestionado por Terraform + Ansible, ver ~/infra-tf y docs/landing.md."

  initialization {
    hostname = "landing"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.242/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Sistema + PostgreSQL + binario (~11 MB). Los mensajes de contacto ocupan
  # nada; la purga borra los de mas de un año.
  disk {
    datastore_id = "local-lvm"
    size         = 8
  }

  cpu { cores = 2 }

  # El binario usa ~15 MB; el resto es para PostgreSQL y la cache de disco.
  memory {
    dedicated = 1024
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

output "landing_ip" {
  value = "192.0.2.242"
}
