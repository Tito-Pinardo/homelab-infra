#!/usr/bin/env python3
"""
Pone al dia las sumas SHA-256 fijadas en group_vars cuando Renovate sube una
version (postUpgradeTasks de renovate.json). Las saca del fichero de sumas
oficial de cada release, nunca de descargar y calcular a ciegas: si la
release no publica la suma de ese fichero, falla y el PR no sale.

Solo toca pares <x>_version / <x>_sha256 de la tabla de abajo, y solo si la
suma no corresponde a la version que hay escrita.
"""
import re
import sys
import urllib.request
from pathlib import Path

G = Path("ansible/inventory/group_vars")

# (fichero, variable de version, variable de suma, URL de sumas, nombre del fichero en ella)
PARES = [
    (G / "forgejo/vars.yml", "forgejo_version", "forgejo_sha256",
     "https://codeberg.org/forgejo/forgejo/releases/download/v{v}/forgejo-{v}-linux-amd64.sha256",
     "forgejo-{v}-linux-amd64"),
    (G / "forgejo_runner/vars.yml", "forgejo_runner_version", "forgejo_runner_sha256",
     "https://code.forgejo.org/forgejo/runner/releases/download/v{v}/forgejo-runner-{v}-linux-amd64.sha256",
     "forgejo-runner-{v}-linux-amd64"),
    (G / "forgejo_runner/vars.yml", "ci_terraform_version", "ci_terraform_sha256",
     "https://releases.hashicorp.com/terraform/{v}/terraform_{v}_SHA256SUMS",
     "terraform_{v}_linux_amd64.zip"),
    (G / "forgejo_runner/vars.yml", "ci_gitleaks_version", "ci_gitleaks_sha256",
     "https://github.com/gitleaks/gitleaks/releases/download/v{v}/gitleaks_{v}_checksums.txt",
     "gitleaks_{v}_linux_x64.tar.gz"),
    (G / "forgejo_runner/vars.yml", "ci_trivy_version", "ci_trivy_sha256",
     "https://github.com/aquasecurity/trivy/releases/download/v{v}/trivy_{v}_checksums.txt",
     "trivy_{v}_Linux-64bit.tar.gz"),
    (G / "forgejo_runner/vars.yml", "ci_tflint_version", "ci_tflint_sha256",
     "https://github.com/terraform-linters/tflint/releases/download/v{v}/checksums.txt",
     "tflint_linux_amd64.zip"),
    (G / "openbao/vars.yml", "openbao_version", "openbao_deb_sha256",
     "https://github.com/openbao/openbao/releases/download/v{v}/checksums.txt",
     "openbao_{v}_linux_amd64.deb"),
    (G / "openbao/vars.yml", "openbao_version", "openbao_targz_sha256",
     "https://github.com/openbao/openbao/releases/download/v{v}/checksums.txt",
     "openbao_{v}_linux_amd64.tar.gz"),
]


def leer(texto, var):
    ...


def suma_oficial(url, nombre):
    ...


def main():
    ...


if __name__ == "__main__":
    sys.exit(main())
