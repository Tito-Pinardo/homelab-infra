"""Secretos de cada grupo desde OpenBao (docs/secretos.md).

Sustituye a los vault.yml de group_vars: los valores viven en OpenBao, en
infra-tf/grupos/<grupo>, y el repo solo guarda sus NOMBRES en
inventory/secretos.yml. Las variables se siguen llamando vault_* y los roles
no cambian.

Lee cada grupo una sola vez por ejecucion con infra-tf-secreto (AppRole del
CT 123, roles/openbao/tasks/cliente.yml). Si un grupo no tiene en OpenBao
todos los nombres de la lista, o OpenBao falla, se para: mejor no desplegar
que desplegar con secretos vacios. Sin infra-tf-secreto (el runner del CI,
que no tiene secretos) solo avisa y no aporta variables.
"""

DOCUMENTATION = """
    name: bao_secretos
    short_description: secretos de cada grupo desde OpenBao
    description: Variables vault_* de cada grupo leidas de OpenBao (infra-tf/grupos/<grupo>).
    extends_documentation_fragment:
      - vars_plugin_staging
"""

import json
import shutil
import subprocess
from pathlib import Path

import yaml

from ansible.errors import AnsibleError
from ansible.inventory.group import Group
from ansible.plugins.vars import BaseVarsPlugin
from ansible.utils.display import Display

MANIFIESTO = Path(__file__).resolve().parent.parent / "inventory" / "secretos.yml"
AYUDANTE = shutil.which("infra-tf-secreto") or str(Path.home() / ".local/bin/infra-tf-secreto")
display = Display()


class VarsModule(BaseVarsPlugin):
    REQUIRES_ENABLED = True
    _manifiesto = None
    _leidos = {}
    _avisado = False

    def get_vars(self, loader, path, entities, cache=True):
        ...

    def _grupo(self, grupo, nombres):
        ...
