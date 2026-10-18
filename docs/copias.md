# Copias de seguridad (Proxmox Backup Server, CT 129)

> Guía de uso: wiki del repo, <https://git.home.arpa/tito/infra-tf/wiki>. Esto es el detalle técnico.

Montado el 2026-10-15. Hasta entonces no había copias periódicas (solo Forgejo y
OpenBao, sueltas a lb2-copias, ya retiradas).

```
host Proxmox ── 02:30 tarea "copias-diarias" (todos los invitados menos OKD) ──┐
             └─ 03:30 copia-datasets (instantánea ZFS de games/minecraft) ────┤ cifrado en el host
                                                                              ▼
                     PBS (CT 129, 192.0.2.233:8007) ── almacén "lb2" = /plex-server/lb2/pbs (USB 4,5 TB)
                        ├─ poda diaria: 7 diarias, 4 semanales, 6 mensuales
                        ├─ verificación semanal (domingo 05:00): relee y comprueba cada copia
                        ├─ prueba de restauración (domingo 08:00): restaura de verdad (ver abajo)
                        └─ recolector de basura diario
fallos ──► webhook "element" de Proxmox ──► matrix-relay ──► sala Incidencias
```

## Qué entra y qué no

| Entra | No entra (y por qué) |
|---|---|
| Todos los CT, también paperless (decisión de Tito) y los que se creen después (`--all`) | VMs de OKD 220-222: laboratorio que se reconstruye |
| Los mundos de Minecraft (`games/minecraft`), aparte: son un *bind mount* de AMP | Películas, series y libros (raiz5, lb1-lb9): decenas de TB, se vuelven a bajar |
| | Steam (`games/steam`): se vuelve a bajar |

Ojo: las copias de un CT **no incluyen sus bind mounts** (`mpN: /ruta/del/host`).
Si algún día un CT guarda algo irrecuperable en uno, añadir el dataset a
`pbs_datasets` (`group_vars/pbs/vars.yml`).

`games` es un RAID 10 (dos espejos), pero un RAID no es una copia: no protege de
un borrado, un mundo estropeado o perder los dos discos de un espejo.

## Cifrado

Las copias se cifran en el host antes de salir (`--encryption-key autogen`). La
clave está en `/etc/pve/priv/storage/pbs-lb2.enc` **y en el gestor de
contraseñas de Tito**: si el servidor muere, sin esa copia no se puede leer
nada. Quien se lleve el disco USB no puede leer las copias.

## Permisos

PBS tiene el usuario `pve@pbs` y su token `pve@pbs!pve` con el rol
**DatastoreBackup** en `/datastore/lb2` (el efectivo de un token es la
intersección del suyo y el de su usuario: los dos lo tienen). Puede hacer copias
y restaurar, **no borrar ni podar**: eso solo lo hace el propio PBS. Un host
comprometido no puede borrar las copias.

La carpeta en lb2 es de `100034` (el usuario `backup` del CT) y `0700`: Plex y
dockge también montan lb2 y no pueden ni listarla.

Si lb2 no está montado, el CT 129 no arranca (el bind mount falla) y nunca
escribe copias en el disco del sistema.

## Piezas

| Pieza | Dónde |
|---|---|
| CT 129 `pbs` | `environments/homelab/lxc-pbs.tf` |
| PBS, almacén, poda, verificación, usuario | `ansible/roles/pbs/` |
| Montaje de lb2, almacén en Proxmox, tarea, avisos, datasets | `ansible/playbooks/pbs.yml` (a mano: toca el host) |
| Script de datasets | `/usr/local/sbin/copia-datasets` (host), `copia-datasets.timer` |
| Variables | `ansible/inventory/group_vars/pbs/vars.yml` |

Interfaz de PBS: `https://192.0.2.233:8007` (desde lucifer o la VPN), usuario
`root@pam` del CT.

## Restaurar

- **Un CT entero:** en Proxmox, CT → Backup → `pbs-lb2` → la copia → Restore.
  Para probar sin pisar el original: `pct restore <id-nuevo> pbs-lb2:backup/ct/<id>/<fecha> --storage local-lvm --unique 1`
  (sin arrancarlo: tendría la misma IP).
- **Ficheros sueltos de un CT:** misma pantalla → *File Restore*.
- **Minecraft:** `proxmox-backup-client` en el host:
  `proxmox-backup-client restore host/minecraft/<fecha> minecraft.pxar /ruta/destino --keyfile /etc/pve/priv/storage/pbs-lb2.enc`
  (repositorio y contraseña como en `/usr/local/sbin/copia-datasets`).
- **Servidor nuevo:** instalar PBS, montar el disco, añadir el almacén existente
  (`proxmox-backup-manager datastore create lb2 /datastore`, coge lo que hay) y en
  Proxmox añadirlo con la clave del gestor como `/etc/pve/priv/storage/pbs-lb2.enc`.

## Prueba de restauración (semanal)

La verificación de PBS comprueba que los bloques no se han estropeado, pero
no que la copia sirva. Para eso, `restauracion.yml` (domingo 06:00 UTC, runner
de despliegue) ejecuta `scripts/copias/prueba_restauracion.py`:

- Los CT se reparten en 4 grupos de tamaño parecido (~50 GB). Cada semana se
  prueba uno, así que cada CT se restaura una vez al mes.
- Cada CT se restaura en un CT temporal `9000 + id` (`--unique`, en
  `local-lvm`, **sin arrancarlo**). Se comprueba que el sistema está y que los
  ficheros de `/etc` y `/opt` que no han cambiado desde la copia (por fecha de
  cambio del inodo, `-cmin`) son idénticos a los del CT en marcha. Después se
  borra el CT temporal; los bind mounts no se tocan.
- Minecraft: saca de la última copia solo los `level.dat` (`--pattern`) y
  comprueba que se pueden leer. Para eso la copia usa
  `--change-detection-mode metadata`: el índice va aparte (`.mpxar`) y no hay
  que leer los 160 GB.
- Paperless (CT 119) queda fuera: la prueba montaría sus ficheros.
- Resumen en la sala CI/CD; si algo falla, en Incidencias.

A mano: Actions → `restauracion.yml` → Run workflow, o en el CT 123:
`prueba_restauracion.py --ct 110 126` (CT concretos) o `--grupo N`.

Primera prueba (15-10): Element y Forgejo restaurados en 2,3 y 1,5 min, con
1.622 y 251 ficheros idénticos al original.

## Avisos

Fallos: webhook `element` de Proxmox y regla `errores-a-element` (severidad
error), a la sala Incidencias. Los fallos de `copia-datasets` avisan desde el
propio script. La prueba de restauración manda su resumen semanal a CI/CD. Probar: `pvesh create /cluster/notifications/targets/element/test`.

## Limitaciones

- Todo está en el mismo sitio: el disco USB está en casa y enchufado al mismo
  servidor. Protege de borrados, corrupción y fallos de disco del servidor, no de
  un incendio o un robo. Siguiente paso posible: una copia fuera (otro disco que
  se rota, o un PBS remoto).
