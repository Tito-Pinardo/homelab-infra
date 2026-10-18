# CA de casa (OpenBao PKI)

> Guía de uso: wiki del repo, página **CA de casa**. Esto es el detalle técnico.

Montada el 2026-10-15. Una sola autoridad para todos los `*.home.arpa`, en
OpenBao (CT 128), con ACME: Caddy pide y renueva sus certificados solo.
Sustituye a la CA interna de Caddy (`local_certs`): Caddy la usa desde el
mismo 15-10 (`caddy_ca_casa: true`), los 27 sitios. Los servidores siguen
fiándose también de la raíz vieja de Caddy (rol `ca_casa`), por si vuelve.

```
pki/      Casa Root CA       EC P-384, hasta 2036. Solo firma la intermedia.
pki_int/  Casa Intermediate  EC P-256, hasta 2031. Firma los de *.home.arpa.
          rol home-lan       subdominios de home.lan, 90 días como máximo
          ACME               https://192.0.2.234:8200/v1/pki_int/acme/directory
```

Huella SHA-256 de la raíz:
`DF:EB:18:CE:68:7A:7E:CF:7E:A5:85:ED:CC:D6:FA:BB:39:B8:FE:59:E7:45:B6:A6:2D:9B:9C:B9:D9:59:C2:39`

## Piezas

| Pieza | Dónde |
|---|---|
| Montar la PKI (una vez, token admin) | `scripts/openbao/configurar-pki.sh` |
| Raíz en todos los CT y el host (Paperless no) | rol `ca_casa`, `playbooks/ca-casa.yml` (a mano) |
| Caddy por ACME | `caddy_ca_casa` en `group_vars/all/ca.yml`; `roles/arr_stack/templates/Caddyfile.j2` y `demeter.caddy.j2` |
| La raíz (pública) | `ansible/roles/ca_casa/files/casa-raiz.crt`, `~/.infra-tf/openbao/casa-raiz.pem` |

- ACME sin EAB: solo hablan con la API de OpenBao las IPs de
  `openbao_origenes_api` (firewall del CT 128).
- Validación HTTP-01: OpenBao resuelve `x.home.arpa` (Technitium → Caddy) y
  entra al puerto 80 de Caddy.
- Caddy habla con la API de OpenBao por HTTPS fiándose de la CA del listener
  (`acme_ca_root`, la misma que usa para `bao.home.arpa`).
- Limpieza automática de certificados caducados (`auto-tidy`, cada día).

## Al cambiar una raíz

Los procesos de larga duración leen las raíces al arrancar: tras instalar una
raíz nueva siguen rechazándola hasta reiniciarlos. El rol `ca_casa` reinicia lo
que hay en `ca_casa_reiniciar` de cada host (runner del CI, Forgejo, Proxmox,
PBS). Lo aprendido el 15-10: al pasar Caddy a la CA de casa, el runner del CI
(CT 127, habla con `https://git.home.arpa`) dejó de coger trabajos con
`x509: certificate signed by unknown authority` hasta reiniciarlo.

## Si OpenBao está sellado

No se pueden emitir ni renovar certificados. Caddy renueva cuando queda un
tercio de la vida (~30 días), así que hay margen de sobra: basta con
desellarlo. Si caducara uno, Caddy lo vuelve a pedir solo al desellar.

## Dispositivos

Cada equipo desde el que se entra a `*.home.arpa` necesita la raíz una vez
(wiki «CA de casa»). Sin ella el navegador avisa, y en los sitios con HSTS
(`books.home.arpa`) ni siquiera deja continuar.

## Cuidado al recargar Caddy

El `Caddyfile` se monta como fichero suelto: Ansible lo reemplaza (fichero
nuevo) y el contenedor sigue viendo el viejo. Nunca
`caddy reload --config /etc/caddy/Caddyfile`, que carga esa copia vieja (el
15-10 dejó caídos 3 minutos `git`, `bao` y `battlepros.home.arpa`). Siempre por
`roles/arr_stack/tasks/caddy_recargar.yml` (candidato en `/config/candidato`,
validado y recargado desde ahí).

## Emitir un certificado a mano (fuera de ACME)

```
bao write pki_int/issue/home-lan common_name=x.home.arpa key_type=ec key_bits=256 ttl=2160h
```

Con un token con la política admin. `key_type` hace falta porque el rol admite
cualquier tipo de clave (lo elige el cliente ACME en su CSR).
