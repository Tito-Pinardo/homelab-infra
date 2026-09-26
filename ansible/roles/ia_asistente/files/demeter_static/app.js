// Interfaz web de Demeter: revision de correos de compra, gastos y pedidos.
'use strict';
const $ = id => document.getElementById(id);
const state = {status:'review', page:1, query:'', csrf:'', selected:null, detail:null, busy:false, listRequest:0, detailRequest:0};
const statuses = {review:'Por revisar', validated:'Confirmados', discarded:'Descartados', pending:'Pendientes', error:'Con errores', all:'Todos los mensajes'};
const reasons = {remitente_no_reconocido:'Comercio por identificar', referencia_ausente:'Falta la referencia', referencia_ausente_o_multiple:'Revisa la referencia de la factura', total_ausente:'Falta el importe total', total_ausente_o_contradictorio:'El importe falta o no coincide entre fuentes', total_ausente_o_ambiguo:'Importe por comprobar', fecha_ausente_o_ambigua:'Fecha por comprobar', varios_pedidos_asignar_importes_manualmente:'Hay varios pedidos: revisa cada importe', adjunto_no_extraido_revisar_original:'Hay un PDF que necesita revisión', importe_o_moneda_ambiguos:'Importe o moneda ambiguos', totales_contradictorios:'Los totales no coinciden', reenviado_o_respuesta_comprobar_duplicado:'Comprueba si este mensaje está duplicado'};
const labels = {merchant:'Comercio',reference:'Factura o referencia',purchased_on:'Fecha de compra',total_minor:'Importe',currency:'Moneda'};
const merchantNames={'anthropic.com':'Anthropic','amazon.es':'Amazon','openai.com':'OpenAI','loteriasyapuestas.es':'Loterías y Apuestas','aliexpress.com':'AliExpress','poecurrency.com':'poecurrency'};

/** Crea un elemento HTML con texto y clase. */
function el(tag, text, cls) {
  // ...
}

/** Formatea un importe en centimos como moneda. */
function formatMoney(amount, currency) {
  // ...
}

/** Formatea una fecha para mostrarla. */
function formatDate(day) {
  // ...
}

/** Devuelve el nombre legible del comercio. */
function merchantName(item, row) {
  // ...
}

/** Indica si un articulo tiene todos los datos para confirmarlo. */
function ready(item) {
  // ...
}

/** Muestra un aviso en pantalla. */
function notify(message, error = false) {
  // ...
}

/** Llama a la API de Demeter con la sesion y el token CSRF. */
async function api(path, options = {}) {
  // ...
}

/** Carga el resumen del mes. */
async function summary() {
  // ...
}

/** Carga la lista de mensajes del estado seleccionado. */
async function loadList() {
  // ...
}

/** Devuelve la cita de evidencia de un campo. */
function quote(value) {
  // ...
}

/** Crea un campo editable del formulario de revision. */
function field(key, value, {evidence = false, index = 0} = {}) {
  // ...
}

/** Crea un bloque plegable con el texto original. */
function sourceBlock(title, text) {
  // ...
}

/** Convierte un importe escrito a centimos. */
function parseAmount(value) {
  // ...
}

/** Abre el detalle de un mensaje. */
async function openDetail(id) {
  // ...
}

/** Pinta el detalle de un mensaje con sus acciones de revision. */
function renderDetail(row) {
  // ...
}

/** Ejecuta una accion de revision sobre un mensaje. */
async function perform(row, action, data) {
  // ...
}

/** Carga los remitentes con mas mensajes por revisar. */
async function loadSenders() {
  // ...
}

/** Descarta en bloque los mensajes de un remitente. */
async function discardSender(sender, total) {
  // ...
}

/** Carga las compras aprobadas automaticamente pendientes de confirmar. */
async function loadAuto() {
  // ...
}

/** Confirma o deshace una compra aprobada automaticamente. */
async function decideAuto(row, action, quiet = false) {
  // ...
}

// Arranque: enlaza la navegacion, los filtros y las acciones en bloque, y
// carga el resumen y la lista inicial.
