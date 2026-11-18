// Agenda de citas (mockup 05): tira de la semana (lunes a domingo), filtro por estado
// y las citas del día elegido, ordenadas por hora.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listarCitas } from '../api.js'
import EtiquetaCita from '../components/EtiquetaCita.jsx'
import Mensaje from '../components/Mensaje.jsx'
import { MESES, TEXTO_DIA, fechaParaApi, formatoHora } from '../formato.js'

// RN-06: los únicos estados de una cita
const ESTADOS = ['Pendiente', 'En proceso', 'Terminada', 'Cancelada']

// Un día a medianoche, para comparar días sin la hora
function soloDia(fecha) {
  return new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate())
}

function sumarDias(fecha, dias) {
  return new Date(fecha.getFullYear(), fecha.getMonth(), fecha.getDate() + dias)
}

function mismoDia(a, b) {
  return fechaParaApi(a) === fechaParaApi(b)
}

// Los 7 días de la semana del día elegido, de lunes a domingo
function semanaDe(dia) {
  const lunes = sumarDias(dia, -((dia.getDay() + 6) % 7))
  return Array.from({ length: 7 }, (_, i) => sumarDias(lunes, i))
}

function Citas() {
  // Se calcula una vez al entrar a la página
  const [hoy] = useState(() => soloDia(new Date()))
  const [dia, setDia] = useState(hoy)
  const [estado, setEstado] = useState('')
  // La lista recuerda de qué día y filtro es: si no coincide, todavía está cargando
  const [resultado, setResultado] = useState(null)
  const [error, setError] = useState('')

  const clave = `${fechaParaApi(dia)}|${estado}`
  const citas = resultado && resultado.clave === clave ? resultado.citas : null

  // Sin espera de 300 ms: aquí no se escribe
  useEffect(() => {
    let vigente = true
    listarCitas({ fecha: fechaParaApi(dia), estado })
      .then((datos) => {
        if (!vigente) return
        // El backend las manda de la más reciente a la más antigua; aquí van por hora
        const ordenadas = [...datos].sort((a, b) => a.fecha.localeCompare(b.fecha))
        setResultado({ clave: `${fechaParaApi(dia)}|${estado}`, citas: ordenadas })
        setError('')
      })
      .catch((e) => vigente && setError(e.detalle))
    return () => {
      vigente = false
    }
  }, [dia, estado])

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">Agenda de citas</h1>
          <p className="pagina-subtitulo">
            Programa y consulta las visitas de los vehículos al taller.
          </p>
        </div>
        <Link to="/citas/nueva" className="boton boton-principal">
          + Agendar cita
        </Link>
      </div>

      <div className="tarjeta semana">
        <div className="semana-encabezado">
          <span className="semana-mes">
            {MESES[dia.getMonth()]} {dia.getFullYear()}
          </span>
          <div className="semana-navegacion">
            <button type="button" className="boton boton-secundario" onClick={() => setDia(sumarDias(dia, -7))}>
              ‹ Semana anterior
            </button>
            <button type="button" className="boton boton-secundario" onClick={() => setDia(hoy)}>
              Hoy
            </button>
            <button type="button" className="boton boton-secundario" onClick={() => setDia(sumarDias(dia, 7))}>
              Semana siguiente ›
            </button>
          </div>
        </div>
        <div className="semana-dias">
          {semanaDe(dia).map((d) => (
            <button
              key={fechaParaApi(d)}
              type="button"
              className={mismoDia(d, dia) ? 'semana-dia elegido' : 'semana-dia'}
              onClick={() => setDia(d)}
            >
              <span className="semana-dia-nombre">{TEXTO_DIA[d.getDay()]}</span>
              <span className="semana-dia-numero">{d.getDate()}</span>
              {mismoDia(d, hoy) && <span className="semana-dia-hoy">Hoy</span>}
            </button>
          ))}
        </div>
      </div>

      <div className="filtros">
        <select value={estado} onChange={(e) => setEstado(e.target.value)} aria-label="Estado">
          <option value="">Todos</option>
          {ESTADOS.map((nombre) => (
            <option key={nombre} value={nombre}>
              {nombre}
            </option>
          ))}
        </select>
      </div>

      <Mensaje tipo="error" texto={error} />

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Citas programadas</h2>
        {citas === null ? (
          error ? null : <p className="texto-gris">Cargando…</p>
        ) : citas.length === 0 ? (
          <p className="texto-gris">No hay citas para este día.</p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Hora</th>
                <th>Cliente</th>
                <th>Vehículo</th>
                <th>Servicio</th>
                <th>Estado</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {citas.map((cita) => (
                <tr key={cita.id_cita}>
                  <td className="producto-nombre">{formatoHora(cita.fecha)}</td>
                  <td className="texto-gris">{cita.vehiculo.cliente.nombre}</td>
                  <td className="texto-gris">
                    {cita.vehiculo.marca} {cita.vehiculo.modelo} {cita.vehiculo.anio ?? ''}
                  </td>
                  <td className="texto-gris">{cita.motivo}</td>
                  <td>
                    <EtiquetaCita estado={cita.estado} />
                  </td>
                  <td className="acciones">
                    <Link to={`/citas/${cita.id_cita}`} className="enlace">
                      Ver
                    </Link>
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

export default Citas
