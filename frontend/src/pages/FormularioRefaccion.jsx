// Alta y edición de una refacción (la misma página): si la ruta trae id_pieza, es edición.
// Hace una revisión rápida antes de llamar al backend, que es quien valida de verdad.
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { actualizarPieza, crearPieza, obtenerPieza } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'
import { calcularEstadoStock } from '../formato.js'

const VACIO = { nombre: '', descripcion: '', cantidad: '', stock_minimo: '', precio_unitario: '' }
const ENTERO = /^-?\d+$/

// Revisa un campo entero; devuelve el mensaje de error o '' si está bien
function revisarEntero(texto, mensajeEntero, mensajeNegativo) {
  if (!ENTERO.test(texto.trim())) {
    return mensajeEntero
  }
  if (Number(texto) < 0) {
    return mensajeNegativo
  }
  return ''
}

function revisar(campos) {
  const errores = {}
  if (campos.nombre.trim() === '') {
    errores.nombre = 'El nombre es obligatorio'
  }
  // RN-01, RN-04: la cantidad no puede ser negativa
  const cantidad = revisarEntero(
    campos.cantidad,
    'La cantidad debe ser un número entero',
    'La cantidad no puede ser negativa',
  )
  if (cantidad) {
    errores.cantidad = cantidad
  }
  // RN-04: el stock mínimo no puede ser negativo
  const minimo = revisarEntero(
    campos.stock_minimo,
    'El stock mínimo debe ser un número entero',
    'El stock mínimo no puede ser negativo',
  )
  if (minimo) {
    errores.stock_minimo = minimo
  }
  // RN-03: el precio debe ser mayor a 0. Number() solo se usa para comparar.
  const precio = campos.precio_unitario.trim()
  if (precio === '' || !Number.isFinite(Number(precio))) {
    errores.precio_unitario = 'El precio debe ser un número'
  } else if (Number(precio) <= 0) {
    errores.precio_unitario = 'El precio debe ser mayor a 0'
  }
  return errores
}

// RN-16: cómo quedará la pieza con lo que se escribió (solo si ambos son enteros válidos)
function nivelPrevisto(campos) {
  const cantidad = campos.cantidad.trim()
  const minimo = campos.stock_minimo.trim()
  if (!/^\d+$/.test(cantidad) || !/^\d+$/.test(minimo)) {
    return null
  }
  return calcularEstadoStock(Number(cantidad), Number(minimo))
}

function FormularioRefaccion() {
  const { id_pieza } = useParams()
  const esEdicion = id_pieza !== undefined
  const navigate = useNavigate()

  const [campos, setCampos] = useState(VACIO)
  const [errores, setErrores] = useState({})
  const [detalle, setDetalle] = useState('')
  const [cargando, setCargando] = useState(esEdicion)
  const [errorCarga, setErrorCarga] = useState('')
  const [guardando, setGuardando] = useState(false)

  // Edición: se piden los datos de la pieza y se llenan los campos
  useEffect(() => {
    if (!esEdicion) {
      return
    }
    let vigente = true
    obtenerPieza(id_pieza)
      .then((pieza) => {
        if (!vigente) return
        setCampos({
          nombre: pieza.nombre,
          descripcion: pieza.descripcion || '',
          cantidad: String(pieza.cantidad),
          stock_minimo: String(pieza.stock_minimo),
          precio_unitario: pieza.precio_unitario,
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
  }, [esEdicion, id_pieza])

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

    const descripcion = campos.descripcion.trim()
    const datos = {
      nombre: campos.nombre,
      descripcion: descripcion === '' ? null : descripcion,
      cantidad: Number(campos.cantidad.trim()),
      stock_minimo: Number(campos.stock_minimo.trim()),
      // El precio va como texto: el dinero no pasa por decimales de punto flotante
      precio_unitario: campos.precio_unitario.trim(),
    }

    setGuardando(true)
    try {
      if (esEdicion) {
        await actualizarPieza(id_pieza, datos)
      } else {
        await crearPieza(datos)
      }
      navigate('/inventario', { state: { aviso: 'Refacción guardada' } })
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
        <Link to="/inventario" className="enlace">
          Volver al inventario
        </Link>
      </section>
    )
  }

  const nivel = nivelPrevisto(campos)

  return (
    <section>
      <form className="tarjeta formulario" onSubmit={guardar} noValidate>
        <h1 className="pagina-titulo">{esEdicion ? 'Editar refacción' : 'Nueva refacción'}</h1>
        <p className="pagina-subtitulo">Completa los datos de la refacción.</p>

        <Mensaje tipo="error" texto={detalle} />

        <div className="formulario-rejilla">
          <label className="campo">
            <span className="campo-etiqueta">Nombre</span>
            <input name="nombre" type="text" maxLength={100} value={campos.nombre} onChange={cambiar} />
            {errores.nombre && <span className="campo-error">{errores.nombre}</span>}
            <span className="campo-ayuda">Se guarda sin acentos.</span>
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Precio unitario (MXN)</span>
            <input
              name="precio_unitario"
              type="text"
              inputMode="decimal"
              value={campos.precio_unitario}
              onChange={cambiar}
            />
            {errores.precio_unitario && (
              <span className="campo-error">{errores.precio_unitario}</span>
            )}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Cantidad en existencia</span>
            <input name="cantidad" type="number" step="1" value={campos.cantidad} onChange={cambiar} />
            {errores.cantidad && <span className="campo-error">{errores.cantidad}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Stock mínimo</span>
            <input
              name="stock_minimo"
              type="number"
              step="1"
              value={campos.stock_minimo}
              onChange={cambiar}
            />
            {errores.stock_minimo && <span className="campo-error">{errores.stock_minimo}</span>}
            <span className="campo-ayuda">Al llegar a esta cantidad se marca como stock bajo.</span>
          </label>

          {/* RN-16: aviso de cómo quedará la pieza antes de guardar */}
          {nivel === 'bajo' && (
            <div className="aviso-nivel aviso-bajo campo-completo">
              Con estos datos la pieza quedará en Stock bajo.
            </div>
          )}
          {nivel === 'critico' && (
            <div className="aviso-nivel aviso-critico campo-completo">
              Con estos datos la pieza quedará en nivel Crítico.
            </div>
          )}

          <label className="campo campo-completo">
            <span className="campo-etiqueta">Descripción</span>
            <textarea
              name="descripcion"
              maxLength={255}
              rows={3}
              value={campos.descripcion}
              onChange={cambiar}
            />
            {errores.descripcion && <span className="campo-error">{errores.descripcion}</span>}
            <span className="campo-ayuda">Opcional.</span>
          </label>
        </div>

        <div className="formulario-botones">
          <Link to="/inventario" className="boton boton-secundario">
            Cancelar
          </Link>
          <button type="submit" className="boton boton-principal" disabled={guardando}>
            {guardando ? 'Guardando…' : 'Guardar refacción'}
          </button>
        </div>
      </form>
    </section>
  )
}

export default FormularioRefaccion
