// Agendar y editar una cita (mockup 06). En el alta se elige cliente y vehículo;
// en la edición solo se cambian fecha, hora, motivo y mano de obra. La fecha va en hora local, sin zona.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { actualizarCita, crearCita, listarClientes, listarVehiculos, ticketCita } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'

const VACIO = { id_cliente: '', id_vehiculo: '', fecha: '', hora: '', motivo: '', costo_mano_obra: '' }

function revisar(campos, esEdicion) {
  const errores = {}
  // RN-12: toda cita pertenece a un vehículo de un cliente
  if (!esEdicion && campos.id_cliente === '') {
    errores.id_cliente = 'Selecciona un cliente'
  }
  if (!esEdicion && campos.id_vehiculo === '') {
    errores.id_vehiculo = 'Selecciona un vehículo'
  }
  if (campos.fecha === '') {
    errores.fecha = 'La fecha es obligatoria'
  }
  if (campos.hora === '') {
    errores.hora = 'La hora es obligatoria'
  }
  if (campos.motivo.trim() === '') {
    errores.motivo = 'El motivo es obligatorio'
  }
  // Vacío cuenta como 0. Number() solo se usa para comparar.
  const costo = campos.costo_mano_obra.trim()
  if (costo !== '') {
    if (!Number.isFinite(Number(costo))) {
      errores.costo_mano_obra = 'El costo de mano de obra debe ser un número'
    } else if (Number(costo) < 0) {
      errores.costo_mano_obra = 'El costo de mano de obra no puede ser negativo'
    }
  }
  return errores
}

