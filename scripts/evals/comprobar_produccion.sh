#!/bin/sh
# Encadena las dos comprobaciones que si miran produccion. La bateria del
# modelo usa resultados sinteticos y no detecta una herramienta caida ni una
# respuesta equivocada.
#
#   sh scripts/evals/comprobar_produccion.sh
#
# Sale con 1 si algo falla, para poder encadenarlo tras un despliegue.
CT="${CT_ASISTENTE:-root@192.0.2.27}"
RAIZ="$(dirname "$0")"
estado=0

echo "== Tools de lectura contra produccion"
ssh -o BatchMode=yes "$CT" 'python3 -' < "$RAIZ/smoke_tools.py" || estado=1

echo
echo "== Preguntas reales con respuesta conocida"
# Sin tuberia directa: con `ssh ... | grep` el estado que cuenta seria el de
# grep. Guardo la salida, miro el estado de Python y despues filtro.
salida="$(mktemp)"
ssh -o BatchMode=yes "$CT" 'python3 -' < "$RAIZ/preguntas_reales.py" > "$salida" 2>&1 || estado=1
grep -v '^\[llm\]\|^\[tool-loop\]' "$salida"
rm -f "$salida"

exit $estado
