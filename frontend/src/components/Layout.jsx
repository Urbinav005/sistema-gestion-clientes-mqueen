// Estructura común de las páginas con sesión: barra lateral, barra superior
// (dónde está el usuario, administrador y "Cerrar sesión") y el contenido de la página.
import { useEffect, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { quienSoy } from '../api.js'
import { cerrarSesion, leerAdmin } from '../sesion.js'
import BarraLateral from './BarraLateral.jsx'

const SECCIONES = {
  '/resumen': 'Resumen',
  '/clientes': 'Clientes',
  '/citas': 'Citas',
  '/vehiculos': 'Vehículos',
  '/inventario': 'Inventario',
}

// Subrutas: [patrón de la ruta, texto de la barra superior]
const SUBRUTAS = [
  [/^\/inventario\/nueva$/, 'Inventario / Nueva refacción'],
  [/^\/inventario\/[^/]+\/editar$/, 'Inventario / Editar refacción'],
  [/^\/clientes\/nuevo$/, 'Clientes / Registrar cliente'],
  [/^\/clientes\/[^/]+\/editar$/, 'Clientes / Editar cliente'],
  [/^\/vehiculos\/nuevo$/, 'Vehículos / Registrar vehículo'],
  [/^\/vehiculos\/[^/]+\/editar$/, 'Vehículos / Editar vehículo'],
  [/^\/vehiculos\/[^/]+\/historial$/, 'Vehículos / Historial'],
  [/^\/citas\/nueva$/, 'Citas / Agendar cita'],
  [/^\/citas\/[^/]+\/editar$/, 'Citas / Editar cita'],
  [/^\/citas\/[^/]+$/, 'Citas / Detalle'],
]

// Texto de la barra superior según la ruta actual
function textoUbicacion(ruta) {
  for (const [patron, texto] of SUBRUTAS) {
    if (patron.test(ruta)) {
      return texto
    }
  }
  return SECCIONES[ruta] || ''
}

function Layout() {
  const [admin, setAdmin] = useState(leerAdmin)
  const location = useLocation()
  const navigate = useNavigate()

  // Una vez al entrar: confirma que el token sigue sirviendo.
  // Si ya no sirve, api.js recibe el 401 y regresa al login.
  useEffect(() => {
    quienSoy()
      .then((datos) => setAdmin({ nombre: datos.nombre, usuario: datos.usuario }))
      .catch(() => {
        // Otros errores (backend apagado) se muestran en cada página
      })
  }, [])

  function salir() {
    cerrarSesion()
    navigate('/login', { replace: true })
  }

  const nombre = admin ? admin.nombre : 'Administrador'

  return (
    <div className="layout">
      <BarraLateral nombreAdmin={nombre} />
      <div className="layout-principal">
        <header className="barra-superior">
          <span className="barra-superior-ubicacion">{textoUbicacion(location.pathname)}</span>
          <div className="barra-superior-usuario">
            <span className="barra-superior-nombre">{nombre}</span>
            <button type="button" className="boton boton-secundario" onClick={salir}>
              Cerrar sesión
            </button>
          </div>
        </header>
        <main className="contenido">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default Layout
