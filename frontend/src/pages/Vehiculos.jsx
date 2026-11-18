// Vehículos registrados (mockup 07): buscador por placa, modelo o cliente, filtro por cliente
// (?id_cliente=), historial, edición, baja lógica y, con "Mostrar dados de baja", reactivación.
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import { darDeBajaVehiculo, listarVehiculos, reactivarVehiculo } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'
import { formatoFecha } from '../formato.js'

// Espera desde la última tecla antes de buscar
const ESPERA_BUSQUEDA = 300

function Vehiculos() {
  const location = useLocation()
  const navigate = useNavigate()
  const [parametros, setParametros] = useSearchParams()
  const idCliente = parametros.get('id_cliente') || ''

  const [buscar, setBuscar] = useState('')
  const [verInactivos, setVerInactivos] = useState(false)
  const [lista, setLista] = useState(null)
  const [error, setError] = useState('')
  // Aviso de éxito; puede venir del formulario al guardar
  const [exito, setExito] = useState(() => location.state?.aviso || '')
  const [recargas, setRecargas] = useState(0)

  // El aviso del formulario se muestra una sola vez (se conserva ?id_cliente=)
  useEffect(() => {
    if (location.state?.aviso) {
      navigate(location.pathname + location.search, { replace: true, state: null })
    }
  }, [location, navigate])

  // La búsqueda y el filtro por cliente los resuelve el backend
  useEffect(() => {
    let vigente = true
    const espera = setTimeout(() => {
      listarVehiculos({ buscar, id_cliente: idCliente, incluir_inactivos: verInactivos })
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
  }, [buscar, idCliente, verInactivos, recargas])

  async function darDeBaja(vehiculo) {
    if (!window.confirm(`¿Dar de baja el vehículo ${vehiculo.placas}?`)) {
      return
    }
    setError('')
    setExito('')
    try {
      await darDeBajaVehiculo(vehiculo.id_vehiculo)
      setExito('Vehículo dado de baja')
      setRecargas((n) => n + 1)
    } catch (e) {
      // 409: el vehículo tiene citas pendientes o en proceso
      setError(e.detalle)
    }
  }

  async function reactivar(vehiculo) {
    setError('')
    setExito('')
    try {
      await reactivarVehiculo(vehiculo.id_vehiculo)
      setExito('Vehículo reactivado')
      setRecargas((n) => n + 1)
    } catch (e) {
      setError(e.detalle)
    }
  }

  function verTodos() {
    setParametros({})
  }

  const hayBusqueda = buscar.trim() !== ''
  const nuevoVehiculo = idCliente ? `/vehiculos/nuevo?id_cliente=${idCliente}` : '/vehiculos/nuevo'

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">Vehículos</h1>
          <p className="pagina-subtitulo">Consulta los vehículos registrados y su propietario.</p>
        </div>
      </div>

      <div className="filtros">
        <input
          type="search"
          className="filtros-buscar"
          placeholder="Buscar placa, modelo o cliente"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
        />
        <label className="casilla">
          <input
            type="checkbox"
            checked={verInactivos}
            onChange={(e) => setVerInactivos(e.target.checked)}
          />
          Mostrar dados de baja
        </label>
        <Link to={nuevoVehiculo} className="boton boton-principal filtros-boton">
          + Registrar vehículo
        </Link>
      </div>

      <Mensaje tipo="exito" texto={exito} />
      <Mensaje tipo="error" texto={error} />

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Vehículos registrados</h2>

        {idCliente && lista !== null && (
          <p className="filtro-cliente">
            {lista.length > 0
              ? `Vehículos de ${lista[0].cliente.nombre}`
              : hayBusqueda
                ? 'No hay vehículos de este cliente que coincidan con la búsqueda.'
                : 'Este cliente no tiene vehículos registrados.'}{' '}
            <button type="button" className="enlace" onClick={verTodos}>
              Ver todos
            </button>
          </p>
        )}

        {lista === null ? (
          error ? null : <p className="texto-gris">Cargando…</p>
        ) : lista.length === 0 ? (
          idCliente ? null : (
            <p className="texto-gris">
              {hayBusqueda
                ? 'No hay vehículos que coincidan con la búsqueda.'
                : 'Aún no hay vehículos registrados.'}
            </p>
          )
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Vehículo</th>
                <th>Año</th>
                <th>Placa</th>
                <th>Propietario</th>
                <th>Última visita</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((v) => {
                // Un vehículo está de baja si él o su cliente lo están
                const deBaja = !v.activo || !v.cliente.activo
                return (
                  <tr key={v.id_vehiculo}>
                    <td>
                      <span className="producto-nombre">
                        {v.marca} {v.modelo}
                      </span>
                      {deBaja && <span className="etiqueta etiqueta-gris etiqueta-junto">Dado de baja</span>}
                    </td>
                    <td className="texto-gris">{v.anio ?? '—'}</td>
                    <td className="texto-gris">{v.placas}</td>
                    <td className="texto-gris">{v.cliente.nombre}</td>
                    <td className="texto-gris">
                      {v.ultima_visita ? formatoFecha(v.ultima_visita) : 'Sin visitas'}
                    </td>
                    <td className="acciones">
                      <Link to={`/vehiculos/${v.id_vehiculo}/historial`} className="enlace">
                        Historial
                      </Link>
                      {!deBaja && (
                        <>
                          <Link to={`/vehiculos/${v.id_vehiculo}/editar`} className="enlace">
                            Editar
                          </Link>
                          <button
                            type="button"
                            className="enlace enlace-peligro"
                            onClick={() => darDeBaja(v)}
                          >
                            Dar de baja
                          </button>
                        </>
                      )}
                      {deBaja && !v.cliente.activo && (
                        <span className="texto-gris texto-chico">Reactiva primero al cliente</span>
                      )}
                      {deBaja && v.cliente.activo && (
                        <button type="button" className="enlace" onClick={() => reactivar(v)}>
                          Reactivar
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        )}
      </div>
    </section>
  )
}

export default Vehiculos
