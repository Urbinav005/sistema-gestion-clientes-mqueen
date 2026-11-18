// Funciones chicas para mostrar datos: dinero en pesos, fechas y horas, texto de cada
// nivel de stock y el cálculo de RN-16 para el aviso del formulario.
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

// ---------- Fechas ----------
// El backend manda y recibe las fechas en hora local y sin zona ("2026-11-20T10:30:00").
// new Date() con ese texto lo interpreta como hora local, que es lo correcto.
// Nunca se usa la conversión a hora de Greenwich: cambiaría la hora y hasta el día.

export const TEXTO_DIA = ['DOM', 'LUN', 'MAR', 'MIÉ', 'JUE', 'VIE', 'SÁB']

export const MESES = [
  'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
  'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre',
]

const MESES_CORTOS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']

function dosDigitos(numero) {
  return String(numero).padStart(2, '0')
}

// "2026-11-20T10:30:00" → "20 nov 2026"
export function formatoFecha(texto) {
  const fecha = new Date(texto)
  return `${fecha.getDate()} ${MESES_CORTOS[fecha.getMonth()]} ${fecha.getFullYear()}`
}

// "2026-11-20T10:30:00" → "10:30"
export function formatoHora(texto) {
  const fecha = new Date(texto)
  return `${dosDigitos(fecha.getHours())}:${dosDigitos(fecha.getMinutes())}`
}

// Un Date → "2026-11-20", con la fecha local (año, mes y día del calendario de aquí)
export function fechaParaApi(fecha) {
  return `${fecha.getFullYear()}-${dosDigitos(fecha.getMonth() + 1)}-${dosDigitos(fecha.getDate())}`
}
