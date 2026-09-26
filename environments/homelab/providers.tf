# providers.tf: qué plugin (provider) usa Terraform y cómo se conecta a Proxmox.
# bpg/proxmox es el provider mantenido activamente (el histórico Telmate/proxmox
# apenas recibe actualizaciones).

terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.66"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://192.0.2.10:8006/"
  api_token = var.proxmox_api_token

  # Proxmox usa certificado autofirmado por defecto -> sin esto, TLS falla.
  insecure = true

  # idmap y device_passthrough no se pueden fijar por la API normal: el
  # provider los aplica por SSH al host.
  ssh {
    agent    = false
    username = "root"
    # Clave SSH del provider. No entra en el state.
    private_key = file(pathexpand(fileexists(pathexpand("~/.ssh/id_ed25519")) ? "~/.ssh/id_ed25519" : "~/.ssh/id_rsa"))
  }
}
