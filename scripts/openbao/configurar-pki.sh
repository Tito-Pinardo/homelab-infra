#!/bin/sh
# CA interna de casa en OpenBao (docs/ca-casa.md), una vez, desde el CT 123
# con un token con la politica admin en BAO_TOKEN (el de tito en la web:
# menu de usuario -> Copy token). Idempotente: se puede repetir.
#
#   - pki/      raiz "Casa Root CA", 10 anos (solo firma la intermedia)
#   - pki_int/  intermedia, 5 anos: firma los certificados de *.home.arpa
#   - rol home-lan: subdominios de home.lan, 90 dias como maximo
#   - ACME en pki_int/ sin EAB (solo llega la LAN: el firewall del CT 128
#     limita quien habla con la API)
#   - deja la raiz en ~/.infra-tf/openbao/casa-raiz.pem
set -eu
export BAO_ADDR="${BAO_ADDR:-https://192.0.2.234:8200}"
export BAO_CACERT="$HOME/.infra-tf/openbao/ca.pem"
: "${BAO_TOKEN:?falta BAO_TOKEN (token con la politica admin)}"
D="$HOME/.infra-tf/openbao"
DIRECTA="$BAO_ADDR"                 # lo que usan los clientes ACME de la LAN
PUBLICA="https://bao.home.arpa"      # AIA/CRL en los certificados (por Caddy)

# --- raiz
bao secrets list | grep -q '^pki/' || bao secrets enable -path=pki -max-lease-ttl=87600h pki
if [ -z "$(bao read -field=certificate pki/cert/ca 2>/dev/null || true)" ]; then
  bao write -field=certificate pki/root/generate/internal \
    common_name="Casa Root CA" organization="Casa" key_type=ec key_bits=384 \
    ttl=87600h issuer_name=casa-raiz >/dev/null
fi
bao write pki/config/urls \
  issuing_certificates="$PUBLICA/v1/pki/ca" crl_distribution_points="$PUBLICA/v1/pki/crl" >/dev/null

# --- intermedia
bao secrets list | grep -q '^pki_int/' || bao secrets enable -path=pki_int -max-lease-ttl=43800h pki
if [ -z "$(bao read -field=certificate pki_int/cert/ca 2>/dev/null || true)" ]; then
  csr=$(bao write -field=csr pki_int/intermediate/generate/internal \
    common_name="Casa Intermediate CA" organization="Casa" key_type=ec key_bits=256)
  firmado=$(printf '%s' "$csr" | bao write -field=certificate pki/root/sign-intermediate \
    csr=- format=pem_bundle ttl=43800h)
  printf '%s' "$firmado" | bao write pki_int/intermediate/set-signed certificate=- >/dev/null
fi
bao write pki_int/config/urls \
  issuing_certificates="$PUBLICA/v1/pki_int/ca" crl_distribution_points="$PUBLICA/v1/pki_int/crl" >/dev/null

# --- rol y ACME
bao write pki_int/roles/home-lan \
  allowed_domains=home.lan allow_subdomains=true allow_bare_domains=false \
  allow_ip_sans=false key_type=any max_ttl=2160h ttl=2160h no_store=false >/dev/null
bao write pki_int/config/cluster path="$DIRECTA/v1/pki_int" aia_path="$PUBLICA/v1/pki_int" >/dev/null
bao secrets tune \
  -passthrough-request-headers=If-Modified-Since \
  -allowed-response-headers=Last-Modified -allowed-response-headers=Location \
  -allowed-response-headers=Replay-Nonce -allowed-response-headers=Link \
  pki_int >/dev/null
bao write pki_int/config/acme enabled=true allowed_roles=home-lan \
  default_directory_policy=role:home-lan eab_policy=not-required >/dev/null
# Limpieza automatica de certificados caducados.
bao write pki_int/config/auto-tidy enabled=true tidy_cert_store=true tidy_revoked_certs=true \
  safety_buffer=72h interval_duration=24h >/dev/null

bao read -field=certificate pki/cert/ca > "$D/casa-raiz.pem"
chmod 0644 "$D/casa-raiz.pem"
echo "Raiz: $D/casa-raiz.pem"
openssl x509 -in "$D/casa-raiz.pem" -noout -subject -enddate -fingerprint -sha256
echo "ACME: $DIRECTA/v1/pki_int/acme/directory"
