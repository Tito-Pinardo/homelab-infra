# homelab-infra

La infraestructura de mi homelab como código: Terraform para crear los
contenedores y VMs en Proxmox, y Ansible para configurarlos.

**Cada pieza, contada por dentro:** en [titopinardogutierrez.com](https://titopinardogutierrez.com/es/#lab)
cada servicio tiene su unidad del rack con un mapa animado, sus decisiones,
sus averías reales y un enlace a su carpeta en este repositorio.

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
                        vault.yml cifrado; aquí solo hay vault.yml.example)
  playbooks/            un playbook por servicio, más los de mantenimiento
  roles/                un rol por servicio
scripts/                monitorización (Zabbix/Wazuh -> Matrix) y pruebas
docs/                   descripción de las piezas más grandes
githooks/               push automatico al repositorio de respaldo
```

## Servicios

| Área | Servicios |
|---|---|
| Entrada | Traefik (público, Let's Encrypt + Cloudflare), Caddy + Authelia (red local) |
| Multimedia | Plex (con GPU), Tautulli, Seerr, stack *arr con qBittorrent tras VPN |
| Comunicación | Synapse (Matrix privado) y Element Web |
| Asistente IA | Hermes: bot de Matrix con herramientas, modelo local, Qdrant y búsqueda en notas, correo y calendario ([docs](docs/)) |
| Finanzas | Demeter: compras y gastos a partir del correo ([docs](docs/demeter-procedimientos.md)) |
| Documentos | Paperless-ngx (aislado, sin SSH) |
| Red | Technitium DNS, sincronización de DNS dinámico |
| Monitorización | Zabbix, Wazuh y avisos a Matrix ([docs](docs/wazuh.md)) |
| Otros | AMP (servidores de juego), n8n, Homepage, Obsidian, clúster OKD |

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
ansible-playbook playbooks/update-containers.yml   # imágenes Docker
```

Cada `group_vars/<grupo>/vault.yml.example` indica qué secretos necesita ese
grupo: se copia a `vault.yml`, se rellena y se cifra con `ansible-vault encrypt`.

## Principios

- Versiones fijadas: nada se actualiza solo al volver a ejecutar un playbook.
- Los datos de cada servicio se restauran aparte; los roles solo gestionan la
  configuración.
- Todo lo privado es accesible solo desde la red local o la VPN, detrás de
  autenticación con doble factor.
- El asistente IA funciona en local: nada sale de mi red.
