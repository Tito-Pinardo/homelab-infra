# lxc-plex.tf: sustituye al CT 100 "plex" - YA PROMOVIDO A DEFINITIVO
# (2026-09-16, confirmado con clientes reales - TV transcodificando bien).
# El CT 100 NO se destruye - se renombra a "plex-old" y se le retira la IP
# .3 (movida a .8) para que pueda arrancarse de nuevo sin chocar con este,
# pero se queda parado indefinidamente como red de seguridad real.
#
# Diferencia clave frente al CT 100 (privilegiado + lxc.mount.entry/cgroup2
# a mano): este CT es SIN PRIVILEGIOS, con "idmap" + "device_passthrough"
# (soportados de forma nativa por el provider) - mismo acceso real a la
# GTX 1050 Ti, demostrado con un encode NVENC real en un CT de prueba
# desechable (115, ya destruido) antes de tocar nada de Plex de verdad.
# Menos superficie de ataque, mismo hardware transcoding.
#
# El GID 44 (grupo "video" del host) pasa 1:1 sin desplazar - por
# coincidencia (o mas bien por diseño del propio Debian), TANTO los
# dispositivos /dev/nvidia*/dri como las carpetas de medios
# (/plex-server/lb*, root:video 2775) pertenecen a ese mismo grupo, y el
# usuario "plex" que crea el propio .deb es miembro de "video" - el mismo
# idmap resuelve el acceso a la GPU Y a los datos de biblioteca a la vez.
#
# device_passthrough NO se declara aqui - la API de Proxmox solo permite
# configurarlo a root@pam (403 real, confirmado con el CT de prueba) y el
# token de Terraform es una cuenta de servicio acotada a proposito. Se
# aplica via `pct set` por SSH root tras crear el CT (ver runbook).

resource "proxmox_virtual_environment_container" "plex" {
  node_name    = "main"
  vm_id        = 117
  unprivileged = true
  description  = "Plex Media Server - servidor definitivo, sustituye al CT 100 (renombrado a plex-old, parado pero conservado como red de seguridad). Sin privilegios + idmap/device_passthrough para la GTX 1050 Ti (ver runbook). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "plex"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.3/24"
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

  # GID 44 (video, dueño de /dev/nvidia*+dri Y de las carpetas de medios)
  # pasa 1:1 sin desplazar; el resto del rango se desplaza como de
  # costumbre. Mismo esquema demostrado en el CT de prueba (115).
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

  # Las 10 bibliotecas de medios (bind mounts de directorios del host, mismas
  # rutas que el CT 100 - ver `pct config 100`) NO se declaran aqui: la API
  # de Proxmox tambien restringe "mount point type bind" a root@pam (403
  # real, mismo motivo que device_passthrough). Se aplican via `pct set`
  # por SSH root tras crear el CT - ver runbook.

  # CRITICO: sin esto, cualquier `terraform apply` (incluso uno que solo
  # toque hostname/IP) ve el device_passthrough/mount_point aplicados por
  # fuera como "drift" respecto al vacio declarado aqui, e intenta
  # eliminarlos - y eliminar esos bloques esta marcado ForceNew en este
  # provider, o sea que INTENTA DESTRUIR Y RECREAR EL CT ENTERO (visto en
  # real 2026-09-16, con Plex ya en produccion y streaming activo - se paro
  # a tiempo revisando el plan antes de aplicar, nunca se llego a ejecutar).
  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, device_passthrough, mount_point]
  }

  started = true
}

output "plex_ip" {
  value = "192.0.2.3"
}
