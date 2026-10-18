# OpenBao: llaves maestras de infra-tf (CT 128)

> Guía de uso: wiki del repo, <https://git.home.arpa/tito/infra-tf/wiki>. Esto es el detalle técnico.

Montado el 2026-10-15. Las dos llaves maestras de infra-tf salen del disco del
CT 123 y pasan a OpenBao (versión libre de HashiCorp Vault):

- la **contraseña del vault de Ansible** (`infra-tf/ansible`, campo `vault_password`)
- las **credenciales de Terraform** (`infra-tf/terraform`, una entrada por `TF_VAR_*`)

Los `vault.yml` del repo siguen igual (cifrados con esa contraseña). Llevarlos
a OpenBao uno a uno es una segunda fase.

```
CT 123 (agent) ── AppRole 'despliegue' (solo lectura, tokens de 15 min,
   │               ligado a la IP del CT 123) ──► OpenBao CT 128 :8200 (TLS propio)
   ├─ ~/.vault-pass-infra-tf  (script: Ansible lo ejecuta y usa lo que imprime)
   ├─ ~/.local/bin/tf         (terraform con TF_VAR_* de OpenBao)
   └─ despliegue.py           (igual, antes de cada plan/aplicar)
```

## Desellado (a mano, decisión de Tito)

OpenBao arranca **sellado** tras cada reinicio del CT o del host: hasta
desellarlo no da secretos, así que no hay despliegues ni playbooks. La clave de
desellado no está en ningún disco del servidor: solo en el gestor de
contraseñas de Tito.

- Aviso en Element «🔒 OpenBao está sellado» (cron `openbao-vigilar` del CT 123,
  cada 10 min) y «🔓 vuelve a estar desellado».
- Desellar: **`https://bao.home.arpa`** (Caddy + Authelia, solo LAN/VPN) → pegar la
  clave. Si Caddy no respondiera, directo en `https://192.0.2.234:8200` (desde
  lucifer o la VPN; el navegador avisa del certificado propio). O por CLI:
  `bao operator unseal` con `BAO_ADDR=https://192.0.2.234:8200`.

## Piezas

| Pieza | Dónde |
|---|---|
| CT 128 `openbao`, 192.0.2.234, 1 vCPU, 512 MB, 8 GB | `environments/homelab/lxc-openbao.tf` |
| Paquete oficial, TLS, configuración (raft), firewall `policy_in: DROP` | `ansible/roles/openbao/` |
| Cliente del CT 123 (`bao`, `infra-tf-secreto`, `tf`, vigilancia) | `roles/openbao/tasks/cliente.yml` |
| Configuración inicial (auditoría, KV, políticas, AppRole, usuario `tito`) | `scripts/openbao/configurar.sh` |
| `bao.home.arpa` en el Caddy de dockge (el certificado lo copia este playbook) | `roles/arr_stack/templates/Caddyfile.j2`, `playbooks/openbao.yml` |
| Playbook (a mano: reiniciar OpenBao lo sella) | `ansible/playbooks/openbao.yml` |
| Copia diaria | En la de PBS con el resto de CT ([copias.md](copias.md)); los datos ya van cifrados por OpenBao |

En el CT 123, `~/.infra-tf/openbao/` (0700): `ca.pem` (el certificado de
OpenBao, fijado), `role_id`, `secret_id`, `token.json` (token de 15 min en caché).

## Uso diario

- Ansible: igual que siempre.
- Terraform a mano en el CT 123: **`tf`** en vez de `terraform` (`tf plan`,
  `tf apply`…). Sin `tf`, Terraform pide `proxmox_api_token`.
- Un secreto suelto: `infra-tf-secreto terraform --json` o
  `infra-tf-secreto ansible vault_password`.
- Web de OpenBao: usuario `tito` (userpass), política `admin`. Auditoría en el CT:
  `/var/log/openbao/audit.log`.

## Puesta en marcha (una vez)

