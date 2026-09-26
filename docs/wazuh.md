# Wazuh

Uso Wazuh como SIEM del homelab: manager, indexer y panel en un solo CT. El
manager lo instale a mano; los agentes de cada CT los despliega
`roles/monitoring` (`playbooks/monitoring.yml`) y las altas se hacen con
`scripts/register_monitoring.py`.

## Que tengo configurado

- Un agente por CT, con una politica SCA propia que revisa lo esencial
  (cuentas, permisos de ficheros sensibles, SSH y la configuracion del propio
  agente) usando `casa-seguridad-check.py`.
- Vigilancia de integridad de ficheros (FIM) en los directorios de
  configuracion de cada servicio.
- Reglas locales para bajar el nivel de avisos conocidos y ruidosos.
- Alertas de nivel alto a Matrix (`scripts/custom-matrix`) y un resumen por
  gravedad a Discord. Solo se envia la descripcion, el equipo, el nivel y la
  regla, nunca el log.
- Retencion de indices limitada con una politica ISM.

La revision de seguridad y su estado real los llevo fuera del repositorio.
