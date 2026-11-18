// Alta y edición de un cliente (mockup 04): nombre, teléfono y correo.
// Si la ruta trae id_cliente, es edición. El backend valida el formato del teléfono y del correo.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { actualizarCliente, crearCliente, obtenerCliente } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'

const VACIO = { nombre: '', telefono: '', correo: '' }

function revisar(campos) {
  const errores = {}
  if (campos.nombre.trim() === '') {
    errores.nombre = 'El nombre es obligatorio'
  }
  if (campos.telefono.trim() === '') {
    errores.telefono = 'El teléfono es obligatorio'
  }
  return errores
}

function FormularioCliente() {
  const { id_cliente } = useParams()
  const esEdicion = id_cliente !== undefined
  const navigate = useNavigate()

  const [campos, setCampos] = useState(VACIO)
  const [errores, setErrores] = useState({})
  const [detalle, setDetalle] = useState('')
  const [cargando, setCargando] = useState(esEdicion)
  const [errorCarga, setErrorCarga] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Edición: se piden los datos del cliente y se llenan los campos
  useEffect(() => {
    if (!esEdicion) {
      return
    }
    let vigente = true
    obtenerCliente(id_cliente)
      .then((datos) => {
        if (!vigente) return
        setCampos({ nombre: datos.nombre, telefono: datos.telefono, correo: datos.correo || '' })
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
  }, [esEdicion, id_cliente])

  function cambiar(evento) {
    const { name, value } = evento.target
    setCampos((anteriores) => ({ ...anteriores, [name]: value }))
  }

  async function guardar(evento) {
    evento.preventDefault()
    setDetalle('')

    const nuevos = revisar(campos)
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) {
      return
    }

    const correo = campos.correo.trim()
    const datos = {
      nombre: campos.nombre,
      telefono: campos.telefono,
      // El correo es opcional: vacío se manda como null
      correo: correo === '' ? null : correo,
    }

    setGuardando(true)
    try {
      if (esEdicion) {
        await actualizarCliente(id_cliente, datos)
      } else {
        await crearCliente(datos)
      }
      navigate('/clientes', { state: { aviso: 'Cliente guardado' } })
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
        <Link to="/clientes" className="enlace">
          Volver a clientes
        </Link>
      </section>
    )
  }

  return (
    <section>
      <h1 className="pagina-titulo">{esEdicion ? 'Editar cliente' : 'Registrar cliente'}</h1>
      <p className="pagina-subtitulo pagina-subtitulo-separado">
        {esEdicion
          ? 'Actualiza los datos del cliente.'
          : 'Completa los datos para dar de alta a un nuevo cliente.'}
      </p>

      <form className="tarjeta formulario" onSubmit={guardar} noValidate>
        <h2 className="tarjeta-titulo">Información personal</h2>

        <Mensaje tipo="error" texto={detalle} />

        <div className="formulario-rejilla">
          <label className="campo">
            <span className="campo-etiqueta">Nombre completo</span>
            <input
              name="nombre"
              type="text"
              maxLength={100}
              placeholder="Ej. Juan Rodríguez"
              value={campos.nombre}
              onChange={cambiar}
            />
            {errores.nombre && <span className="campo-error">{errores.nombre}</span>}
            <span className="campo-ayuda">Se guarda sin acentos.</span>
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Teléfono</span>
            <input
              name="telefono"
              type="tel"
              maxLength={15}
              placeholder="Ej. 618 000 0000"
              value={campos.telefono}
              onChange={cambiar}
            />
            {errores.telefono && <span className="campo-error">{errores.telefono}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Correo electrónico</span>
            <input
              name="correo"
              type="email"
              maxLength={100}
              placeholder="Ej. correo@ejemplo.com"
              value={campos.correo}
              onChange={cambiar}
            />
            {errores.correo && <span className="campo-error">{errores.correo}</span>}
            <span className="campo-ayuda">Opcional.</span>
          </label>
        </div>

        {!esEdicion && (
          <p className="formulario-nota">Después de guardar podrás registrar los vehículos del cliente.</p>
        )}

        <div className="formulario-botones">
          <Link to="/clientes" className="boton boton-secundario">
            Cancelar
          </Link>
          <button type="submit" className="boton boton-principal" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar cliente'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default FormularioCliente
