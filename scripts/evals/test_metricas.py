"""Telemetría de la Fase 0: línea de métricas y detección de narración.

Sin modelo, sin red y sin importar el bot: se cargan por AST solo las
funciones puras, igual que el resto de pruebas de esta carpeta.
"""
import ast
import re
import unittest
from pathlib import Path

FILES = Path(__file__).resolve().parents[2] / 'ansible/roles/ia_asistente/files'
BOT = FILES / 'ia_bot.py'
LLM = FILES / 'local_llm_client.py'


def cargar_pistas():
    """`pista_de_enrutado` con TODAS sus constantes `_PISTA_*`.

    Cargarlas por nombre obligaba a tocar cada prueba al añadir un patrón, y
    de hecho rompió la batería entera una vez (NameError a mitad de una
    medición). Mejor recogerlas por prefijo.
    """
    ...


def cargar(path, nombres, entorno=None):
    ...


class MetricasTests(unittest.TestCase):
    def metricas(self, data, reparto='no consultado'):
        ...

    def test_incluye_tokens_y_tiempos(self):
        ...

    def test_reparto_solo_cuando_el_modelo_acaba_de_cargarse(self):
        ...

    def test_respuesta_sin_metricas_no_rompe(self):
        ...


class NarracionTests(unittest.TestCase):
    def setUp(self):
        ...

    def test_detecta_el_caso_real_del_eval(self):
        ...

    def test_respuesta_normal_no_se_marca(self):
        ...

    def test_no_confunde_un_prefijo_con_el_nombre_entero(self):
        ...

    def test_varias_tools_en_la_misma_respuesta(self):
        ...


class ReintentoNarracionTests(unittest.TestCase):
    def setUp(self):
        ...

    def pedir(self, reply, usadas=()):
        ...

    def test_reintenta_una_tool_de_lectura(self):
        ...

    def test_no_reintenta_si_el_turno_ya_uso_tools(self):
        ...

    def test_nunca_reintenta_una_escritura(self):
        ...

    def test_no_reintenta_si_nombra_varias(self):
        ...

    def test_respuesta_normal_no_dispara_reintento(self):
        ...


class ValidarArgumentosTests(unittest.TestCase):
    def setUp(self):
        ...

    def test_entero_en_texto_se_corrige(self):
        ...

    def test_booleano_en_texto_se_corrige(self):
        ...

    def test_falta_obligatorio_devuelve_error_legible(self):
        ...

    def test_valor_no_convertible_se_deja_igual(self):
        ...

    def test_tool_desconocida_no_rompe(self):
        ...


class RazonamientoTests(unittest.TestCase):
    """think=true solo donde aporta: elegir tool y calcular argumentos."""

    def setUp(self):
        ...

    def test_la_primera_llamada_razona(self):
        ...

    def test_la_llamada_tras_una_tool_con_datos_no_razona(self):
        ...

    def test_da_igual_cuantas_tools_se_hayan_usado(self):
        ...


class MarcaTurnoTests(unittest.TestCase):
    def setUp(self):
        ...

    def test_respuesta_final_tras_usar_tools(self):
        ...

    def test_respuesta_final_que_nombra_la_tool_usada_no_es_narracion(self):
        ...

    def test_narracion_solo_si_el_turno_no_uso_ninguna(self):
        ...

    def test_respuesta_de_charla_sin_tools(self):
        ...

    def test_varias_tools_en_el_mismo_turno(self):
        ...



class AnunciosDemeterTests(unittest.TestCase):
    """Como anuncia Hermes las compras que Deméter aprueba sola (2026-09-23)."""

    def setUp(self):
        ...

    def compra(self, n, merchant='loteriasyapuestas.es', total=500):
        ...

    def test_pocas_compras_se_anuncian_una_a_una_con_su_papelera(self):
        ...

    def test_una_rafaga_va_en_un_solo_mensaje_por_comercio(self):
        ...

    def test_una_compra_con_varias_filas_se_anuncia_una_vez(self):
        ...

    def test_el_checkpoint_llega_al_final_si_no_quedan_mas(self):
        ...

    def test_con_la_consulta_llena_no_se_salta_ninguna_compra(self):
        ...

    def test_un_envio_rechazado_no_se_da_por_publicado(self):
        ...

    def test_el_limite_de_hermes_es_el_de_la_consulta(self):
        ...


class ConsultarNotasTests(unittest.TestCase):
    """Preguntas sobre algo ya ocurrido: el codigo busca en las notas si el
    modelo iba a responder sin mirarlas (2026-09-23, ~80 % con solo la pista)."""

    def setUp(self):
        ...

    def test_sin_tools_o_solo_con_estado_actual_se_consultan_las_notas(self):
        ...

    def test_si_ya_fue_a_una_fuente_de_datos_no_se_le_enmienda(self):
        ...

    def test_una_pregunta_en_presente_no_se_toca(self):
        ...

    def test_las_tools_de_estado_existen_en_el_catalogo(self):
        ...


