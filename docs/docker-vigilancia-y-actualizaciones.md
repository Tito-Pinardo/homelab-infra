# Docker: vigilancia, avisos y actualizaciones

Objetivo: saber cada dia que contenedor tiene imagen nueva, enterarme al
momento de lo que se cae y actualizar desde Ansible, que es la fuente de
verdad de los `compose.yaml`.

## Piezas

| Pieza | Donde |
|---|---|
| Recogida del estado | `scripts/sync_monitoring_snapshot.py` (`get_docker_status`), en el host Proxmox |
| Logica de avisos | `ansible/roles/ia_asistente/files/docker_estado.py` |
| Envio a Matrix | `ia_bot.py`: resumen diario, Hefesto e Hipnos |
| Herramientas de Hermes | `ia_tools.py`: `get_hefesto_status`, `get_hipnos_status` |
| Actualizacion | `ansible/playbooks/update-containers.yml` |

## Como funciona

1. Cada pocos minutos el host genera una instantanea con el estado de los
   contenedores de cada CT (estado, salud, reinicios, imagen en uso) y, con
   una cache de varias horas, si el registro tiene una imagen mas nueva.
2. El bot lee esa instantanea y decide que avisar:
   - **Resumen diario**: contenedores caidos y numero de imagenes nuevas.
   - **Hefesto** (diario, solo si hay algo): que actualizar en cada CT.
   - **Hipnos** (al momento): caidas, recuperaciones, reinicios solos y
     contenedores desaparecidos. Un problema tiene que verse en dos pasadas
     seguidas antes de avisar, para no avisar de reinicios normales.
3. Para actualizar lanzo el playbook con los stacks que quiera; falla si
   algun contenedor no queda en marcha y sano.

Los CT que tengo aislados no se consultan.
