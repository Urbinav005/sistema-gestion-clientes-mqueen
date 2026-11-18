// Directorio de clientes (mockup 03): buscador, alta, edición, baja lógica
// y, con "Mostrar dados de baja", reactivación.
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { darDeBajaCliente, listarClientes, reactivarCliente } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'

// Espera desde la última tecla antes de buscar
const ESPERA_BUSQUEDA = 300

function textoVehiculos(numero) {
  if (numero === 0) {
    return 'Sin vehículos'
  }
  return `${numero} ${numero === 1 ? 'vehículo' : 'vehículos'}`
}

function Clientes() {
  const location = useLocation()
  const navigate = useNavigate()

  const [buscar, setBuscar] = useState('')
  const [verInactivos, setVerInactivos] = useState(false)
  const [lista, setLista] = useState(null)
  const [error, setError] = useState('')
  // Aviso de éxito; puede venir del formulario al guardar
  const [exito, setExito] = useState(() => location.state?.aviso || '')
  const [recargas, setRecargas] = useState(0)

  // El aviso del formulario se muestra una sola vez
  useEffect(() => {
    if (location.state?.aviso) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location, navigate])

  // La búsqueda la resuelve el backend
  useEffect(() => {
    let vigente = true
    const espera = setTimeout(() => {
      listarClientes({ buscar, incluir_inactivos: verInactivos })
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
  }, [buscar, verInactivos, recargas])

  async function darDeBaja(cliente) {
    const confirmado = window.confirm(
      `¿Dar de baja a "${cliente.nombre}"? Sus vehículos dejarán de aparecer en las listas.`,
    )
    if (!confirmado) {
      return
    }
    setError('')
    setExito('')
    try {
      await darDeBajaCliente(cliente.id_cliente)
      setExito('Cliente dado de baja')
      setRecargas((n) => n + 1)
    } catch (e) {
      // 409: el cliente tiene citas pendientes o en proceso
      setError(e.detalle)
    }
  }

  async function reactivar(cliente) {
    setError('')
    setExito('')
    try {
      await reactivarCliente(cliente.id_cliente)
      setExito('Cliente reactivado')
      setRecargas((n) => n + 1)
    } catch (e) {
      setError(e.detalle)
    }
  }

  const hayBusqueda = buscar.trim() !== ''

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">Clientes</h1>
          <p className="pagina-subtitulo">
            Consulta y administra la información de los clientes del taller.
          </p>
        </div>
      </div>

      <div className="filtros">
        <input
          type="search"
          className="filtros-buscar"
          placeholder="Buscar por nombre o teléfono"
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
        <Link to="/clientes/nuevo" className="boton boton-principal filtros-boton">
          + Nuevo cliente
        </Link>
      </div>

      <Mensaje tipo="exito" texto={exito} />
      <Mensaje tipo="error" texto={error} />

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Directorio de clientes</h2>
        {lista === null ? (
          error ? null : <p className="texto-gris">Cargando…</p>
        ) : lista.length === 0 ? (
          <p className="texto-gris">
            {hayBusqueda
              ? 'No hay clientes que coincidan con la búsqueda.'
              : 'Aún no hay clientes registrados.'}
          </p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Cliente</th>
                <th>Teléfono</th>
                <th>Correo</th>
                <th>Vehículos</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {lista.map((c) => (
                <tr key={c.id_cliente}>
                  <td>
                    <span className="producto-nombre">{c.nombre}</span>
                    {!c.activo && <span className="etiqueta etiqueta-gris etiqueta-junto">Dado de baja</span>}
                  </td>
                  <td className="texto-gris">{c.telefono}</td>
                  <td className="texto-gris">{c.correo || '—'}</td>
                  <td className="texto-gris">
                    {c.activo && c.total_vehiculos > 0 ? (
                      <Link to={`/vehiculos?id_cliente=${c.id_cliente}`} className="enlace">
                        {textoVehiculos(c.total_vehiculos)}
                      </Link>
                    ) : (
                      textoVehiculos(c.total_vehiculos)
                    )}
                  </td>
                  <td className="acciones">
                    {c.activo ? (
                      <>
                        <Link to={`/vehiculos/nuevo?id_cliente=${c.id_cliente}`} className="enlace">
                          Agregar vehículo
                        </Link>
                        <Link to={`/clientes/${c.id_cliente}/editar`} className="enlace">
                          Editar
                        </Link>
                        <button
                          type="button"
                          className="enlace enlace-peligro"
                          onClick={() => darDeBaja(c)}
                        >
                          Dar de baja
                        </button>
                      </>
                    ) : (
                      <button type="button" className="enlace" onClick={() => reactivar(c)}>
                        Reactivar
                      </button>
                    )}
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

export default Clientes
