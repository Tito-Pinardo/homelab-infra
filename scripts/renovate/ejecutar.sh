#!/bin/sh
# Lanza Renovate contra infra-tf en Forgejo (workflow renovate.yml, runner
# despliegue del CT 123). Node 24 y Renovate en ~/.infra-tf, los instala
# roles/forgejo/tasks/despliegue_agent.yml. Ver docs/renovate.md.
set -eu
B="$HOME/.infra-tf"
NODE=$(ls -d "$B"/node-v*-linux-x64 | tail -1)
RENOVATE=$(ls -d "$B"/renovate-*/node_modules/.bin/renovate | tail -1)
export PATH="$NODE/bin:$PATH"
export RENOVATE_PLATFORM=forgejo
export RENOVATE_ENDPOINT="http://192.0.2.235:3000/api/v1"
export RENOVATE_TOKEN="$(cat "$B/renovate-token")"
export RENOVATE_REPOSITORIES="tito/infra-tf"
# git por la IP del CT (el clone_url de la API es git.home.arpa, con Authelia).
export RENOVATE_GIT_URL=endpoint
export RENOVATE_GIT_AUTHOR="Renovate <renovate@git.home.arpa>"
export RENOVATE_ONBOARDING=false
export RENOVATE_REQUIRE_CONFIG="${RENOVATE_REQUIRE_CONFIG:-required}"
export RENOVATE_BASE_DIR="$B/renovate-trabajo"
export RENOVATE_ALLOWED_COMMANDS='["^python3 scripts/renovate/sumas\\.py$"]'
export LOG_LEVEL="${LOG_LEVEL:-info}"
exec "$RENOVATE" "$@"
