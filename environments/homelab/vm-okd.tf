# Clúster OKD compact (3 nodos control-plane, schedulable). VMs reales (no LXC) -
# CoreOS necesita virtualizacion completa, no contenedores. VMID = ultimo octeto
# de la IP para que sea facil de mapear (220/221/222 <-> .220/.221/.222).
#
# Las MAC estan fijadas a mano (rango localmente administrado 02:00:00:...) para
# que coincidan exactamente con agent-config.yaml (~/infra-tf/okd/cluster419) - el
# agent-based installer asigna cada IP estatica por MAC, no por orden de arranque.
#
# Version de OKD: 4.19.0-okd-scos.19, NO 4.22.x. La 4.22.0-okd-scos.10 tiene un
# bug reproducible en su ISO del Agent-Based Installer que cuelga cargando
# initrd.img via El Torito/BIOS (confirmado con 10 configuraciones distintas,
# incluyendo QEMU puro sin Proxmox y sin KVM - ver runbook "OKD Cluster -
# Agent-Based Installer" en Obsidian para el diagnostico completo). La 4.19 no
# tiene ese bug.
#
# bios = seabios (por defecto, no explicito): UEFI/OVMF se colgaba en su propio
# boot manager con esta familia de ISOs, en un byte fijo, independiente del bus
# de disco (SATA/IDE/SCSI). SeaBIOS + IDE es la combinacion que funciona.

locals {
  okd_nodes = {
    "okd-master-0" = { vm_id = 220, mac = "02:00:00:00:01:01", ip = "192.0.2.220" }
    "okd-master-1" = { vm_id = 221, mac = "02:00:00:00:01:02", ip = "192.0.2.221" }
    "okd-master-2" = { vm_id = 222, mac = "02:00:00:00:01:03", ip = "192.0.2.222" }
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

  # 32GB, no 16GB: el entorno live del agent-based installer guarda todo
  # (incluidas las imagenes de contenedor del bootstrap, >17GB) en un overlay
  # temporal en RAM (/run/ephemeral*) de aprox. el 50% de la RAM asignada.
  # Con 16GB el overlay (~7.9GB) se llenaba a media instalacion y keepalived
  # entraba en bucle de fallo por "No space left on device" - visto en vivo
  # durante el bootstrap real. Ver runbook OKD en Obsidian.
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
      # Restos de cuando se probo UEFI: cada nodo conserva un efi_disk de 4 MB
      # en local-lvm y `machine` vale " ". Con SeaBIOS el disco EFI no se lee
      # nunca, pero sin esto cada plan proponia BORRARLO (2026-09-23). Se
      # prefiere reflejar la realidad a destruir algo para cuadrar el plan;
      # si algun dia se quiere limpiar, se quita de aqui y se aplica a mano.
      efi_disk,
      machine,
    ]
  }
}

output "okd_node_ips" {
  value = { for k, v in local.okd_nodes : k => v.ip }
}