class CorregirFechasTests(unittest.TestCase):
    """Guardia de dias de la semana, con las frases erroneas REALES del 23-09.

    Ese dia (miercoles 23) Hermes escribio "hoy (martes 23 sep)" y "Martes
    22 sep (hoy)": 1 de cada ~7 agendas, con el dia correcto ya escrito en el
    dato que recibia. La segunda ni siquiera la veia un medidor que solo
    comprobase que dia y numero cuadran entre si.
    """

    def setUp(self):
        ...

    def fija(self, texto):
        ...

    def test_dia_equivocado_junto_a_hoy(self):
        ...

    def test_fecha_entera_equivocada_marcada_como_hoy(self):
        ...

    def test_dia_equivocado_sin_hoy(self):
        ...

    def test_lo_correcto_no_se_toca(self):
        ...

    def test_un_hoy_cercano_pero_de_otro_evento_no_arrastra_la_fecha(self):
        ...

    def test_con_mes_explicito_se_usa_ese_mes(self):
        ...

    def test_sin_mes_y_lejos_de_la_agenda_no_se_adivina(self):
        ...

    def test_devuelve_que_cambio_para_el_registro(self):
        ...


class FiltroEventosTests(unittest.TestCase):
    """Primera pasada del filtro de agenda: por palabras, sin modelo.

    Buscaba la pregunta ENTERA como subcadena, que casi nunca coincide, y
    delegaba en un sub-prompt que el 23-09 por la noche acerto 1 de 3 veces
    con "¿cuanto costo la entrada de la pelicula que tengo esta semana?".
    Sin el evento, la pregunta encadenada se quedaba sin titulo que buscar.
    """

    PELI = {'titulo': 'VENGADORES: ENDGAME (ATMOS) (IV)', 'categoria': '',
            'descripcion': 'Cine con Sylvia y mi hermana. Creado desde un correo de tickets@ocinequadernillos.es.'}
    PADEL = {'titulo': 'Clases padel', 'categoria': '', 'descripcion': ''}
    PARTIDO = {'titulo': 'Partido de 1:30H en pistas 2 y 9', 'categoria': '', 'descripcion': ''}

    def setUp(self):
        ...

    def test_la_pregunta_real_encuentra_la_pelicula(self):
        ...

    def test_encuentra_por_el_titulo(self):
        ...

    def test_una_pregunta_sin_palabras_con_significado_no_filtra(self):
        ...

    def test_lo_que_no_aparece_no_se_inventa(self):
        ...

if __name__ == '__main__':
    unittest.main()


class CacheTools(unittest.TestCase):
    """Las tools lentas (git, whois, GitHub) se reutilizan un rato."""

    def setUp(self):
        ...

    def test_la_segunda_llamada_no_reejecuta(self):
        ...

    def test_claves_distintas_no_se_pisan(self):
        ...

    def test_ttl_cero_siempre_consulta(self):
        ...


class SaludSinRuidoTests(unittest.TestCase):
    """get_server_health era el resultado más grande de todos (5093 chars)."""

    def test_deja_fuera_lo_que_tiene_tool_propia(self):
        ...

    def test_sin_snapshot_lo_dice(self):
        ...


class PistaEnrutadoTests(unittest.TestCase):
    """Aviso puntual para preguntas sobre algo ya ocurrido."""

    def setUp(self):
        ...

    def test_caso_real_pendiente_desde_el_22_09(self):
        ...

    def test_otras_formas_de_preguntar_por_el_pasado(self):
        ...

    def test_el_estado_en_vivo_no_se_desvia(self):
        ...

    def test_texto_vacio(self):
        ...


class RespaldoDemeterTests(unittest.TestCase):
    """Deméter vacío no es "no existe": el correo puede tener el dato."""

    def setUp(self):
        ...

    def test_sin_resultados_sugiere_el_correo(self):
        ...

    def test_con_resultados_no_lo_sugiere(self):
        ...

    def test_resumen_con_totales_no_lo_sugiere(self):
        ...

    def test_otras_tools_no_llevan_aviso_de_demeter(self):
        ...


class ResultadoUtilTests(unittest.TestCase):
    """Un resultado vacío no cierra la pregunta: hay que seguir razonando."""

    def setUp(self):
        ...

    def test_detecta_resultados_vacios(self):
        ...

    def test_reconoce_resultados_con_datos(self):
        ...

    def test_tras_un_resultado_vacio_se_vuelve_a_razonar(self):
        ...

    def test_tras_un_resultado_con_datos_solo_se_redacta(self):
        ...

    def test_la_primera_llamada_siempre_razona(self):
        ...


