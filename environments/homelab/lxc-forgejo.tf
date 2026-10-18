# lxc-forgejo.tf: CT 126 "forgejo" (servidor git con interfaz web) y CT 127
# "forgejo-runner" (ejecuta el CI de los repos).
#
# Forgejo recibe una copia de infra-tf en cada push al repo central del CT
# 123 (hook post-receive de ese bare, ver roles/forgejo). No sustituye a los
# remotos de siempre: si este CT se cae, el trabajo sigue igual.
#
# El runner va en un CT aparte a proposito: ejecuta lo que haya en el repo,
# asi que no comparte maquina con los repos ni guarda nada sensible (ni la
# clave de la API de Proxmox, ni el tfstate, ni la contraseña del vault).
# Solo comprueba; terraform apply y ansible-playbook siguen lanzandose desde
# el CT 123. Modo "host" (sin Docker): sin nesting, el aislamiento es el CT.
# Ver docs/forgejo.md.

resource "proxmox_virtual_environment_container" "forgejo" {
  node_name    = "main"
  vm_id        = 126
  unprivileged = true
  description  = "Forgejo (git.home.arpa, Caddy+Authelia, solo LAN/VPN): copia de infra-tf con CI. Gestionado por Terraform + Ansible, ver ~/infra-tf y docs/forgejo.md."

  initialization {
    hostname = "forgejo"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.235/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Binario (~100 MB) + SQLite + repos: infra-tf ocupa 16 MB con todo el
  # historial. 10 GB dan para muchos repos mas.
  disk {
    datastore_id = "local-lvm"
    size         = 10
  }

  cpu { cores = 2 }

  # Forgejo con SQLite y un usuario se queda en ~200 MB.
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

resource "proxmox_virtual_environment_container" "forgejo_runner" {
  node_name    = "main"
  vm_id        = 127
  unprivileged = true
  description  = "Runner del CI de Forgejo (modo host, sin Docker ni secretos; solo comprueba). Gestionado por Terraform + Ansible, ver ~/infra-tf y docs/forgejo.md."

  initialization {
    hostname = "forgejo-runner"

    user_account {
      keys = local.admin_ssh_keys
    }

    ip_config {
      ipv4 {
        address = "192.0.2.236/24"
        gateway = "192.0.2.1"
      }
    }
  }

  operating_system {
    template_file_id = "local:vztmpl/debian-13-standard_13.1-2_amd64.tar.zst"
    type             = "debian"
  }

  # Herramientas del CI (terraform, ansible-lint, gitleaks), cache de
  # providers y colecciones, y la copia de trabajo de cada ejecucion.
  disk {
    datastore_id = "local-lvm"
    size         = 16
  }

  cpu { cores = 2 }

  # ansible-lint sobre todo el repo es lo que mas pide (~1 GB).
  memory {
    dedicated = 2048
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

output "forgejo_ip" {
  value = "192.0.2.235"
}

output "forgejo_runner_ip" {
  value = "192.0.2.236"
}
