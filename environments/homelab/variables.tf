# variables.tf: declara qué inputs necesita esta configuración.
# El VALOR real vive en terraform.tfvars (fuera de git).

variable "proxmox_api_token" {
  description = "Token API de terraform@pve (formato: usuario@realm!tokenid=secreto)"
  type        = string
  sensitive   = true
}
