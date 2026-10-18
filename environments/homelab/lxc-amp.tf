# lxc-amp.tf: sustituye al CT 108 "AMP" (CubeCoders Application Management
# Panel, gestiona 10 instancias de servidores de juego). El servicio mas
# complejo migrado hasta ahora - ver el runbook de Obsidian
# "05 Procedimientos/Terraform en Proxmox.md" para el detalle completo
# (Docker, UFW auto-sincronizado por AMP cada 5 min, bug conocido de
# timeout en el arranque, licencia AMP Advanced ligada a machine-id).
#
# Se creo en paralelo con IP temporal (.239), se verifico a fondo (10
# instancias reconstruidas desde los datos copiados del CT108, Docker+UFW
# sanos, licencia reactivada con la clave del usuario) y se promovio el
# 2026-09-18/19 - mismo patron que traefik-test -> traefik: hostname "amp" +
# IP .136. El CT 108 original queda PARADO (no destruido) como red de
# seguridad, renombrado "amp-old".
#
# Los datos de juego (158G minecraft + 19G steam) NO se copian - son
# bind-mounts de datasets ZFS del pool "games" en el host, se reutilizan
# tal cual (mismo volumen, misma ruta). Solo el estado propio de ADS01
# (usuarios/roles/2FA/config, ~1.5GB) se copio, igual que /etc/dns en
# Technitium.
#
# Tamano reducido respecto al CT108 original (24 cores/64GB, uso real ~5GB
# con solo 2 de 10 instancias corriendo) - decision mia 2026-09-18.
# RAM subida a 32GB el 2026-10-06: David01 reserva 20GB de heap al arrancar
# (Xms=Xmx + AlwaysPreTouch) y Velocity hasta 4GB; con 24GB y sin swap no
# cabian los dos al maximo.
#
# CPU fijada al socket 0 (6 nucleos fisicos + sus hilos gemelos) con una
# linea raw en /etc/pve/lxc/121.conf que este provider no gestiona:
#   lxc.cgroup2.cpuset.cpus: 0,2,4,6,8,10,24,26,28,30,32,34
# pvestatd no reequilibra los CT que la tienen. Si se recrea el CT hay que
# volver a ponerla a mano. Detalle en docs/amp-rendimiento.md.

resource "proxmox_virtual_environment_container" "amp" {
  node_name    = "main"
  vm_id        = 121
  unprivileged = true
  description  = "AMP (panel de servidores de juego, 192.0.2.136:8080), sustituye al CT 108 (parado, red de seguridad). Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "amp"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.136/24"
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
    size         = 80
  }

  cpu { cores = 12 }

  memory {
    dedicated = 65536
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  # mount_point de tipo "bind" (directorio del host, no un volumen Proxmox
  # normal) solo lo puede crear root@pam via la API - el token normal del
  # provider da 403 "Permission check failed" (mismo tipo de restriccion ya
  # documentada para device_passthrough en lxc-plex.tf). Se aplican los dos
  # mp0/mp1 a mano via 'pct set' (SSH root al host) despues del create, y se
  # ignoran aqui para que Terraform no intente "corregir" ese drift
  # destruyendo el CT.
  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, mount_point]
  }

  features {
    nesting = true
  }

  started = true
}

output "amp_ip" {
  value = "192.0.2.136"
}
