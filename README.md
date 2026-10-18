# homelab-infra

La infraestructura de mi homelab como código: Terraform para crear los
contenedores y VMs en Proxmox, y Ansible para configurarlos.

**Cada pieza, contada por dentro:** en [titopinardogutierrez.com](https://titopinardogutierrez.com/es/#lab)
cada servicio tiene su unidad del rack con un mapa animado, sus decisiones,
sus averías reales y un enlace a su carpeta en este repositorio.

> **Nota:** esta es una versión pública y reducida del repositorio real, que
> vive en mi Forgejo. Las funciones solo tienen el nombre y una descripción de
> lo que hacen. Las IPs son de los rangos de documentación (`192.0.2.0/24`,
> `198.51.100.0/24`, `203.0.113.0/24`) y los dominios son `example.*`. Las
> listas de orígenes del firewall y todos los secretos se han quitado. No se
> puede desplegar tal cual. Cómo se genera: [más abajo](#cómo-se-publica-esta-copia).

## Estructura

```
.forgejo/workflows/     CI, plan y despliegue con aprobación, deriva nocturna,
                        Renovate y esta copia pública
environments/homelab/   Terraform (provider bpg/proxmox): un fichero por CT o VM
ansible/
  inventory/            hosts.yml y group_vars por grupo (los secretos van en
                        vault.yml cifrado; aquí solo hay vault.yml.example)
  playbooks/            un playbook por servicio, más los de mantenimiento
  roles/                un rol por servicio
scripts/                monitorización (Zabbix/Wazuh -> Matrix) y pruebas
  despliegue/           qué playbooks toca cada cambio, plan y aplicar
  publico/              generador y control de fugas de esta copia
docs/                   descripción de las piezas más grandes
githooks/               push automatico al repositorio de respaldo
```

## Servicios

| Área | Servicios |
|---|---|
| Entrada | Traefik (público, Let's Encrypt + Cloudflare), Caddy + Authelia (red local) |
| Plataforma | Forgejo con CI/CD (los cambios entran por PR con el plan a la vista y se aplican con un clic), Renovate, OpenBao para las llaves ([docs](docs/despliegue.md)) |
| Seguridad | CrowdSec delante de Traefik con la lista comunitaria ([docs](docs/crowdsec.md)), Wazuh |
| Copias | Proxmox Backup Server: diarias, incrementales y cifradas, restauración probada ([docs](docs/copias.md)) |
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
  Renovate propone las subidas por PR y el CI las comprueba.
- Nada se aplica sin plan: cada cambio enseña antes qué va a tocar y lo
  apruebo yo. Cada noche se comprueba que lo real no se ha desviado del repo.
- Los roles gestionan la configuración; los datos están en las copias de PBS.
- Todo lo privado es accesible solo desde la red local o la VPN, detrás de
  autenticación con doble factor.
- El asistente IA funciona en local: nada sale de mi red.

## Cómo se publica esta copia

No la mantengo a mano: sale del repositorio real en cada cambio.

1. Al fusionar un cambio, un generador coge solo los ficheros de una lista
   blanca, cambia IPs y dominios, vacía las listas del firewall, deja de cada
   `vault.yml` solo los nombres de las variables y recorta las funciones.
2. Un control de fugas (gitleaks, IPs públicas y una lista de patrones
   privados) bloquea la copia si encuentra algo. El mismo control corre en el
   CI de cada PR, así que los problemas se ven antes de fusionar.
3. La copia queda como propuesta en un repositorio privado y me avisa. Si la
   apruebo, se vuelve a generar, se comprueba que es exactamente la que
   revisé y se publica aquí, sin reescribir la historia.
