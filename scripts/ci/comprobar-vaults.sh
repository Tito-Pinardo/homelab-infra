#!/bin/sh
# Comprueba que los vault*.yml del repo estan cifrados con ansible-vault, sea
# el fichero entero o cada valor por separado (!vault |, como agents y
# ia_asistente). Lo usa el CI de Forgejo (ver docs/forgejo.md): un vault
# descifrado por error llevaria las contraseñas en claro al repo.
set -eu
fallos=0
total=0
for f in $(git ls-files 'ansible/**/vault*.yml'); do
  total=$((total + 1))
  head -n1 "$f" | grep -q '^\$ANSIBLE_VAULT;' && continue
  # Cifrado por valor: toda clave de primer nivel tiene que ser !vault.
  sueltas=$(grep -E '^[A-Za-z_][A-Za-z0-9_]*:' "$f" | grep -v '!vault' || true)
  if [ -n "$sueltas" ]; then
    echo "SIN CIFRAR en $f: $(echo "$sueltas" | cut -d: -f1 | tr '\n' ' ')"
    fallos=$((fallos + 1))
  fi
done
echo "$total vault revisados, $fallos con valores sin cifrar"
[ "$fallos" -eq 0 ]
