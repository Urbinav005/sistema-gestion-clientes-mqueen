// Barra lateral: logo "AG", nombre del taller, menú principal y el administrador.
// NavLink marca la opción activa con la clase "activa".
import { NavLink } from 'react-router-dom'

// Mismo orden que el mockup. Los íconos son caracteres simples (sin librería de íconos).
const OPCIONES = [
  { ruta: '/resumen', texto: 'Resumen', icono: '⌂' },
  { ruta: '/clientes', texto: 'Clientes', icono: '◎' },
  { ruta: '/citas', texto: 'Citas', icono: '◷' },
  { ruta: '/vehiculos', texto: 'Vehículos', icono: '◇' },
  { ruta: '/inventario', texto: 'Inventario', icono: '▦' },
]

// "Rodolfo Urbina" → "RU"; "Administrador" → "AD"
function iniciales(nombre) {
  const palabras = nombre.trim().split(/\s+/).filter(Boolean)
  if (palabras.length === 0) {
    return '?'
  }
  if (palabras.length === 1) {
    return palabras[0].slice(0, 2).toUpperCase()
  }
  return (palabras[0][0] + palabras[1][0]).toUpperCase()
}

function BarraLateral({ nombreAdmin }) {
  return (
    <aside className="barra-lateral">
      <div className="marca">
        <div className="logo">AG</div>
        <div>
          <div className="marca-nombre">TALLER AUTO GREEN</div>
          <div className="marca-sub">SISTEMA ADMINISTRATIVO</div>
        </div>
      </div>

      <nav className="menu">
        <div className="menu-titulo">MENÚ PRINCIPAL</div>
        {OPCIONES.map((opcion) => (
          <NavLink
            key={opcion.ruta}
            to={opcion.ruta}
            className={({ isActive }) => (isActive ? 'menu-opcion activa' : 'menu-opcion')}
          >
            <span className="menu-icono" aria-hidden="true">
              {opcion.icono}
            </span>
            {opcion.texto}
          </NavLink>
        ))}
      </nav>

      <div className="admin">
        <div className="admin-iniciales">{iniciales(nombreAdmin)}</div>
        <div>
          <div className="admin-nombre">{nombreAdmin}</div>
          <div className="admin-sub">Acceso interno</div>
        </div>
      </div>
    </aside>
  )
}

export default BarraLateral
