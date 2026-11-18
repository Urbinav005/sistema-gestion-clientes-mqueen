// Alta y edición de un vehículo (no está en Figma): cliente, placas, marca, modelo, año y kilometraje.
// Si la ruta trae id_vehiculo, es edición. En el alta, ?id_cliente= llega ya elegido.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { actualizarVehiculo, crearVehiculo, listarClientes, obtenerVehiculo } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'

const ENTERO = /^-?\d+$/

function revisar(campos) {
  const errores = {}
  // RN-12: todo vehículo pertenece a un cliente
  if (campos.id_cliente === '') {
    errores.id_cliente = 'Selecciona un cliente'
  }
  if (campos.placas.trim() === '') {
    errores.placas = 'Las placas son obligatorias'
  }
  if (campos.marca.trim() === '') {
    errores.marca = 'La marca es obligatoria'
  }
  if (campos.modelo.trim() === '') {
    errores.modelo = 'El modelo es obligatorio'
  }
  // Año y kilometraje son opcionales; si traen algo, debe ser entero
  if (campos.anio.trim() !== '' && !ENTERO.test(campos.anio.trim())) {
    errores.anio = 'El año debe ser un número entero'
  }
  if (campos.kilometraje.trim() !== '' && !ENTERO.test(campos.kilometraje.trim())) {
    errores.kilometraje = 'El kilometraje debe ser un número entero'
  }
  return errores
}

// Vacío → null; si no, el número entero
function enteroOpcional(texto) {
  const limpio = texto.trim()
  return limpio === '' ? null : Number(limpio)
}

function FormularioVehiculo() {
  const { id_vehiculo } = useParams()
  const esEdicion = id_vehiculo !== undefined
  const [parametros] = useSearchParams()
  const clienteInicial = esEdicion ? '' : parametros.get('id_cliente') || ''
  const navigate = useNavigate()

  const [campos, setCampos] = useState({
    id_cliente: clienteInicial,
    placas: '',
    marca: '',
    modelo: '',
    anio: '',
    kilometraje: '',
  })
  const [clientes, setClientes] = useState([])
  const [errores, setErrores] = useState({})
  const [detalle, setDetalle] = useState('')
  const [cargando, setCargando] = useState(esEdicion)
  const [errorCarga, setErrorCarga] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Al guardar o cancelar: si llegó filtrado por cliente, regresa a ese filtro
  const destino = clienteInicial ? `/vehiculos?id_cliente=${clienteInicial}` : '/vehiculos'

  // Clientes activos para el select
  useEffect(() => {
    let vigente = true
    listarClientes()
      .then((datos) => vigente && setClientes(datos))
      .catch((e) => vigente && setDetalle(e.detalle))
    return () => {
      vigente = false
    }
  }, [])

  // Edición: se piden los datos del vehículo y se llenan los campos
  useEffect(() => {
    if (!esEdicion) {
      return
    }
    let vigente = true
    obtenerVehiculo(id_vehiculo)
      .then((v) => {
        if (!vigente) return
        setCampos({
          id_cliente: String(v.id_cliente),
          placas: v.placas,
          marca: v.marca,
          modelo: v.modelo,
          anio: v.anio === null ? '' : String(v.anio),
          kilometraje: v.kilometraje === null ? '' : String(v.kilometraje),
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
  }, [esEdicion, id_vehiculo])

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

    const datos = {
      id_cliente: Number(campos.id_cliente),
      placas: campos.placas,
      marca: campos.marca,
      modelo: campos.modelo,
      anio: enteroOpcional(campos.anio),
      kilometraje: enteroOpcional(campos.kilometraje),
    }

    setGuardando(true)
    try {
      if (esEdicion) {
        await actualizarVehiculo(id_vehiculo, datos)
      } else {
        await crearVehiculo(datos)
      }
      navigate(destino, { state: { aviso: 'Vehículo guardado' } })
    } catch (e) {
      // Lo escrito no se pierde: solo se muestran los errores (placas repetidas, rangos…)
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
        <Link to="/vehiculos" className="enlace">
          Volver a vehículos
        </Link>
      </section>
    )
  }

  return (
    <section>
      <h1 className="pagina-titulo">{esEdicion ? 'Editar vehículo' : 'Registrar vehículo'}</h1>
      <p className="pagina-subtitulo pagina-subtitulo-separado">Completa los datos del vehículo.</p>

      <form className="tarjeta formulario" onSubmit={guardar} noValidate>
        <h2 className="tarjeta-titulo">Datos del vehículo</h2>

        <Mensaje tipo="error" texto={detalle} />

        <div className="formulario-rejilla">
          <label className="campo campo-completo">
            <span className="campo-etiqueta">Cliente</span>
            <select name="id_cliente" value={campos.id_cliente} onChange={cambiar}>
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
            <span className="campo-etiqueta">Placas</span>
            <input name="placas" type="text" maxLength={15} value={campos.placas} onChange={cambiar} />
            {errores.placas && <span className="campo-error">{errores.placas}</span>}
            <span className="campo-ayuda">Se guardan en mayúsculas.</span>
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Marca</span>
            <input name="marca" type="text" maxLength={50} value={campos.marca} onChange={cambiar} />
            {errores.marca && <span className="campo-error">{errores.marca}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Modelo</span>
            <input name="modelo" type="text" maxLength={50} value={campos.modelo} onChange={cambiar} />
            {errores.modelo && <span className="campo-error">{errores.modelo}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Año</span>
            <input name="anio" type="number" step="1" value={campos.anio} onChange={cambiar} />
            {errores.anio && <span className="campo-error">{errores.anio}</span>}
            <span className="campo-ayuda">Opcional.</span>
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Kilometraje</span>
            <input
              name="kilometraje"
              type="number"
              step="1"
              value={campos.kilometraje}
              onChange={cambiar}
            />
            {errores.kilometraje && <span className="campo-error">{errores.kilometraje}</span>}
            <span className="campo-ayuda">Opcional.</span>
          </label>
        </div>

        <div className="formulario-botones">
          <Link to={destino} className="boton boton-secundario">
            Cancelar
          </Link>
          <button type="submit" className="boton boton-principal" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar vehículo'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default FormularioVehiculo
