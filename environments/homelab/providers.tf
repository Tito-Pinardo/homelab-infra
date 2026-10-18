# providers.tf: qué plugin (provider) usa Terraform y cómo se conecta a Proxmox.
# bpg/proxmox es el provider mantenido activamente (el histórico Telmate/proxmox
# apenas recibe actualizaciones).

terraform {
  # Estado en una ruta fija fuera del checkout, la misma para el checkout de
  # trabajo y el de despliegue (runner del CT 123): un solo estado y un solo
  # bloqueo. La ruta va en el init, no aqui (ver docs/despliegue.md):
  #   terraform init -backend-config=path=/home/agent/.infra-tf/estado/homelab.tfstate
  # El CI usa init -backend=false y no lo necesita.
  backend "local" {}

  # La del CI y el CT 123 (ci_terraform_version); 1.16 por los avisos de tflint.
  required_version = ">= 1.16"

  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.116"
    }
  }
}

provider "proxmox" {
  endpoint  = "https://192.0.2.2:8006/"
  api_token = var.proxmox_api_token

  # Proxmox usa certificado autofirmado por defecto -> sin esto, TLS falla.
  insecure = true

  # idmap (y device_passthrough, aunque ese requiere ademas root@pam en la
  # API - ver lxc-gpu-test.tf) no se pueden fijar via la API normal, el
  # provider los aplica via SSH directo al host. Reusa la misma clave que ya
  # tiene acceso root por SSH (usada en todo el repo para pct exec/firewall).
  ssh {
    agent    = false
    username = "root"
    # id_ed25519 en el CT 123 (agents, usuario 'agent'), id_rsa en lucifer.
    # Solo es la conexion SSH del provider, no entra en el state.
    private_key = file(pathexpand(fileexists(pathexpand("~/.ssh/id_ed25519")) ? "~/.ssh/id_ed25519" : "~/.ssh/id_rsa"))
  }
}
