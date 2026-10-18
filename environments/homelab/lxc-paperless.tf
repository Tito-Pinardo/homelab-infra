# lxc-paperless.tf: sustituye al CT 133 "paperless" (creado a mano
# 2026-09-09, ver runbook en Obsidian + auditoria-casa/paperless-20260909/).
# Documentos personales sensibles (catastro, defuncion, empadronamiento) -
# integrado con la IA local del PC lucifer (Ollama, 192.0.2.30:11434) para
# sugerencias/busqueda semantica.
#
# Divergencia deliberada del resto de la flota: SIN "user_account" (ningun
# root SSH). Se descubrio 2026-09-17 que el CT 133 original habia acabado
# con SSH abierto (regla de firewall para PC+VPN, sshd activo, 2 claves en
# authorized_keys) pese a haberse disenado "sin SSH, root bloqueado" - un
# descuido de seguridad no documentado, en el servicio que menos margen
# tiene para tenerlo. Decision explicita del usuario al migrar: cerrar SSH
# del todo. Administracion exclusiva via 'pct exec' desde el host Proxmox
# (ver ansible/inventory/group_vars/paperless/vars.yml, connection plugin
# community.proxmox.proxmox_pct_remote) - sin excepcion para PC ni VPN, a
# diferencia de zabbix/wazuh (que si mantienen esa regla).

resource "proxmox_virtual_environment_container" "paperless" {
  node_name    = "main"
  vm_id        = 119
  unprivileged = true
  description  = "Paperless-ngx (documentos personales sensibles). Sin SSH a proposito - administrar solo via pct exec. Gestionado por Terraform + Ansible, ver ~/infra-tf."

  initialization {
    hostname = "paperless"

    # Sin bloque "user_account": ninguna clave SSH, root sin password - a
    # diferencia de TODOS los demas CT de este repo.

    ip_config {
      ipv4 {
        # IP definitiva (la que tenia el CT 133 original) - promovida el
        # 2026-09-17 tras verificar el CT 119 a fondo (datos restaurados,
        # nginx TLS con el certificado real, stack sano). CT 133 parado
        # (no destruido) - red de seguridad, no hay backups todavia.
        address = "192.0.2.245/24"
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

  cpu { cores = 4 }

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

output "paperless_ip" {
  value = "192.0.2.245"
}
