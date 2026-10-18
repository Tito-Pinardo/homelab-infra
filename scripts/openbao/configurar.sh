#!/bin/sh
# Configuracion inicial de OpenBao (CT 128), una sola vez, desde el CT 123 con
# el token root en BAO_TOKEN (sale de 'bao operator init'; revocarlo al
# terminar). Idempotente: se puede repetir. Ver docs/openbao.md.
#
#   (la auditoria va en la configuracion: roles/openbao/templates/openbao.hcl.j2)
#   - KV v2 en infra-tf/ con ansible (vault_password) y terraform (sus TF_VAR)
#   - politica 'despliegue' (solo lectura de infra-tf/) y AppRole 'despliegue'
#     ligado a la IP del CT 123, tokens de 15 min
#   - politica 'admin' y usuario 'tito' (userpass) para la web
#   - deja role_id y secret_id en ~/.infra-tf/openbao/ (0600)
#
# Los secretos van por la entrada estandar (nunca como argumento: se verian
# en la lista de procesos). Los lee de los ficheros de siempre (~/.vault-pass-infra-tf y
# ~/.infra-tf/homelab.tfvars) solo si aun son ficheros normales.
set -eu
export BAO_ADDR="${BAO_ADDR:-https://192.0.2.234:8200}"
export BAO_CACERT="$HOME/.infra-tf/openbao/ca.pem"
: "${BAO_TOKEN:?falta BAO_TOKEN (token root de bao operator init)}"
: "${TITO_PASSWORD:?falta TITO_PASSWORD (contraseña de tito para la web)}"
D="$HOME/.infra-tf/openbao"

bao secrets list | grep -q '^infra-tf/' || bao secrets enable -path=infra-tf kv-v2

bao policy write despliegue - <<'POL'
path "infra-tf/data/*" { capabilities = ["read"] }
POL
bao policy write admin - <<'POL'
path "*" { capabilities = ["create", "read", "update", "patch", "delete", "list", "sudo"] }
POL

bao auth list | grep -q '^approle/' || bao auth enable approle
bao write auth/approle/role/despliegue \
  token_policies=despliegue token_ttl=15m token_max_ttl=1h \
  secret_id_bound_cidrs=192.0.2.237/32 token_bound_cidrs=192.0.2.237/32
umask 077
bao read -field=role_id auth/approle/role/despliegue/role-id > "$D/role_id"
[ -s "$D/secret_id" ] || bao write -f -field=secret_id auth/approle/role/despliegue/secret-id > "$D/secret_id"

bao auth list | grep -q '^userpass/' || bao auth enable userpass
printf %s "$TITO_PASSWORD" | bao write auth/userpass/users/tito password=- token_policies=admin token_ttl=1h

if [ -f "$HOME/.vault-pass-infra-tf" ] && [ ! -x "$HOME/.vault-pass-infra-tf" ]; then
  bao kv put -mount=infra-tf ansible vault_password=- < "$HOME/.vault-pass-infra-tf"
fi
if [ -f "$HOME/.infra-tf/homelab.tfvars" ]; then
  token=$(sed -n 's/^proxmox_api_token *= *"\(.*\)"$/\1/p' "$HOME/.infra-tf/homelab.tfvars")
  [ -n "$token" ] && printf %s "$token" | bao kv put -mount=infra-tf terraform proxmox_api_token=-
fi
echo "OpenBao configurado. Comprobar: ~/.local/bin/infra-tf-secreto terraform --json >/dev/null && echo ok"
