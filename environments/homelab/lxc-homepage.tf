# lxc-homepage.tf: dashboard de servicios (gethomepage.dev), sustituye a
# Fenrus. Es una app Next.js sin release binaria - hay que compilarla
# (Node.js + pnpm) dentro del CT, de ahi mas CPU/RAM/disco que Element pese
# a servir tambien contenido en gran parte estatico tras el build.

resource "proxmox_virtual_environment_container" "homepage" {
  node_name    = "main"
  vm_id        = 112
  unprivileged = true
  description  = "Dashboard de servicios (Homepage - gethomepage.dev), sustituye a Fenrus. Lista de servicios generada desde traefik_routes (ver group_vars/all/services.yml). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "homepage"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.250/24"
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
    size         = 10
  }

  cpu { cores = 4 }

  memory {
    dedicated = 3072
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # user_account.keys es ForceNew - este CT se creo antes de anadir la
  # segunda clave SSH (Mac) a locals.tf. Ambas claves ya estan en
  # authorized_keys a mano (mismo patron que el resto de CT viejos, ver
  # providers.tf/locals.tf) - sin esto, cualquier 'terraform apply' intenta
  # "corregir" el desajuste destruyendo y recreando el CT entero.
  # Descubierto 2026-09-19 revisando un 'terraform plan' que iba a borrar
  # 4 CT en produccion.
  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, initialization[0].user_account]
  }

  started = true
}

output "homepage_ip" {
  value = "192.0.2.250"
}
