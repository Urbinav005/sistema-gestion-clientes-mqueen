// Todas las llamadas fetch al backend. Ningún componente llama a fetch directamente.
// Los errores se lanzan como { estado, detalle, errores } para mostrarlos en pantalla.
import { cerrarSesion, leerToken } from './sesion.js'

const URL_API = 'http://localhost:8000/api'
// Clave donde se deja el aviso de sesión vencida para que el login lo muestre
export const CLAVE_AVISO = 'mqueen_aviso'

async function pedir(ruta, opciones = {}) {
  const cabeceras = {}
  if (opciones.cuerpo !== undefined) {
    cabeceras['Content-Type'] = 'application/json'
  }
  const token = leerToken()
  if (token) {
    cabeceras['Authorization'] = `Bearer ${token}`
  }

  let respuesta
  try {
    respuesta = await fetch(URL_API + ruta, {
      method: opciones.metodo || 'GET',
      headers: cabeceras,
      body: opciones.cuerpo !== undefined ? JSON.stringify(opciones.cuerpo) : undefined,
    })
  } catch {
    // Backend apagado o sin red
    throw {
      estado: 0,
      detalle: 'No se pudo conectar con el servidor. Revisa que el backend esté encendido.',
      errores: [],
    }
  }

  if (respuesta.status === 204) {
    return null
  }

  let datos = null
  try {
    datos = await respuesta.json()
  } catch {
    datos = null
  }

  if (respuesta.ok) {
    return datos
  }

  const detalle =
    datos && typeof datos.detail === 'string' ? datos.detail : 'Ocurrió un error inesperado'
  const errores = datos && Array.isArray(datos.errores) ? datos.errores : []

  // RN-13: con la sesión vencida o inválida se regresa al login
  if (respuesta.status === 401 && ruta !== '/auth/login') {
    cerrarSesion()
    sessionStorage.setItem(CLAVE_AVISO, detalle)
    window.location.assign('/login')
  }

  throw { estado: respuesta.status, detalle, errores }
}

// ---------- Sesión ----------

export function iniciarSesion(usuario, password) {
  return pedir('/auth/login', { metodo: 'POST', cuerpo: { usuario, password } })
}

export function quienSoy() {
  return pedir('/auth/yo')
}

// ---------- Inventario ----------

export function listarInventario({ buscar, estado_stock } = {}) {
  // Solo se mandan los parámetros que traen algo
  const parametros = new URLSearchParams()
  if (buscar && buscar.trim() !== '') {
    parametros.set('buscar', buscar.trim())
  }
  if (estado_stock) {
    parametros.set('estado_stock', estado_stock)
  }
  const consulta = parametros.toString()
  return pedir(consulta ? `/inventario?${consulta}` : '/inventario')
}

export function resumenInventario() {
  return pedir('/inventario/resumen')
}

export function obtenerPieza(id_pieza) {
  return pedir(`/inventario/${encodeURIComponent(id_pieza)}`)
}

export function crearPieza(datos) {
  return pedir('/inventario', { metodo: 'POST', cuerpo: datos })
}

export function actualizarPieza(id_pieza, datos) {
  return pedir(`/inventario/${encodeURIComponent(id_pieza)}`, { metodo: 'PUT', cuerpo: datos })
}

export function eliminarPieza(id_pieza) {
  return pedir(`/inventario/${encodeURIComponent(id_pieza)}`, { metodo: 'DELETE' })
}
