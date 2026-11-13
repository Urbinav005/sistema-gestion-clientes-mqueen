// Pantalla de acceso del administrador (mockup 01): usuario y contraseña.
// Si el backend acepta, guarda la sesión y entra al inventario.
import { useEffect, useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { CLAVE_AVISO, iniciarSesion } from '../api.js'
import Mensaje from '../components/Mensaje.jsx'
import { guardarSesion, leerToken } from '../sesion.js'

function Login() {
  const navigate = useNavigate()
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [errores, setErrores] = useState({})
  const [detalle, setDetalle] = useState('')
  const [entrando, setEntrando] = useState(false)
  // Aviso que dejó api.js cuando la sesión venció
  const [aviso] = useState(() => sessionStorage.getItem(CLAVE_AVISO) || '')

  // El aviso se muestra solo una vez
  useEffect(() => {
    sessionStorage.removeItem(CLAVE_AVISO)
  }, [])

  // Ya hay sesión: no tiene caso volver a entrar
  if (leerToken()) {
    return <Navigate to="/inventario" replace />
  }

  async function entrar(evento) {
    evento.preventDefault()
    setDetalle('')

    // Revisión rápida: no se llama al backend con campos vacíos
    const nuevos = {}
    if (usuario.trim() === '') {
      nuevos.usuario = 'El usuario es obligatorio'
    }
    if (password === '') {
      nuevos.password = 'La contraseña es obligatoria'
    }
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) {
      return
    }

    setEntrando(true)
    try {
      const respuesta = await iniciarSesion(usuario, password)
      guardarSesion(respuesta.token, respuesta.administrador)
      navigate('/inventario', { replace: true })
    } catch (error) {
      setEntrando(false)
      if (error.estado === 401) {
        setDetalle(error.detalle)
        setPassword('')
      } else if (error.errores.length > 0) {
        // 400 o 422: cada error bajo su campo
        const porCampo = {}
        for (const e of error.errores) {
          porCampo[e.campo] = e.mensaje
        }
        setErrores(porCampo)
        if (!porCampo.usuario && !porCampo.password) {
          setDetalle(error.detalle)
        }
      } else {
        setDetalle(error.detalle)
      }
    }
  }

  return (
    <div className="login">
      <section className="login-panel">
        <div className="marca">
          <div className="logo logo-grande">AG</div>
          <div>
            <div className="marca-nombre">TALLER AUTO GREEN</div>
            <div className="marca-sub">SISTEMA ADMINISTRATIVO</div>
          </div>
        </div>
        <div className="login-lema">
          <h1>Control total de tu taller.</h1>
          <p>Clientes, citas, vehículos e inventario en un solo sistema.</p>
        </div>
      </section>

      <section className="login-formulario">
        <form onSubmit={entrar} noValidate>
          <h2>Bienvenido de nuevo</h2>
          <p className="texto-gris">Ingresa con tu cuenta de administrador.</p>

          <Mensaje tipo="error" texto={aviso} />
          <Mensaje tipo="error" texto={detalle} />

          <label className="campo">
            <span className="campo-etiqueta">Usuario</span>
            <input
              type="text"
              value={usuario}
              placeholder="admin"
              autoComplete="username"
              onChange={(e) => setUsuario(e.target.value)}
            />
            {errores.usuario && <span className="campo-error">{errores.usuario}</span>}
          </label>

          <label className="campo">
            <span className="campo-etiqueta">Contraseña</span>
            <input
              type="password"
              value={password}
              autoComplete="current-password"
              onChange={(e) => setPassword(e.target.value)}
            />
            {errores.password && <span className="campo-error">{errores.password}</span>}
            <span className="campo-ayuda">Acceso exclusivo para personal administrativo.</span>
          </label>

          <button type="submit" className="boton boton-principal boton-ancho" disabled={entrando}>
            {entrando ? 'Entrando…' : 'Entrar al sistema'}
          </button>

          <p className="login-olvido">¿Olvidaste tu contraseña? Contacta al responsable.</p>
        </form>
      </section>
    </div>
  )
}

export default Login
