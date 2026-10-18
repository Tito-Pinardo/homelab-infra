resource "proxmox_virtual_environment_container" "traefik" {
  node_name    = "main"
  vm_id        = 209
  unprivileged = true
  description  = "Reverse proxy / punto de entrada publico - enruta *.example.org, example.net y titopinardogutierrez.com hacia los servicios internos (TLS via Let's Encrypt + Cloudflare DNS-01). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "traefik"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        # Cutover 2026-09-15: este CT (209) se convierte en el Traefik real,
        # toma la IP que tenía el 109. El puerto de MikroTik no se toca -
        # su DNAT ya apunta a .6, así que basta con mover la IP aquí.
        address = "192.0.2.6/24"
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
    size         = 50
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

output "traefik_prod_ip" {
  value = "192.0.2.6"
}
