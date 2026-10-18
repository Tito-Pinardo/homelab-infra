# Inicio de sesión único (Authelia OIDC)

> Guía de uso: wiki del repo, página **Inicio de sesión único**. Esto es el detalle técnico.

Desde el 2026-10-15, Forgejo, Proxmox VE y PBS dejan entrar con la cuenta de
Authelia (usuario, contraseña y 2FA una sola vez por sesión). Los usuarios
locales siguen funcionando: si Authelia cae, se entra como siempre.

```
navegador ──► Forgejo / Proxmox / PBS ──► «Entrar con Authelia»
                   ▲                              │
                   │      código + token          ▼
                   └──────────────────── auth.home.arpa (Authelia, CT 122)
```

| Cliente | URL de vuelta | Usuario | Permisos |
|---|---|---|---|
| Forgejo | `https://git.home.arpa/user/oauth2/authelia/callback` | `tito`, vinculado solo | los de `tito` |
| Proxmox VE | `https://192.0.2.2:8006` | `tito@authelia` (realm *authelia*) | Administrator en `/` |
| PBS | `https://192.0.2.233:8007` | `tito@authelia` (realm *authelia*) | Admin en `/` |
| OpenBao | `https://bao.home.arpa/ui/vault/auth/oidc/oidc/callback` (y `http://localhost:8250/oidc/callback` para `bao login -method=oidc`) | rol *admins* | política `admin`, 1 h |

## Piezas

- `playbooks/sso.yml` (a mano: toca el host de Proxmox). Antes, `ca-casa.yml`
  (raíces de casa y de Caddy en los clientes) y `forgejo.yml` (`[oauth2_client]`).
- Clientes: `sso_clientes` en `group_vars/all/sso.yml`; secreto y hash de cada
  uno en `group_vars/arr_stack/vault.yml` (`vault_oidc_<cliente>_secreto` /
  `_hash`). El hash lo genera Authelia:
  `docker exec -i authelia authelia crypto hash generate pbkdf2 --variant sha512`.
- Authelia: `configuration.yml` no lo gestiona Ansible (sus secretos son de la
  instalación); el playbook mete los clientes en un bloque marcado dentro de
  `identity_providers.oidc.clients` (plantilla
  `playbooks/templates/authelia-clientes.j2`), valida con
  `authelia validate-config` y reinicia. Si no valida, deja la configuración
  anterior. `consent_mode: implicit`: no pregunta «¿autorizar?».

## Detalles de cada cliente

- **Forgejo**: `USERNAME = preferred_username` y `ACCOUNT_LINKING = auto`:
  entrar como `tito` en Authelia vincula la cuenta `tito` (Forgejo intenta
  crearla, ve que existe y la vincula; `DISABLE_REGISTRATION` no lo impide). La
  fuente exige el grupo `admins` (`--required-claim-name groups`) y salta el
  2FA local (ya lo pide Authelia).
- **Proxmox**: `username-claim username` (= `preferred_username`), sin
  autocreación. `username-claim` solo se puede poner al crear el realm.
- **PBS**: `username-claim preferred_username` (aquí es el nombre literal del
  claim), sin autocreación; tampoco se puede cambiar después. `--scopes` va
  en un solo argumento.

Proxmox y PBS validan el certificado de `auth.home.arpa`: sin la raíz (de Caddy
hoy, de casa cuando `caddy_ca_casa` sea `true`) el inicio de sesión falla.

## Comprobaciones hechas (15-10)

- Proxmox y PBS generan la URL de autorización (leen la configuración de
  Authelia por HTTPS) y Authelia la acepta (303 al login).
- Authelia rechaza una URL de vuelta no registrada (`invalid_request`) y un
  cliente que no existe (`invalid_client`).

- **OpenBao** (18-10): método `oidc` con el rol `admins`, que exige el grupo
  `admins` de Authelia (`bound_claims`) y da la política `admin` durante 1 h.
  La configuración del método la hace un token admin, a mano (no hay
  playbook): `oidc_discovery_url=https://auth.home.arpa`, `oidc_client_id=openbao`
  y la raíz de casa en `oidc_discovery_ca_pem` (OpenBao lleva arrancado desde
  antes de la raíz nueva y reiniciarlo lo sella). El secreto del cliente está
  en `grupos/arr_stack` (`vault_oidc_openbao_*`).

## Pendiente

- Cliente `outline` en Authelia: de una wiki que ya no existe; se puede borrar.
