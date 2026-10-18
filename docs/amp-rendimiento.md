# AMP: ajustes de rendimiento para juegos (2026-10-06)

CT 121 `amp` y pool ZFS `games` del host. Nota completa (mediciones, motivos)
en Obsidian: `05 Procedimientos/AMP - Rendimiento para juegos 2026-10-06`.

Copias del estado anterior y reversión en el host:
`/root/amp-rendimiento-20261006/` (`revertir.sh`).

## Discos del pool `games` (host)

Son 4 SAS mecánicos de 2,5" (ST91000640SS) en dos mirrors. Venían con la caché
de escritura **desactivada**.

| Cambio | Cómo | Persistencia |
|---|---|---|
| Caché de escritura (WCE) activada | `sdparm --set=WCE=1 --save /dev/sdX` | Guardada en el propio disco |
| Planificador `none` (ZFS ya ordena la E/S) | `/etc/udev/rules.d/60-zfs-games-scheduler.rules` (por WWN) | udev |

Es segura con ZFS: ZFS vacía la caché del disco al cerrar cada grupo de
transacciones y en cada escritura síncrona, así que un corte de luz no deja
el pool inconsistente.

Medido con fio en un dataset temporal (sin compresión):

| Prueba | Antes | Después |
|---|---|---|
| Escritura aleatoria 16K con fsync | 108 IOPS | 946 IOPS |
| Escritura secuencial 1M | 38 MB/s | 123 MB/s |

**Si se cambia un disco del pool**, la caché del nuevo vendrá apagada: repetir
`sdparm --set=WCE=1 --save` y añadir su WWN a la regla de udev.

## ZFS

- `games/minecraft`: `compression=lz4` (antes `off`) y `dnodesize=auto`.
- `games/steam`: `dnodesize=auto`.
- Solo afecta a lo que se escriba a partir de ahora.
- `sync` se queda en `standard` y `zfs_txg_timeout` en 5 s a propósito: hay
  cortes de luz y no hay SAI.

## CPU y memoria del CT 121

- Fijado al socket 0 con una línea raw en `/etc/pve/lxc/121.conf`, que el
  provider de Terraform no gestiona:
  `lxc.cgroup2.cpuset.cpus: 0,2,4,6,8,10,24,26,28,30,32,34`.
  Antes Proxmox le daba 12 hilos sueltos de los dos sockets y Java tenía la
  memoria en un nodo y los hilos en el otro. pvestatd no reequilibra los CT
  con esa línea.
- La memoria no se ata (`cpuset.mems` libre): Java la reserva en el nodo 0
  por localidad y, si un día falta, puede usar el nodo 1 en vez de fallar.
- RAM 24 → 32 GB (`lxc-amp.tf`).
- Páginas grandes para memoria compartida en modo `advise` en el host
  (`/etc/tmpfiles.d/thp-shmem-advise.conf`), necesario para que el heap de
  ZGC use páginas grandes.

## Instancias (configuración de AMP, `MinecraftModule.kvp`)

David01 (NeoForge 1.21.1):

- `Java.MinHeapSizeMB` 2048 → 20480 (Xms = Xmx).
- `Java.CustomOpts`: fuera `-XX:+ZGenerational` (Java 25 lo ignora) y
  `-XX:ZCollectionInterval=5` (limpieza forzada cada 5 s) y
  `ZUncommitDelay`; añadidos `-XX:+AlwaysPreTouch -XX:+UseTransparentHugePages`.
- `Minecraft.NetworkCompressionThreshold` 512 → -1: Velocity ya comprime hacia
  los jugadores, el backend no necesita comprimir otra vez.

velocity01: fuera `-Dvelocity.packet-decode-logging=true` (depuración).

Editar estos ficheros solo con la instancia parada (`ampinstmgr -q <nombre>`),
porque AMP los reescribe.

## Actualizar AMP sin sorpresas

Al actualizar Docker dentro del CT se reinicia el servicio y se paran todos
los `AMP_*`. `ampinstmgr --UpgradeAll true` solo reinicia lo que ya estaba
encendido, y al reiniciarse ADS01 enciende las instancias con «Start on Boot»
(redstone01 lo tiene). Después de actualizar, comprobar con `ampinstmgr -t`
y dejar encendidas solo David01 y velocity01. Última actualización:
2026-10-06, a 2.8.0.8.
