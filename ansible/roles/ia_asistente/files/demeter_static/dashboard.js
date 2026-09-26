'use strict';
// Vistas de panel mensual y pedidos de la interfaz de Demeter.
const dashboardState = {view: 'dashboard', ordersOffset: 0, request: 0, monthlyRequest: 0};

/** Cambia la vista activa y carga sus datos. */
function showView(view) {
  // ...
}

/** Redacta el texto de cobertura de la sincronizacion de correo. */
function coverageText(c) {
  // ...
}

/** Pinta un desglose de gasto por categoria o comercio. */
function breakdown(id, items, key) {
  // ...
}

/** Carga el panel del mes: cobertura, desgloses, historial y gastos recurrentes. */
async function loadDashboard() {
  // ...
}

/** Carga la lista de pedidos segun los filtros. */
async function loadOrders() {
  // ...
}

/** Pinta la tarjeta de un pedido con sus documentos, seguimiento y organizacion. */
function orderCard(order) {
  // ...
}

// Arranque: enlaza la navegacion, los filtros, la paginacion y la
// importacion de correos, y carga el panel inicial.