```sh
ansible-playbook playbooks/openbao.yml          # instala; OpenBao queda sin inicializar
BAO_ADDR=https://192.0.2.234:8200 BAO_CACERT=~/.infra-tf/openbao/ca.pem \
  bao operator init -key-shares=1 -key-threshold=1 -format=json   # clave y token root
bao operator unseal                             # con esa clave
BAO_TOKEN=<root> TITO_PASSWORD=<…> scripts/openbao/configurar.sh
ansible-playbook playbooks/openbao.yml          # activa ~/.vault-pass-infra-tf contra OpenBao
bao token revoke <root>                         # el root no se guarda en ningún sitio
```

Si algún día hace falta un token root: `bao operator generate-root` con la clave
de desellado.

## Contraseña del vault de Ansible (histórico)

Desde el 18-10 no queda ningún `vault.yml`: los secretos de Ansible están en
OpenBao (`infra-tf/grupos/<grupo>`, [secretos.md](secretos.md)) y Ansible ya no
pide contraseña. La del vault sigue en `infra-tf/ansible` solo para leer los
`vault.yml` de la historia de git:
`ansible-vault view --vault-password-file <(infra-tf-secreto ansible vault_password) <fichero>`.
El rekey del 15-10 (PR #31) ya no aplica; `rekey-vault.py` se retiró.

## Recuperar el acceso de administrador

No hay token root guardado ni hace falta: se genera uno temporal con la clave
de desbloqueo. OpenBao 2.x trae cerrados los endpoints sin autenticar de
`generate-root`, así que hay que abrirlos un momento (hecho el 15-10 para
cambiar la contraseña de `tito` y la del vault):

1. En el CT 128, copia de `/etc/openbao/openbao.hcl` y añadir en el bloque
   `listener` la línea `disable_unauthed_generate_root_endpoints = false`;
   `systemctl restart openbao` y desellar.
2. `bao operator generate-root -init`, `bao operator generate-root` (pide la
   clave) y `bao operator generate-root -decode=… -otp=…` → token root.
3. El cambio que haga falta, por ejemplo
   `bao write auth/userpass/users/tito/password password=-` (la contraseña por
   la entrada estándar).
4. `bao token revoke -self`.
5. Restaurar la configuración, reiniciar y desellar. Comprobar que
   `/v1/sys/generate-root/attempt` vuelve a dar 405 y que
   `ansible-playbook playbooks/openbao.yml --check --limit openbao` sale a 0.

## Si algo va mal

- **«OpenBao está SELLADO»**: desellar (arriba).
- **«OpenBao no responde»**: CT 128 caído (`pct start 128` en el host) o red.
- **OpenBao perdido del todo**: restaurar el CT de la copia de lb2 (los datos
  van cifrados y se desellan con la misma clave). Sin copia ni clave: la
  contraseña del vault y el token de Proxmox están también en el gestor de
  contraseñas de Tito (copia de emergencia); volver a ponerlos en ficheros y
  `configurar.sh` de nuevo.
- **Cambiar el `secret_id`** del CT 123: con un token admin,
  `bao write -f -field=secret_id auth/approle/role/despliegue/secret-id > ~/.infra-tf/openbao/secret_id`
  y revocar el anterior.

## Desde el 18-10

- **Inicio de sesión con Authelia** (método `oidc`, rol `admins`): en
  `https://bao.home.arpa` elegir *OIDC* → *Sign in with OIDC Provider*. Solo el
  grupo `admins` de Authelia; política `admin`, 1 h. Detalle en
  [sso.md](sso.md). El usuario `tito` (contraseña) sigue funcionando.
- **AppRole `secretos`**: escribe los secretos de Ansible
  (`infra-tf/grupos/*`) desde el CT 123 ([secretos.md](secretos.md)).
- La política `admin` incluye `patch` (antes OpenBao avisaba al actualizar
  un secreto con `kv patch`).
