# Cluster OKD compacto (3 nodos control-plane). VMs y no LXC porque CoreOS
# necesita virtualizacion completa.
#
# Las MAC estan fijadas para que coincidan con agent-config.yaml: el
# instalador asigna cada IP estatica por MAC.
#
# Version de OKD fijada a una que instala bien con el Agent-Based Installer.

locals {
  okd_nodes = {
    "okd-master-0" = { vm_id = 220, mac = "02:00:00:00:01:01", ip = "192.0.2.18" }
    "okd-master-1" = { vm_id = 221, mac = "02:00:00:00:01:02", ip = "192.0.2.19" }
    "okd-master-2" = { vm_id = 222, mac = "02:00:00:00:01:03", ip = "192.0.2.20" }
  }
}

resource "proxmox_virtual_environment_vm" "okd_node" {
  for_each = local.okd_nodes

  node_name = "main"
  vm_id     = each.value.vm_id
  name      = each.key

  cpu {
    cores = 4
    type  = "host"
  }

  # 32 GB: el entorno live del instalador guarda las imagenes del bootstrap en
  # un overlay en RAM de la mitad de la memoria asignada.
  memory {
    dedicated = 32768
  }

  disk {
    datastore_id = "local-lvm"
    interface    = "scsi0"
    size         = 120
  }

  network_device {
    bridge      = "vmbr0"
    mac_address = each.value.mac
  }

  # El provider no añade rng0 por defecto (a diferencia del asistente web de
  # Proxmox). Sin fuente de entropia, el arranque de CoreOS se puede quedar
  # colgado indefinidamente esperando /dev/random durante Ignition.
  rng {
    source = "/dev/urandom"
  }

  cdrom {
    file_id   = "local:iso/okd-agent-419.iso"
    interface = "ide3"
  }

  boot_order = ["ide3", "scsi0"]

  agent {
    enabled = false # CoreOS trae su propio qemu-guest-agent, pero aun no esta instalado el SO
  }

  started = false

  lifecycle {
    ignore_changes = [
      cdrom,      # tras la instalacion se expulsa/retira la ISO a mano; no reinsertarla en cada apply
      boot_order, # idem - una vez instalado, el orden real de arranque puede cambiar manualmente
      # Restos de una prueba con UEFI: cada nodo conserva un disco EFI que con
      # SeaBIOS no se usa. Lo reflejo aqui para que el plan no proponga borrarlo.
      efi_disk,
      machine,
    ]
  }
}

output "okd_node_ips" {
  value = { for k, v in local.okd_nodes : k => v.ip }
}
