// Funciones chicas para mostrar datos: dinero en pesos, texto de cada nivel de stock
// y el cálculo de RN-16 para el aviso del formulario.
const FORMATO_PESOS = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'MXN' })

// Solo para mostrar: "85905.00" → "$85,905.00". El dinero nunca se manda así al backend.
export function formatoDinero(texto) {
  return FORMATO_PESOS.format(Number(texto))
}

export const TEXTO_ESTADO = {
  suficiente: 'Suficiente',
  bajo: 'Stock bajo',
  critico: 'Crítico',
}

// RN-16: la misma fórmula del backend. Solo la usa el aviso del formulario antes de guardar;
// la tabla y las tarjetas usan el estado_stock que manda el backend.
export function calcularEstadoStock(cantidad, stock_minimo) {
  if (cantidad === 0 || cantidad * 2 <= stock_minimo) {
    return 'critico'
  }
  if (cantidad <= stock_minimo) {
    return 'bajo'
  }
  return 'suficiente'
}
