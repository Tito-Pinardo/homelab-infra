# lxc-pbs.tf: CT 129 "pbs" - Proxmox Backup Server. Copias diarias, cifradas e
# incrementales de todos los CT (OKD fuera) al disco USB lb2. Ver docs/copias.md.
#
# El almacen es un bind mount de /plex-server/lb2/pbs (mp0, /datastore): como
# el resto de bind mounts del repo, necesita root@pam y lo pone
# playbooks/pbs.yml con 'pct set'; aqui se ignora (ver lxc-plex.tf: quitarlo
# desde aqui recrearia el CT). Si lb2 no esta montado, el CT no arranca: asi
# nunca escribe copias en el disco del sistema.

resource "proxmox_virtual_environment_container" "pbs" {
  node_name    = "main"
  vm_id        = 129
  unprivileged = true
  description  = "Proxmox Backup Server: copias cifradas de los CT en lb2 (/plex-server/lb2/pbs). Gestionado por Terraform + Ansible, ver ~/infra-tf y docs/copias.md."

  initialization {
    hostname = "pbs"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.233/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Solo el sistema y PBS: las copias van en lb2.
  disk {
    datastore_id = "local-lvm"
    size         = 8
  }

  cpu { cores = 2 }

  # Recolector de basura y verificacion recorren todos los trozos: 2 GB van bien
  # para unos cientos de GB de copias.
  memory {
    dedicated = 2048
  }

  network_interface {
    name     = "eth0"
    bridge   = "vmbr0"
    firewall = true
  }

  lifecycle {
    # RAM en caliente (docs/despliegue.md): el proveedor reinicia el CT al
    # cambiarla; se cambia con pct set / la web y aqui queda como registro.
    ignore_changes = [memory, mount_point]
  }

  started = true
}

output "pbs_ip" {
  value = "192.0.2.233"
}
