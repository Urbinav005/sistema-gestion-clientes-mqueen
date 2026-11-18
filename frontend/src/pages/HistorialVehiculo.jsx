// Historial de citas de un vehículo (RF-12, no está en Figma): fecha, motivo, estado y total
// de cada cita, con enlace a su detalle.
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { historialVehiculo, obtenerVehiculo } from '../api.js'
import EtiquetaCita from '../components/EtiquetaCita.jsx'
import Mensaje from '../components/Mensaje.jsx'
import { formatoDinero, formatoFecha, formatoHora } from '../formato.js'

function HistorialVehiculo() {
  const { id_vehiculo } = useParams()
  const [vehiculo, setVehiculo] = useState(null)
  const [citas, setCitas] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    let vigente = true
    Promise.all([obtenerVehiculo(id_vehiculo), historialVehiculo(id_vehiculo)])
      .then(([datosVehiculo, datosCitas]) => {
        if (!vigente) return
        setVehiculo(datosVehiculo)
        setCitas(datosCitas)
      })
      .catch((e) => vigente && setError(e.detalle))
    return () => {
      vigente = false
    }
  }, [id_vehiculo])

  const volver = (
    <Link to="/vehiculos" className="enlace">
      Volver a vehículos
    </Link>
  )

  if (error) {
    return (
      <section>
        <Mensaje tipo="error" texto={error} />
        {volver}
      </section>
    )
  }

  if (vehiculo === null) {
    return <p className="texto-gris">Cargando…</p>
  }

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">
            Historial de {vehiculo.marca} {vehiculo.modelo}
          </h1>
          <p className="pagina-subtitulo">
            {vehiculo.placas} · {vehiculo.cliente.nombre}
          </p>
        </div>
        {volver}
      </div>

      <div className="tarjeta">
        <h2 className="tarjeta-titulo">Citas del vehículo</h2>
        {citas.length === 0 ? (
          <p className="texto-gris">Este vehículo todavía no tiene citas.</p>
        ) : (
          <table className="tabla">
            <thead>
              <tr>
                <th>Fecha</th>
                <th>Hora</th>
                <th>Motivo</th>
                <th>Estado</th>
                <th>Total</th>
                <th>Acciones</th>
              </tr>
            </thead>
            <tbody>
              {citas.map((cita) => (
                <tr key={cita.id_cita}>
                  <td>{formatoFecha(cita.fecha)}</td>
                  <td className="texto-gris">{formatoHora(cita.fecha)}</td>
                  <td className="texto-gris">{cita.motivo}</td>
                  <td>
                    <EtiquetaCita estado={cita.estado} />
                  </td>
                  {/* RN-09: el total lo calcula el backend */}
                  <td>{formatoDinero(cita.total)}</td>
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

export default HistorialVehiculo
