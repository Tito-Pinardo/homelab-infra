# homelab-infra

La infraestructura de mi homelab como código: Terraform para crear los
contenedores y VMs en Proxmox, y Ansible para configurarlos.

> **Nota:** esta es una versión pública y reducida del repositorio real. Las
> funciones solo tienen el nombre y una descripción de lo que hacen. Las IPs
> son de los rangos de documentación (`192.0.2.0/24`, `198.51.100.0/24`,
> `203.0.113.0/24`) y los dominios son `example.*`. Las reglas de firewall, las
> listas de orígenes permitidos y todos los secretos se han quitado. No se
> puede desplegar tal cual.

## Estructura

```
environments/homelab/   Terraform (provider bpg/proxmox): un fichero por CT o VM
ansible/
  inventory/            hosts.yml y group_vars por grupo (los secretos van en
                        vault.yml cifrado; aqui solo hay vault.yml.example)
  playbooks/            un playbook por servicio, mas los de mantenimiento
  roles/                un rol por servicio
scripts/                monitorizacion (Zabbix/Wazuh -> Matrix) y pruebas
docs/                   descripcion de las piezas mas grandes
githooks/               push automatico al repositorio de respaldo
```

## Servicios

| Area | Servicios |
|---|---|
| Entrada | Traefik (publico, Let's Encrypt + Cloudflare), Caddy + Authelia (red local) |
| Multimedia | Plex (con GPU), Tautulli, Seerr, stack *arr con qBittorrent tras VPN |
| Comunicacion | Synapse (Matrix privado) y Element Web |
| Asistente IA | Hermes: bot de Matrix con herramientas, modelo local, Qdrant y busqueda en notas, correo y calendario ([docs](docs/)) |
| Finanzas | Demeter: compras y gastos a partir del correo ([docs](docs/demeter-procedimientos.md)) |
| Documentos | Paperless-ngx (aislado, sin SSH) |
| Red | Technitium DNS, sincronizacion de DNS dinamico |
| Monitorizacion | Zabbix, Wazuh y avisos a Matrix ([docs](docs/wazuh.md)) |
| Otros | AMP (servidores de juego), n8n, Homepage, Obsidian, cluster OKD |

## Uso

```bash
# Crear o actualizar la infraestructura
cd environments/homelab
cp terraform.tfvars.example terraform.tfvars   # rellenar el token de Proxmox
terraform init && terraform plan

# Configurar un servicio
cd ansible
ansible-playbook playbooks/<servicio>.yml

# Mantenimiento
ansible-playbook playbooks/update-all.yml          # paquetes del sistema
ansible-playbook playbooks/update-containers.yml   # imagenes Docker
```

Cada `group_vars/<grupo>/vault.yml.example` indica que secretos necesita ese
grupo: se copia a `vault.yml`, se rellena y se cifra con `ansible-vault encrypt`.

## Principios

- Versiones fijadas: nada se actualiza solo al volver a ejecutar un playbook.
- Los datos de cada servicio se restauran aparte; los roles solo gestionan la
  configuracion.
- Todo lo privado es accesible solo desde la red local o la VPN, detras de
  autenticacion con doble factor.
- El asistente IA funciona en local: nada sale de mi red.
