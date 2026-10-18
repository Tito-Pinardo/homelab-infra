# lxc-openbao.tf: CT 128 "openbao" - guarda las llaves maestras de infra-tf
# (contraseña del vault de Ansible y credenciales de Terraform), que salen
# del disco del CT 123. Ver docs/openbao.md.
#
# Se desella A MANO tras cada arranque (decision de Tito, 15-10): la clave
# de desellado no esta en ningun disco del servidor. Mientras este sellado no
# hay despliegues ni playbooks, y avisa en Element.

resource "proxmox_virtual_environment_container" "openbao" {
  node_name    = "main"
  vm_id        = 128
  unprivileged = true
  description  = "OpenBao (bao.home.arpa, Caddy+Authelia; API solo para el CT 123): llaves maestras de infra-tf. Desellado a mano. Gestionado por Terraform + Ansible, ver ~/infra-tf y docs/openbao.md."

  initialization {
    hostname = "openbao"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.234/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Binario (~100 MB) + datos cifrados (unos KB) + log de auditoria.
  disk {
    datastore_id = "local-lvm"
    size         = 8
  }

  cpu { cores = 1 }

  memory {
    dedicated = 512
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

output "openbao_ip" {
  value = "192.0.2.234"
}
