#!/bin/sh
# AppRole "secretos" (docs/secretos.md): escribir los secretos de Ansible
# (infra-tf/grupos/*) desde el CT 123 sin el token de tito. Solo esas rutas,
# solo desde la IP del CT 123, tokens de 15 min. Una vez, con un token admin
# en BAO_TOKEN. Idempotente. Deja role_id y secret_id en
# ~/.infra-tf/openbao/secretos-{role,secret}_id (0600).
set -eu
export BAO_ADDR="${BAO_ADDR:-https://192.0.2.234:8200}"
export BAO_CACERT="$HOME/.infra-tf/openbao/ca.pem"
: "${BAO_TOKEN:?falta BAO_TOKEN (token con la politica admin)}"
D="$HOME/.infra-tf/openbao"
bao policy write secretos-escritura - <<'POL'
# Crear, cambiar y leer los secretos de los grupos de Ansible. Nada mas.
path "infra-tf/data/grupos/*" { capabilities = ["create", "update", "patch", "read"] }
path "infra-tf/metadata/grupos/*" { capabilities = ["read"] }
POL
bao write auth/approle/role/secretos \
  token_policies=secretos-escritura token_ttl=15m token_max_ttl=30m \
  secret_id_bound_cidrs=192.0.2.237/32 token_bound_cidrs=192.0.2.237/32 >/dev/null
umask 077
bao read -field=role_id auth/approle/role/secretos/role-id > "$D/secretos-role_id"
[ -s "$D/secretos-secret_id" ] || bao write -f -field=secret_id auth/approle/role/secretos/secret-id > "$D/secretos-secret_id"
echo "AppRole secretos lista (politica secretos-escritura)"
