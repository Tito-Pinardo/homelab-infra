#!/usr/bin/env python3
"""Propone y publica la copia publica de infra-tf (docs/publico.md).

Corre en el runner de despliegue (CT 123, usuario agent):

- propuesta <sha>: genera la copia de ese commit, pasa el control de fugas y
  la deja como un commit en la rama "propuesta" del repo privado
  tito/homelab-infra de Forgejo. Avisa en Element con el enlace al diff.
- publicar <sha>: vuelve a generar la copia de ese commit, comprueba que es
  la misma que la propuesta, la lleva a main y la empuja a GitHub (sin
  force push). La fusion la hace git, no Forgejo: asi el autor es el de los
  commits publicos y no la cuenta de Forgejo.

Uso: publicar.py {propuesta|publicar} <sha>
"""
import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

BASE = Path.home() / ".infra-tf" / "publico"
INFRA = BASE / "infra-tf"
STAGING = BASE / "homelab-infra"
GENERADO = BASE / "generado"
FORGEJO_SSH = "ssh://git@192.0.2.235:2222/tito"
FORGEJO_WEB = "https://git.home.arpa/tito/homelab-infra"
GITHUB = "git@github.com:Tito-Pinardo/homelab-infra.git"
GITHUB_WEB = "https://github.com/Tito-Pinardo/homelab-infra"
PY = "/home/agent/.local/share/pipx/venvs/ansible-core/bin/python"
AUTOR = {"GIT_AUTHOR_NAME": "Tito-Pinardo", "GIT_AUTHOR_EMAIL": "Tito-Pinardo@users.noreply.github.com",
         "GIT_COMMITTER_NAME": "Tito-Pinardo", "GIT_COMMITTER_EMAIL": "Tito-Pinardo@users.noreply.github.com"}


def sh(*cmd, cwd=None, check=True, env=None):
    ...


def avisar(texto):
    """Mensaje a la sala CI/CD de Element (mismo relay que el despliegue)."""
    ...


def preparar(sha):
    """Clones al dia y la copia de ese commit generada y comprobada."""
    ...


def rama_con_copia(sha):
    """Rama local "propuesta" = main + un commit con la copia generada."""
    ...


def propuesta(sha):
    ...


def publicar(sha):
    ...


if __name__ == "__main__":
    if len(sys.argv) != 3 or sys.argv[1] not in ("propuesta", "publicar"):
        sys.exit(__doc__)
    {"propuesta": propuesta, "publicar": publicar}[sys.argv[1]](sys.argv[2])
