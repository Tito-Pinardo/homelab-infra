#!/bin/sh
# Las dos comprobaciones que SI ven produccion, encadenadas. La bateria del
# modelo usa resultados sinteticos y no detecta ni una tool caida ni una
# respuesta equivocada: el 2026-09-22 Demeter llevaba 13 horas sin responder
# y nadie se entero.
#
#   sh scripts/evals/comprobar_produccion.sh
#
# Sale con 1 si algo falla, para poder encadenarlo tras un despliegue.
CT="${CT_ASISTENTE:-root@192.0.2.247}"
RAIZ="$(dirname "$0")"
estado=0

echo "== Tools de lectura contra produccion"
ssh -o BatchMode=yes "$CT" 'python3 -' < "$RAIZ/smoke_tools.py" || estado=1

echo
echo "== Preguntas reales con respuesta conocida"
# Sin tuberia directa: en `ssh ... | grep` el estado que cuenta es el de
# grep, asi que 2 preguntas mal daban exit=0 (2026-09-23). Se guarda la
# salida, se mira el estado de Python y despues se filtra para leerla.
salida="$(mktemp)"
ssh -o BatchMode=yes "$CT" 'python3 -' < "$RAIZ/preguntas_reales.py" > "$salida" 2>&1 || estado=1
grep -v '^\[llm\]\|^\[tool-loop\]' "$salida"
rm -f "$salida"

exit $estado
