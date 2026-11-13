// Protege las páginas del sistema: si no hay sesión guardada, manda al login.
import { Navigate } from 'react-router-dom'
import { leerToken } from '../sesion.js'

function RutaProtegida({ children }) {
  // RN-13: solo el administrador con sesión ve el sistema
  if (!leerToken()) {
    return <Navigate to="/login" replace />
  }
  return children
}

export default RutaProtegida
