# CT de Plex sin privilegios, con idmap y device_passthrough para usar la
# GPU (NVENC) en el transcodificado.

resource "proxmox_virtual_environment_container" "plex" {
  node_name    = "main"
  vm_id        = 117
  unprivileged = true
  description  = "Plex Media Server sin privilegios con acceso a la GPU. Gestionado por Terraform + Ansible."

  initialization {
    hostname = "plex"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.11/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-12-standard_12.12-1_amd64.tar.zst"
    type             = "debian"
  }

  disk {
    datastore_id = "local-lvm"
    size         = 48
  }

  cpu { cores = 6 }

  memory {
    dedicated = 24576
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  features {
    nesting = true
  }

  # El GID 44 (video, dueno de los dispositivos de la GPU y de las carpetas de
  # medios) pasa 1:1; el resto del rango se desplaza como de costumbre.
  idmap {
    type         = "gid"
    container_id = 0
    host_id      = 100000
    size         = 44
  }
  idmap {
    type         = "gid"
    container_id = 44
    host_id      = 44
    size         = 1
  }
  idmap {
    type         = "gid"
    container_id = 45
    host_id      = 100045
    size         = 65491
  }
  idmap {
    type         = "uid"
    container_id = 0
    host_id      = 100000
    size         = 65536
  }

  # Las bibliotecas de medios (bind mounts del host) no se declaran aqui: la
  # API de Proxmox restringe los mount points de tipo bind a root@pam. Se
  # aplican con 'pct set' tras crear el CT.

  # Imprescindible: sin esto, cualquier apply veria el passthrough y los mount
  # points aplicados por fuera como diferencias e intentaria quitarlos, y en
  # este provider eso recrea el CT entero.
  lifecycle {
    ignore_changes = [device_passthrough, mount_point]
  }

  started = true
}

output "plex_ip" {
  value = "192.0.2.11"
}
