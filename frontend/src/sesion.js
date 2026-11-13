// Guarda, lee y borra la sesión del administrador en sessionStorage:
// aguanta recargar la página, pero se pierde al cerrar la pestaña.
const CLAVE_TOKEN = 'mqueen_token'
const CLAVE_ADMIN = 'mqueen_admin'

// La contraseña nunca se guarda: solo el token y los datos del administrador
export function guardarSesion(token, administrador) {
  sessionStorage.setItem(CLAVE_TOKEN, token)
  const datos = { nombre: administrador.nombre, usuario: administrador.usuario }
  sessionStorage.setItem(CLAVE_ADMIN, JSON.stringify(datos))
}

export function leerToken() {
  return sessionStorage.getItem(CLAVE_TOKEN)
}

export function leerAdmin() {
  const texto = sessionStorage.getItem(CLAVE_ADMIN)
  if (!texto) {
    return null
  }
  try {
    return JSON.parse(texto)
  } catch {
    return null
  }
}

export function cerrarSesion() {
  sessionStorage.removeItem(CLAVE_TOKEN)
  sessionStorage.removeItem(CLAVE_ADMIN)
}
