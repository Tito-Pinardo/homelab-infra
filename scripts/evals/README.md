# Evaluacion de Hermes y Demeter

Aqui estan las pruebas del asistente y de Demeter.

- `test_*.py`: pruebas unitarias con datos sinteticos y bases temporales. No
  consultan cuentas reales ni envian mensajes.
- `hermes_eval.py`: bateria de preguntas contra el modelo local, con
  criterios automaticos por respuesta.
- `smoke_tools.py`: ejecuta una vez cada herramienta de lectura contra
  produccion y comprueba que responde.
- `preguntas_reales.py`: preguntas con respuesta conocida contra produccion.
- `resiliencia.py`: simula caidas de dependencias y comprueba que el
  asistente lo dice en vez de inventar.
- `comprobar_produccion.sh`: encadena las dos comprobaciones contra
  produccion y sale con error si alguna falla.