class ReintentoTrasVacioTests(unittest.TestCase):
    """Tras una búsqueda vacía, el modelo ofrece la siguiente en vez de hacerla."""

    def setUp(self):
        ...

    def test_caso_real_del_cine(self):
        ...

    def test_no_se_reintenta_la_que_ya_fallo(self):
        ...

    def test_si_el_resultado_traia_datos_no_se_reintenta(self):
        ...

    def test_sigue_sin_reintentar_escrituras(self):
        ...


class PistaAccesoTests(unittest.TestCase):
    """Cómo se entra a un servicio está en las notas, no en el estado en vivo."""

    def setUp(self):
        ...

    def test_caso_real_del_panel(self):
        ...

    def test_otras_formas(self):
        ...

    def test_no_roba_preguntas_de_estado(self):
        ...

    def test_el_pasado_sigue_teniendo_su_pista(self):
        ...


class DireccionesInventadasTests(unittest.TestCase):
    """Una IP que no está en ninguna fuente es inventada."""

    def setUp(self):
        ...

    def test_caso_real(self):
        ...

    def test_ip_respaldada_no_se_marca(self):
        ...

    def test_ip_que_escribio_el_usuario(self):
        ...

    def test_respuesta_sin_ips(self):
        ...

    def test_varias_ips_sin_repetir(self):
        ...


class ImportesInventadosTests(unittest.TestCase):
    """Un importe que no sale de ninguna fuente es inventado."""

    def setUp(self):
        ...

    def test_caso_real_del_cine(self):
        ...

    def test_importe_del_correo_se_acepta(self):
        ...

    def test_centimos_de_demeter_se_aceptan_en_euros(self):
        ...

    def test_una_suma_legitima_no_se_marca(self):
        ...

    def test_una_suma_de_cuatro_conceptos_tampoco(self):
        ...

    def test_sigue_marcando_lo_que_no_sale_de_ahi(self):
        ...

    def test_sin_fuentes_no_se_marca_nada(self):
        ...

    def test_respuesta_sin_importes(self):
        ...


class PistaEncadenadaTests(unittest.TestCase):
    """Preguntas que son dos: qué evento es, y cuánto costó."""

    def setUp(self):
        ...

    def test_caso_real(self):
        ...

    def test_otras_formas(self):
        ...

    def test_no_se_mete_en_preguntas_de_un_solo_paso(self):
        ...


class HerramientaCaidaTests(unittest.TestCase):
    """Una tool que falla no es una búsqueda sin resultados."""

    def setUp(self):
        ...

    def test_un_error_se_avisa_como_fallo(self):
        ...

    def test_una_busqueda_vacia_no_es_un_fallo(self):
        ...

    def test_el_aviso_de_antiguedad_sigue_funcionando(self):
        ...


class AvisaDelFalloTests(unittest.TestCase):
    """«No he encontrado nada» y «no he podido comprobarlo» no son lo mismo."""

    def setUp(self):
        ...

    def test_respuestas_que_si_lo_dejan_claro(self):
        ...

    def test_respuestas_ambiguas(self):
        ...


class AnotarCaidaTests(unittest.TestCase):
    """Un fallo corregido en el mismo turno no es un fallo que avisar."""

    def setUp(self):
        ...

    def test_un_error_queda_apuntado(self):
        ...

    def test_un_reintento_bueno_borra_el_fallo(self):
        ...

    def test_el_exito_de_otra_tool_no_borra_el_fallo(self):
        ...


class SeguimientoConPronombreTests(unittest.TestCase):
    """«¿Y cuánto me costaron?» sin repetir de qué se habla."""

    def setUp(self):
        ...

    def test_seguimientos_cortos(self):
        ...

    def test_preguntas_con_sujeto_propio_no_se_tocan(self):
        ...


class EurosYCoberturaTests(unittest.TestCase):
    """Deméter habla en céntimos y marca completo aunque queden por revisar."""

    def test_anade_el_importe_en_euros(self):
        ...

    def test_importes_pequenos_y_grandes(self):
        ...

    def test_no_toca_lo_que_no_es_centimos(self):
        ...

    def test_avisa_de_los_mensajes_por_revisar(self):
        ...

    def test_sin_pendientes_no_avisa_de_eso(self):
        ...


class ClavesDemeterTests(unittest.TestCase):
    """Pedidos por llegar y mensajes sin revisar son cosas distintas."""

    def setUp(self):
        ...

    def test_separa_los_dos_conceptos(self):
        ...

    def test_retira_los_nombres_ambiguos(self):
        ...

    def test_sin_esas_claves_no_inventa_nada(self):
        ...
