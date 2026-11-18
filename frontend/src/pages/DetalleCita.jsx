// Detalle de una cita / ticket (no está en Figma): datos, cambio de estado, refacciones usadas
// (agregar y quitar) y totales. Todo sale del ticket que calcula el backend.
import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import {
  agregarPiezaCita,
  cambiarEstadoCita,
  listarInventario,
  quitarPiezaCita,
  ticketCita,
} from '../api.js'
import EtiquetaCita from '../components/EtiquetaCita.jsx'
import Mensaje from '../components/Mensaje.jsx'
import { formatoDinero, formatoFecha, formatoHora } from '../formato.js'

const ENTERO = /^\d+$/

function DetalleCita() {
  const { id_cita } = useParams()
  const location = useLocation()
  const navigate = useNavigate()

  const [ticket, setTicket] = useState(null)
  const [errorCarga, setErrorCarga] = useState('')
  const [error, setError] = useState('')
  const [exito, setExito] = useState(() => location.state?.aviso || '')
  // RN-02: aviso de stock bajo que manda el backend al agregar una pieza
  const [avisoStock, setAvisoStock] = useState('')
  const [recargas, setRecargas] = useState(0)
  const [ocupado, setOcupado] = useState(false)

  // Formulario para agregar una refacción
  const [piezas, setPiezas] = useState([])
  const [recargasPiezas, setRecargasPiezas] = useState(0)
  const [idPieza, setIdPieza] = useState('')
  const [cantidad, setCantidad] = useState('1')
  const [erroresPieza, setErroresPieza] = useState({})

  // El aviso del formulario se muestra una sola vez
  useEffect(() => {
    if (location.state?.aviso) {
      navigate(location.pathname, { replace: true, state: null })
    }
  }, [location, navigate])

  useEffect(() => {
    let vigente = true
    ticketCita(id_cita)
      .then((datos) => {
        if (!vigente) return
        setTicket(datos)
        setErrorCarga('')
      })
      .catch((e) => vigente && setErrorCarga(e.detalle))
    return () => {
      vigente = false
    }
  }, [id_cita, recargas])

  // RN-07: las existencias del select se vuelven a pedir después de agregar o quitar
  useEffect(() => {
    let vigente = true
    listarInventario()
      .then((datos) => vigente && setPiezas(datos))
      .catch((e) => vigente && setError(e.detalle))
    return () => {
      vigente = false
    }
  }, [recargasPiezas])

  function limpiarAvisos() {
    setError('')
    setExito('')
    setAvisoStock('')
  }

  async function cambiarEstado(nuevo, pregunta) {
    if (pregunta && !window.confirm(pregunta)) {
      return
    }
    limpiarAvisos()
    setOcupado(true)
    try {
      await cambiarEstadoCita(id_cita, nuevo)
      setRecargas((n) => n + 1)
      // RN-10: al cancelar, las piezas regresan al inventario
      setRecargasPiezas((n) => n + 1)
    } catch (e) {
      setError(e.detalle)
    }
    setOcupado(false)
  }

  async function agregar(evento) {
    evento.preventDefault()
    limpiarAvisos()

    const nuevos = {}
    if (idPieza === '') {
      nuevos.id_pieza = 'Selecciona una refacción'
    }
    if (!ENTERO.test(cantidad.trim()) || Number(cantidad) < 1) {
      nuevos.cantidad = 'La cantidad debe ser al menos 1'
    }
    setErroresPieza(nuevos)
    if (Object.keys(nuevos).length > 0) {
      return
    }

    setOcupado(true)
    try {
      // La respuesta ya es el ticket nuevo
      const nuevo = await agregarPiezaCita(id_cita, Number(idPieza), Number(cantidad.trim()))
      setTicket(nuevo)
      setAvisoStock(nuevo.aviso || '')
      setIdPieza('')
      setCantidad('1')
      setRecargasPiezas((n) => n + 1)
    } catch (e) {
      // RN-01: "Stock insuficiente: solo hay N" va bajo la cantidad
      const porCampo = {}
      for (const err of e.errores) {
        porCampo[err.campo] = err.mensaje
      }
      setErroresPieza(porCampo)
      if (!porCampo.cantidad && !porCampo.id_pieza) {
        setError(e.detalle)
      }
    }
    setOcupado(false)
  }

  async function quitar(renglon) {
    if (!window.confirm(`¿Quitar "${renglon.nombre}" de la cita? Regresará al inventario.`)) {
      return
    }
    limpiarAvisos()
    setOcupado(true)
    try {
      const nuevo = await quitarPiezaCita(id_cita, renglon.id_pieza)
      setTicket(nuevo)
      setRecargasPiezas((n) => n + 1)
    } catch (e) {
      setError(e.detalle)
    }
    setOcupado(false)
  }

  const volver = (
    <Link to="/citas" className="enlace no-imprimir">
      Volver a la agenda
    </Link>
  )

  if (errorCarga) {
    return (
      <section>
        <Mensaje tipo="error" texto={errorCarga} />
        {volver}
      </section>
    )
  }

  if (ticket === null) {
    return <p className="texto-gris">Cargando…</p>
  }

  const { vehiculo } = ticket
  // RN-11: Terminada y Cancelada quedan cerradas
  const abierta = ticket.estado === 'Pendiente' || ticket.estado === 'En proceso'

  return (
    <section className="ticket">
      <div className="pagina-encabezado">
        <div className="ticket-titulo">
          <h1 className="pagina-titulo">Cita #{ticket.id_cita}</h1>
          <EtiquetaCita estado={ticket.estado} />
        </div>
        {volver}
      </div>

      <div className="no-imprimir">
        <Mensaje tipo="exito" texto={exito} />
        <Mensaje tipo="error" texto={error} />
      </div>

      <div className="tarjeta ficha">
        <h2 className="tarjeta-titulo">Datos de la cita</h2>
        <dl className="ficha-datos">
          <div>
            <dt>Fecha y hora</dt>
            <dd>
              {formatoFecha(ticket.fecha)}, {formatoHora(ticket.fecha)}
            </dd>
          </div>
          <div>
            <dt>Cliente</dt>
            <dd>
              {vehiculo.cliente.nombre}
              <span className="texto-gris"> · {vehiculo.cliente.telefono}</span>
            </dd>
          </div>
          <div>
            <dt>Vehículo</dt>
            <dd>
              {vehiculo.marca} {vehiculo.modelo} {vehiculo.anio ?? ''}
              <span className="texto-gris"> · {vehiculo.placas}</span>
            </dd>
          </div>
          <div>
            <dt>Motivo</dt>
            <dd>{ticket.motivo}</dd>
          </div>
        </dl>

        <div className="ficha-acciones no-imprimir">
          {ticket.estado === 'Pendiente' && (
            <button
              type="button"
              className="boton boton-principal"
              disabled={ocupado}
              onClick={() => cambiarEstado('En proceso')}
            >
              Iniciar servicio
            </button>
          )}
          {ticket.estado === 'En proceso' && (
            <button
              type="button"
              className="boton boton-principal"
              disabled={ocupado}
              onClick={() =>
                cambiarEstado(
                  'Terminada',
                  '¿Terminar el servicio? La cita quedará cerrada y ya no se podrá modificar.',
                )
              }
            >
              Terminar servicio
            </button>
          )}
          {abierta && (
            <>
              <Link to={`/citas/${ticket.id_cita}/editar`} className="boton boton-secundario">
                Editar datos
              </Link>
              <button
                type="button"
                className="boton boton-secundario boton-peligro"
                disabled={ocupado}
                onClick={() =>
                  cambiarEstado(
                    'Cancelada',
                    // RN-10: cancelar devuelve las piezas al inventario
                    '¿Cancelar la cita? Las piezas registradas regresarán al inventario.',
                  )
                }
              >
                Cancelar cita
              </button>
            </>
          )}
          {!abierta && (
            <p className="nota">Esta cita está {ticket.estado} y ya no se puede modificar.</p>
          )}
        </div>
      </div>

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Refacciones usadas</h2>

        {ticket.renglones.length === 0 ? (
          <p className="texto-gris">Todavía no se registran refacciones.</p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Refacción</th>
                <th>Cantidad</th>
                <th>Precio unitario</th>
                <th>Importe</th>
                {abierta && <th className="no-imprimir">Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {ticket.renglones.map((renglon) => (
                <tr key={renglon.id_pieza}>
                  <td className="producto-nombre">{renglon.nombre}</td>
                  <td>{renglon.cantidad}</td>
                  {/* RN-08: el precio congelado del renglón, no el del inventario */}
                  <td>{formatoDinero(renglon.precio_unitario)}</td>
                  <td>{formatoDinero(renglon.importe)}</td>
                  {abierta && (
                    <td className="acciones no-imprimir">
                      <button
                        type="button"
                        className="enlace enlace-peligro"
                        disabled={ocupado}
                        onClick={() => quitar(renglon)}
                      >
                        Quitar
                      </button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {abierta && (
          <form className="agregar-pieza no-imprimir" onSubmit={agregar} noValidate>
            {avisoStock && <div className="aviso-nivel aviso-bajo">{avisoStock}</div>}
            <div className="agregar-pieza-campos">
              <label className="campo agregar-pieza-refaccion">
                <span className="campo-etiqueta">Refacción</span>
                <select value={idPieza} onChange={(e) => setIdPieza(e.target.value)}>
                  <option value="">Selecciona una refacción</option>
                  {piezas.map((p) => (
                    <option key={p.id_pieza} value={String(p.id_pieza)}>
                      {p.nombre} — {p.cantidad} disponibles — {formatoDinero(p.precio_unitario)}
                    </option>
                  ))}
                </select>
                {erroresPieza.id_pieza && <span className="campo-error">{erroresPieza.id_pieza}</span>}
              </label>
              <label className="campo agregar-pieza-cantidad">
                <span className="campo-etiqueta">Cantidad</span>
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={cantidad}
                  onChange={(e) => setCantidad(e.target.value)}
                />
                {erroresPieza.cantidad && <span className="campo-error">{erroresPieza.cantidad}</span>}
              </label>
              <button type="submit" className="boton boton-principal" disabled={ocupado}>
                Agregar
              </button>
            </div>
          </form>
        )}

        {/* RN-09: los totales los calcula el backend; aquí no se suma nada */}
        <dl className="totales">
          <div>
            <dt>Refacciones</dt>
            <dd>{formatoDinero(ticket.subtotal_piezas)}</dd>
          </div>
          <div>
            <dt>Mano de obra</dt>
            <dd>{formatoDinero(ticket.costo_mano_obra ?? '0')}</dd>
          </div>
          <div className="totales-total">
            <dt>Total</dt>
            <dd>{formatoDinero(ticket.total)}</dd>
          </div>
        </dl>

        {ticket.estado === 'Cancelada' && (
          // RN-10: una cita cancelada no cobra nada
          <p className="nota">Cita cancelada: las piezas regresaron al inventario y no se cobra nada.</p>
        )}
      </div>

      <div className="formulario-botones no-imprimir">
        <button type="button" className="boton boton-secundario" onClick={() => window.print()}>
          Imprimir ticket
        </button>
      </div>
    </section>
  )
}

export default DetalleCita
