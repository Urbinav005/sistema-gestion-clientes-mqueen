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

// Texto de la barra superior según la ruta actual
function textoUbicacion(ruta) {
  if (ruta === '/inventario/nueva') {
    return 'Inventario / Nueva refacción'
  }
  if (ruta.startsWith('/inventario/') && ruta.endsWith('/editar')) {
    return 'Inventario / Editar refacción'
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