function FormularioCita() {
  const { id_cita } = useParams()
  const esEdicion = id_cita !== undefined
  const navigate = useNavigate()

  const [campos, setCampos] = useState(VACIO)
  const [clientes, setClientes] = useState([])
  const [vehiculos, setVehiculos] = useState(null)
  // Edición: la cita tal como llegó (cliente y vehículo solo se muestran)
  const [cita, setCita] = useState(null)
  const [errores, setErrores] = useState({})
  const [detalle, setDetalle] = useState('')
  const [cargando, setCargando] = useState(esEdicion)
  const [errorCarga, setErrorCarga] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Alta: clientes activos para el primer select
  useEffect(() => {
    if (esEdicion) {
      return
    }
    let vigente = true
    listarClientes()
      .then((datos) => vigente && setClientes(datos))
      .catch((e) => vigente && setDetalle(e.detalle))
    return () => {
      vigente = false
    }
  }, [esEdicion])

  // Alta: los vehículos del cliente elegido
  useEffect(() => {
    if (esEdicion || campos.id_cliente === '') {
      return
    }
    let vigente = true
    listarVehiculos({ id_cliente: campos.id_cliente })
      .then((datos) => vigente && setVehiculos(datos))
      .catch((e) => vigente && setDetalle(e.detalle))
    return () => {
      vigente = false
    }
  }, [esEdicion, campos.id_cliente])

  // Edición: se carga la cita desde su ticket
  useEffect(() => {
    if (!esEdicion) {
      return
    }
    let vigente = true
    ticketCita(id_cita)
      .then((datos) => {
        if (!vigente) return
        setCita(datos)
        setCampos({
          ...VACIO,
          // Se corta el texto del backend: no pasa por Date, así no cambia la hora
          fecha: datos.fecha.slice(0, 10),
          hora: datos.fecha.slice(11, 16),
          motivo: datos.motivo,
          costo_mano_obra: datos.costo_mano_obra ?? '',
        })
        setCargando(false)
      })
      .catch((e) => {
        if (!vigente) return
        setErrorCarga(e.detalle)
        setCargando(false)
      })
    return () => {
      vigente = false
    }
  }, [esEdicion, id_cita])

  function cambiar(evento) {
    const { name, value } = evento.target
    setCampos((anteriores) => ({ ...anteriores, [name]: value }))
  }

  function cambiarCliente(evento) {
    // Al cambiar de cliente, el vehículo se vacía
    const id_cliente = evento.target.value
    setCampos((anteriores) => ({ ...anteriores, id_cliente, id_vehiculo: '' }))
    setVehiculos(null)
  }

  async function guardar(evento) {
    evento.preventDefault()
    setDetalle('')

    const nuevos = revisar(campos, esEdicion)
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) {
      return
    }

    const costo = campos.costo_mano_obra.trim()
    const datos = {
      // Hora local sin zona, armada pegando textos: "2026-11-20" + "T" + "10:30" + ":00"
      fecha: `${campos.fecha}T${campos.hora}:00`,
      motivo: campos.motivo,
      // El dinero va como texto, nunca como número de punto flotante
      costo_mano_obra: costo === '' ? '0' : costo,
    }

    setGuardando(true)
    try {
      if (esEdicion) {
        await actualizarCita(id_cita, datos)
        navigate(`/citas/${id_cita}`, { state: { aviso: 'Cita guardada' } })
      } else {
        const nueva = await crearCita({ id_vehiculo: Number(campos.id_vehiculo), ...datos })
        // Al detalle de la cita recién creada, para agregarle las piezas
        navigate(`/citas/${nueva.id_cita}`, { state: { aviso: 'Cita guardada' } })
      }
    } catch (e) {
      // Lo escrito no se pierde: solo se muestran los errores
      setGuardando(false)
      setDetalle(e.detalle)
      const porCampo = {}
      for (const error of e.errores) {
        porCampo[error.campo] = error.mensaje
      }
      setErrores(porCampo)
    }
  }

  if (cargando) {
    return <p className="texto-gris">Cargando…</p>
  }

  if (errorCarga) {
    return (
      <section>
        <Mensaje tipo="error" texto={errorCarga} />
        <Link to="/citas" className="enlace">
          Volver a la agenda
        </Link>
      </section>
    )
  }

  // RN-11: una cita Terminada o Cancelada ya no se modifica
  if (esEdicion && (cita.estado === 'Terminada' || cita.estado === 'Cancelada')) {
    return (
      <section>
        <p className="nota">La cita está {cita.estado} y ya no se puede modificar.</p>
        <Link to={`/citas/${id_cita}`} className="enlace">
          Ver la cita
        </Link>
      </section>
    )
  }

  const sinVehiculos = !esEdicion && campos.id_cliente !== '' && vehiculos !== null && vehiculos.length === 0

  return (
    <section>
      <h1 className="pagina-titulo">{esEdicion ? 'Editar cita' : 'Agendar nueva cita'}</h1>
      <p className="pagina-subtitulo pagina-subtitulo-separado">
        Registra la visita de un vehículo y el servicio solicitado.
      </p>

      <form className="tarjeta formulario" onSubmit={guardar} noValidate>
        <h2 className="tarjeta-titulo">Datos de la cita</h2>

        <Mensaje tipo="error" texto={detalle} />

        <div className="formulario-rejilla">
          {esEdicion ? (
            <>
              <div className="campo">
                <span className="campo-etiqueta">Cliente</span>
                <span className="campo-fijo">{cita.vehiculo.cliente.nombre}</span>
              </div>
              <div className="campo">
                <span className="campo-etiqueta">Vehículo</span>
                <span className="campo-fijo">
                  {cita.vehiculo.placas} · {cita.vehiculo.marca} {cita.vehiculo.modelo}
                </span>
              </div>
            </>
          ) : (
            <>
              <label className="campo">
                <span className="campo-etiqueta">Cliente</span>
                <select name="id_cliente" value={campos.id_cliente} onChange={cambiarCliente}>
                  <option value="">Selecciona un cliente</option>
                  {clientes.map((c) => (
                    <option key={c.id_cliente} value={String(c.id_cliente)}>
                      {c.nombre}
                    </option>
                  ))}
                </select>
                {errores.id_cliente && <span className="campo-error">{errores.id_cliente}</span>}
              </label>

              <label className="campo">
                <span className="campo-etiqueta">Vehículo</span>
                <select
                  name="id_vehiculo"
                  value={campos.id_vehiculo}
                  onChange={cambiar}
                  disabled={campos.id_cliente === ''}
                >
                  <option value="">Selecciona un vehículo</option>
                  {(vehiculos || []).map((v) => (
                    <option key={v.id_vehiculo} value={String(v.id_vehiculo)}>
                      {v.placas} · {v.marca} {v.modelo}
                    </option>
                  ))}
                </select>
                {errores.id_vehiculo && <span className="campo-error">{errores.id_vehiculo}</span>}
                {sinVehiculos && (
                  <span className="campo-ayuda">
                    Este cliente no tiene vehículos registrados.{' '}
                    <Link to={`/vehiculos/nuevo?id_cliente=${campos.id_cliente}`} className="enlace">
                      Registrar vehículo
                    </Link>
                  </span>
                )}
              </label>
            </>
          )}

          <label className="campo">
            <span className="campo-etiqueta">Fecha</span>
            <input name="fecha" type="date" value={campos.fecha} onChange={cambiar} />
            {errores.fecha && <span className="campo-error">{errores.fecha}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Hora</span>
            <input name="hora" type="time" value={campos.hora} onChange={cambiar} />
            {errores.hora && <span className="campo-error">{errores.hora}</span>}
          </label>

          <label className="campo campo-completo">
            <span className="campo-etiqueta">Motivo de la visita</span>
            <textarea name="motivo" maxLength={255} rows={3} value={campos.motivo} onChange={cambiar} />
            {errores.motivo && <span className="campo-error">{errores.motivo}</span>}
            <span className="campo-ayuda">Ej. Cambio de aceite. Se guarda sin acentos.</span>
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Costo de mano de obra (MXN)</span>
            <input
              name="costo_mano_obra"
              type="text"
              inputMode="decimal"
              value={campos.costo_mano_obra}
              onChange={cambiar}
            />
            {errores.costo_mano_obra && (
              <span className="campo-error">{errores.costo_mano_obra}</span>
            )}
          </label>
        </div>

        {!esEdicion && <p className="formulario-nota">La cita quedará registrada como Pendiente.</p>}

        <div className="formulario-botones">
          <Link to={esEdicion ? `/citas/${id_cita}` : '/citas'} className="boton boton-secundario">
            Cancelar
          </Link>
          <button type="submit" className="boton boton-principal" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar cita'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default FormularioCita
