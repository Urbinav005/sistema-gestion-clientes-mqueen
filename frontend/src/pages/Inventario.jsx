// Pantalla de control de inventario (mockup 08): tarjetas de resumen, buscador,
// filtro por nivel de stock y tabla de refacciones con editar y eliminar.
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { eliminarPieza, listarInventario, resumenInventario } from '../api.js'
import EtiquetaStock from '../components/EtiquetaStock.jsx'
import Mensaje from '../components/Mensaje.jsx'
import TarjetaResumen from '../components/TarjetaResumen.jsx'
import { formatoDinero } from '../formato.js'

// Espera desde la última tecla antes de buscar
const ESPERA_BUSQUEDA = 300

function piezas(numero) {
  return `${numero} ${numero === 1 ? 'pieza' : 'piezas'}`
}

function Inventario() {
  const location = useLocation()
  const navigate = useNavigate()

  const [buscar, setBuscar] = useState('')
  const [filtro, setFiltro] = useState('')
  const [lista, setLista] = useState(null)
  const [resumen, setResumen] = useState(null)
  const [error, setError] = useState('')
  // Aviso de éxito; puede venir del formulario al guardar
  const [exito, setExito] = useState(() => location.state?.aviso || '')
  // Al cambiar este número se vuelven a pedir la lista y el resumen
  const [recargas, setRecargas] = useState(0)

  // El aviso del formulario se muestra una sola vez (no vuelve al recargar)
  useEffect(() => {
    if (location.state?.aviso) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location, navigate])

  // Resumen: siempre del inventario completo, no cambia con la búsqueda
  useEffect(() => {
    let vigente = true
    resumenInventario()
      .then((datos) => vigente && setResumen(datos))
      .catch((e) => vigente && setError(e.detalle))
    return () => {
      vigente = false
    }
  }, [recargas])

  // Lista: la búsqueda y el filtro los resuelve el backend
  useEffect(() => {
    let vigente = true
    const espera = setTimeout(() => {
      listarInventario({ buscar, estado_stock: filtro })
        .then((datos) => {
          if (!vigente) return
          setLista(datos)
          setError('')
        })
        .catch((e) => vigente && setError(e.detalle))
    }, ESPERA_BUSQUEDA)
    return () => {
      vigente = false
      clearTimeout(espera)
    }
  }, [buscar, filtro, recargas])

  async function eliminar(pieza) {
    const confirmado = window.confirm(
      `¿Eliminar "${pieza.nombre}"? Esta acción no se puede deshacer.`,
    )
    if (!confirmado) {
      return
    }
    setError('')
    setExito('')
    try {
      await eliminarPieza(pieza.id_pieza)
      setExito('Refacción eliminada')
      setRecargas((n) => n + 1)
    } catch (e) {
      // Por ejemplo 409: la pieza ya se usó en citas
      setError(e.detalle)
    }
  }

  const hayBusqueda = buscar.trim() !== '' || filtro !== ''

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">Control de inventario</h1>
          <p className="pagina-subtitulo">
            Administra refacciones y revisa las existencias disponibles.
          </p>
        </div>
        <Link to="/inventario/nueva" className="boton boton-principal">
          + Nueva refacción
        </Link>
      </div>

      {/* RN-16: las tarjetas usan los mismos niveles que la tabla */}
      <div className="tarjetas">
        <TarjetaResumen
          titulo="Productos registrados"
          valor={resumen ? resumen.total_piezas : '—'}
          subtitulo={
            // RN-05: valor del inventario calculado por el backend
            resumen ? `Valor del inventario: ${formatoDinero(resumen.valor_inventario)}` : ''
          }
          tono="azul"
        />
        <TarjetaResumen
          titulo="Stock suficiente"
          valor={resumen ? resumen.suficiente : '—'}
          subtitulo="Arriba del mínimo"
          tono="verde"
        />
        <TarjetaResumen
          titulo="Stock bajo"
          valor={resumen ? resumen.bajo : '—'}
          subtitulo="Próximos a agotarse"
          tono="amarillo"
        />
        <TarjetaResumen
          titulo="Stock crítico"
          valor={resumen ? resumen.critico : '—'}
          subtitulo="Necesitan reposición"
          tono="rojo"
        />
      </div>

      <div className="filtros">
        <input
          type="search"
          className="filtros-buscar"
          placeholder="Buscar por nombre o descripción"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <select value={filtro} onChange={(e) => setFiltro(e.target.value)} aria-label="Estado">
          <option value="">Todos</option>
          <option value="suficiente">Suficiente</option>
          <option value="bajo">Stock bajo</option>
          <option value="critico">Crítico</option>
        </select>
      </div>

      <Mensaje tipo="exito" texto={exito} />
      <Mensaje tipo="error" texto={error} />

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Existencias de refacciones</h2>
        {lista === null ? (
          error ? null : <p className="texto-gris">Cargando…</p>
        ) : lista.length === 0 ? (
          <p className="texto-gris">
            {hayBusqueda
              ? 'No hay refacciones que coincidan con la búsqueda.'
              : 'Aún no hay refacciones registradas.'}
          </p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Producto</th>
                <th>Existencia</th>
                <th>Mínimo</th>
                <th>Precio</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((pieza) => (
                <tr key={pieza.id_pieza}>
                  <td>
                    <div className="producto-nombre">{pieza.nombre}</div>
                    {pieza.descripcion && (
                      <div className="producto-descripcion">{pieza.descripcion}</div>
                    )}
                  </td>
                  <td className="texto-gris">{piezas(pieza.cantidad)}</td>
                  <td className="texto-gris">{piezas(pieza.stock_minimo)}</td>
                  <td>{formatoDinero(pieza.precio_unitario)}</td>
                  <td>
                    <EtiquetaStock estado={pieza.estado_stock} />
                  </td>
                  <td className="acciones">
                    <Link to={`/inventario/${pieza.id_pieza}/editar`} className="enlace">
                      Editar
                    </Link>
                    <button
                      type="button"
                      className="enlace enlace-peligro"
                      onClick={() => eliminar(pieza)}
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

export default Inventario
