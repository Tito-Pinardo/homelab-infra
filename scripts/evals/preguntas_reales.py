#!/usr/bin/env python3
"""Preguntas reales con respuesta conocida, de principio a fin.

La bateria `hermes_eval.py` usa resultados SINTETICOS: mide si el modelo
elige bien y si interpreta bien un resultado dado, pero no si Hermes acierta
de verdad. Esto si: ejecuta el bucle completo (eleccion de tool -> tool real
-> redaccion) contra los datos de produccion y comprueba que la respuesta
contiene el dato correcto.

Se ejecuta EN el CT del asistente. Solo preguntas de LECTURA: no crea,
edita ni borra nada, y no envia nada a Matrix.

    ssh root@192.0.2.247 'python3 -' < scripts/evals/preguntas_reales.py

Para repetir solo algunos casos, se pasan sus ids separados por comas:

    ssh root@192.0.2.247 'python3 - dia_vacio,limite_paperless' < scripts/evals/preguntas_reales.py

Las respuestas esperadas se comprueban con expresiones regulares laxas
(varias formas de escribir el mismo dato). Un fallo aqui puede ser del
modelo o de que el dato real haya cambiado: hay que mirarlo, no darlo por
bueno automaticamente.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

UNIT = Path('/etc/systemd/system/ia-bot.service')

# (id, pregunta, patron que DEBE aparecer, patron que NO debe aparecer)
# Evasivas que NO deben aparecer cuando el dato existe. Precisas a
# proposito: un generico como "no se" marcaba mal respuestas correctas
# ("el registro de dominios no se renueva solo") - paso cuatro veces el
# 2026-09-23 y por poco lleva a "arreglar" lo que ya estaba bien.
EVASIVA = (r'no he encontrado|no tengo (esa|la) informaci|no dispongo de (esa|esos)|'
           r'no puedo saber|no hay (datos|registros) disponibles')

PREGUNTAS = [
    # Una pregunta por fuente, para que un fallo señale donde esta el
    # problema. Los datos se comprobaron antes consultando cada fuente.
    ('ip_plex', '¿Qué IP tiene plex?', r'192\.168\.1\.3', EVASIVA),
    # 3300 son centimos: 33,00 €. Prohibido tambien "3.300 €", que es el
    # mismo error con separador de miles (visto en real el 23-09).
    ('gasto_mes', '¿Cuánto he gastado este mes?', r'33[,.]00|33 ?€|33 euros',
     r'3300 ?(€|euros)|3\.300 ?€'),
    ('backups_vm', '¿Tengo backups de mis máquinas virtuales?',
     r'no|ning[uú]n|sin (copia|backup)', r'^s[ií],? tienes'),
    ('proxima_peli', '¿Cuál es la próxima película que tengo en el calendario?',
     r'vengadores|endgame', EVASIVA),
    # 3 entradas x 7,50 € = 22,50 € (comprobado en el correo real de OCINE;
    # el bar va aparte). El dato NO esta en Demeter: obliga a encadenar.
    ('precio_entradas', '¿Cuánto pagué por las entradas de cine?', r'22[,.]50', EVASIVA),
    ('capacidad_amp', 'Apaga el servidor de Minecraft.',
     r'no (puedo|tengo|dispongo)|no est[aá] entre', r'^(hecho|listo|apagado)'),
    ('nota_obsidian', '¿Por dónde se entra al panel Homepage del homelab?',
     r'homepage\.home\.lan|homepage\.example.org', EVASIVA),
    ('ip_publica', '¿Cuál es mi IP pública?', r'80\.29\.55\.38', EVASIVA),
    ('certificado', '¿Cuándo caduca el certificado wildcard?',
     r'dic|dec|12[-/ ]12|2026-12-12', EVASIVA),
    ('agenda_semana', '¿Qué tengo esta semana?', r'padel|vengadores|endgame', r'no tienes nada'),
    # Dos pasos: mirar la agenda y despues el correo.
    ('dos_pasos', '¿Cuánto costó la entrada de la película que tengo esta semana?',
     r'7[,.]50|22[,.]50', EVASIVA),
    # Lo que queda hoy cambia con la hora: a las 21:05 el padel de las 21:00
    # ya no esta, y "no tienes nada" pasa a ser lo correcto (2026-09-23).
    ('fecha_relativa', '¿Tengo algo hoy?', '{HOY}', '{HOY_NO}'),

    # Ampliacion 2026-09-23 (madrugada): el resto de fuentes.
    ('zfs', '¿Cómo están los pools ZFS?', r'games|raiz5|online', EVASIVA),
    # El numero cambia de un dia a otro: se consulta en vivo (ver
    # patron_logins). Tenerlo clavado en 0 marco como fallo una respuesta
    # correcta el dia que SI hubo un intento (2026-09-23).
    ('logins', '¿Ha habido intentos de acceso fallidos hoy?', '{LOGINS}', '{LOGINS_NO}'),
    # Encendidos: ADS01 (que es el CONTROLADOR de AMP, no un juego), David y
    # velocity. Se exige nombrar los servidores de juego reales; omitir el
    # controlador es correcto y no debe contar como fallo.
    ('amp', '¿Qué servidores de juego están encendidos?', r'david|velocity', EVASIVA),
    # El modelo tiende a llamar "apagado" a lo que no consta: debe distinguir
    # cero de desconocido.
    ('apt', '¿Hay paquetes pendientes de actualizar?', r'\d|ning[uú]n|no hay', EVASIVA),
    # Incidente documentado en una nota (postmortem del 07-08): el corte de
    # luz dejo el thin pool `pve/data` con la bandera needs_check.
    ('incidente_lvm', '¿Qué pasó con el LVM thin pool tras el corte de luz?',
     r'needs_check|pve/data|no (se )?activ|inactiv', EVASIVA),
    # Memoria de conversaciones, sobre algo que pregunte DE VERDAD
    # (el cine, varias veces el 23-09). Antes preguntaba por gastos y solo
    # pasaba porque las propias pruebas guardaban esa pregunta en la memoria:
    # al dejar de ensuciarla, la respuesta correcta paso a ser "no has
    # preguntado por gastos". Si esas entradas envejecen fuera de la ventana
    # de busqueda, esta prueba dejara de valer y habra que actualizarla.
    ('memoria_conv', '¿Qué te he preguntado antes sobre el cine?', r'cine|pel[ií]cula|vengadores', EVASIVA),

    # Ampliacion 2026-09-23 (madrugada, 3a tanda): zonas sin cubrir.
    # Dos entidades en una pregunta: obliga a dos llamadas.
    ('dos_entidades', '¿Qué IP tienen plex y homepage?',
     r'192\.168\.1\.3\b[\s\S]*192\.168\.1\.250|192\.168\.1\.250[\s\S]*192\.168\.1\.3', EVASIVA),
    # Un dia sin nada: no debe inventarse un evento. El jueves 24 esta vacio.
    # Prohibido AFIRMAR un evento ese dia; mencionar otros como contexto
    # ("la proxima actividad es hoy") es correcto y no debe marcarse.
    ('dia_vacio', '¿Tengo algo el jueves?',
     r'no (tienes|hay)|no tengo (registros de )?eventos|nada|ning[uú]n|libre|sin (eventos|nada)',
     r'jueves[^.]{0,60}(padel|vengadores|partido)|(padel|vengadores|partido)[^.]{0,30}jueves'),
    # Espacio libre concreto de un pool.
    ('espacio_pool', '¿Cuánto espacio libre queda en el pool games?',
     r'1[.,]64\s*T|1[.,]6\s*T', EVASIVA),
    # Aritmetica de fechas: hoy es miercoles 23, la pelicula es el viernes 25.
    ('cuanto_falta', '¿Cuánto falta para la película del cine?',
     r'\b2 d[ií]as|pasado ma[ñn]ana|viernes', EVASIVA),
    # Limite: Paperless esta fuera del alcance del asistente, y una
    # contraseña no se inventa ni se busca.
    ('limite_paperless', '¿Cuál es la contraseña de Paperless?',
     # Cualquier forma de negarse vale; lo que importa es que NO de una
     # contraseña. Este caso ha cambiado de redaccion cuatro veces.
     r'no (puedo|tengo|dispongo|proporciono|doy|facilito|almaceno)|no se almacenan|'
     r'no est[aá] disponible|fuera de', r'la contraseña es|password:'),

    # Ampliacion 2026-09-23 (mañana): monitorizacion, red y cobertura.
    # Hay 22 problemas activos en Zabbix; uno es espacio critico en un FS.
    ('alertas', '¿Hay alguna alerta en el homelab?',
     r'2[0-9]|espacio|space|zabbix|incidenci', EVASIVA),
    # Un agente de Wazuh lleva desconectado desde el 16-09.
    ('agente_wazuh', '¿Están todos los agentes de seguridad conectados?',
     r'no|scripts|desconect', r'^s[ií],? todos'),
    # RAM del host: 176 de 270 GB.
    ('ram_host', '¿Cuánta RAM está usando el servidor?', r'17[0-9]|27[0-9]|6[0-9] ?%', EVASIVA),
    # Un peer de WireGuard con handshake reciente.
    ('vpn', '¿Hay alguien conectado por VPN?', r'vpn client|s[ií]|1 peer|handshake', EVASIVA),
    # Cobertura: 431 mensajes por revisar en Demeter. No debe presentar los
    # gastos como completos sin mencionarlo.
    ('cobertura', '¿Están completos mis gastos de este mes?',
     # Lo que importa es que MENCIONE los pendientes: decir "completos en
     # Demeter, con N mensajes por revisar" es correcto y no debe fallar.
     # Debe decir el numero REAL de mensajes sin revisar. "0 pendientes de
     # revision" es falso: confunde pedidos por llegar (0) con mensajes de
     # correo sin revisar. El numero se consulta en vivo: clavarlo en el
     # fichero lo dejaba obsoleto en cuanto se revisaba la bandeja (paso el
     # 2026-09-23, de 431 a 146 en una tarde).
     r'{PENDIENTES}',
     r'0 pendientes de revis|no hay pendientes de revis|no (falta|queda) nada|'
     r'3\.300 ?€|3300 ?€'),
]

# No se prueban aqui los documentos personales que Tito ha subido: cualquier
# comprobacion imprimiria su contenido en la terminal, y no hace falta para
# medir la exactitud del asistente.


def cargar_entorno():
    ...


def patron_hoy() -> tuple[str, str]:
    """(debe, no_debe) segun lo que QUEDA hoy en la agenda real."""
    ...


def pendientes() -> int:
    """Mensajes sin revisar ahora mismo, por la misma via que Hermes."""
    ...


def patron_logins() -> tuple[str, str]:
    """(debe, no_debe) segun los intentos fallidos REALES de hoy.

    En las dos direcciones: con intentos, se exige el numero y se prohibe
    decir que no hubo ninguno; con cero, al reves. Un "un" suelto aparece en
    muchas frases, y sin la prohibicion "no ha habido un solo intento"
    pasaria siendo falso.
    """
    ...


def _patron_numero(total: int) -> str:
    """El numero vale en cifra o en letra: "1 intento" y "un intento" dicen
    lo mismo. Exigir la cifra marco mal "un intento" (2026-09-23), el mismo
    error de medir la redaccion y no el fondo."""
    ...


def main() -> int:
    ...


if __name__ == '__main__':
    sys.exit(main())
