// Resumen general del taller (mockup 02), la pantalla de inicio: cuatro tarjetas,
// las próximas citas de hoy y las alertas de inventario. Todo lo calcula el backend.
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { resumenGeneral } from '../api.js'
import EtiquetaCita from '../components/EtiquetaCita.jsx'
import EtiquetaStock from '../components/EtiquetaStock.jsx'
import Mensaje from '../components/Mensaje.jsx'
import TarjetaResumen from '../components/TarjetaResumen.jsx'
import { formatoHora } from '../formato.js'

function plural(numero, singular, varios) {
  return `${numero} ${numero === 1 ? singular : varios}`
}

function Resumen() {
  const [datos, setDatos] = useState(null)
  const [error, setError] = useState('')

  // Se pide una vez al entrar; no se actualiza solo
  useEffect(() => {
    let vigente = true
    resumenGeneral()
      .then((respuesta) => vigente && setDatos(respuesta))
      .catch((e) => vigente && setError(e.detalle))
    return () => {
      vigente = false
    }
  }, [])

  return (
    <section>
      <div className="pagina-encabezado">
        <div>
          <h1 className="pagina-titulo">Resumen general</h1>
          <p className="pagina-subtitulo">Vista rápida de la actividad del taller.</p>
        </div>
      </div>

      <Mensaje tipo="error" texto={error} />

      {datos === null ? (
        error ? null : <p className="texto-gris">Cargando…</p>
      ) : (
        <>
          <div className="tarjetas">
            {/* RN-06: vehículos con una cita En proceso */}
            <TarjetaResumen
              titulo="Vehículos en taller"
              valor={datos.vehiculos_en_taller}
              subtitulo="Con servicio en proceso"
              tono="azul"
              simbolo="V"
            />
            {/* RN-06: las de hoy sin las canceladas */}
            <TarjetaResumen
              titulo="Citas de hoy"
              valor={datos.citas_hoy}
              subtitulo={plural(datos.citas_hoy_pendientes, 'pendiente', 'pendientes')}
              tono="naranja"
              simbolo="C"
            />
            <TarjetaResumen
              titulo="Clientes registrados"
              valor={datos.clientes_registrados}
              subtitulo={`+${datos.clientes_nuevos_mes} este mes`}
              tono="verde"
              simbolo="U"
            />
            {/* RN-02, RN-16: stock bajo incluye a las críticas */}
            <TarjetaResumen
              titulo="Stock bajo o crítico"
              valor={datos.stock_bajo}
              subtitulo={`${datos.stock_critico} en nivel crítico`}
              tono="rojo"
              simbolo="!"
            />
          </div>

          <div className="resumen-columnas">
            <div className="tarjeta">
              <div className="resumen-tarjeta-encabezado">
                <div>
                  <h2 className="tarjeta-titulo resumen-tarjeta-titulo">Próximas citas</h2>
                  <p className="texto-gris texto-chico">Agenda del día</p>
                </div>
                <Link to="/citas" className="enlace">
                  Ver agenda
                </Link>
              </div>
              {datos.proximas_citas.length === 0 ? (
                <p className="texto-gris">No hay citas pendientes para hoy.</p>
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
                    {datos.proximas_citas.map((cita) => (
                      <tr key={cita.id_cita}>
                        <td className="producto-nombre">{formatoHora(cita.fecha)}</td>
                        <td className="texto-gris">{cita.vehiculo.cliente.nombre}</td>
                        <td className="texto-gris">
                          {cita.vehiculo.marca} {cita.vehiculo.modelo}
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

            <div className="tarjeta">
              <div className="resumen-tarjeta-encabezado">
                <div>
                  <h2 className="tarjeta-titulo resumen-tarjeta-titulo">Alertas de inventario</h2>
                  <p className="texto-gris texto-chico">Productos que necesitan atención</p>
                </div>
                <Link to="/inventario" className="enlace">
                  Ver inventario
                </Link>
              </div>
              {datos.alertas_inventario.length === 0 ? (
                <p className="texto-gris">Todas las refacciones tienen stock suficiente.</p>
              ) : (
                <ul className="alertas">
                  {datos.alertas_inventario.map((pieza) => (
                    <li key={pieza.id_pieza}>
                      <div>
                        <div className="producto-nombre">{pieza.nombre}</div>
                        <div className="texto-gris texto-chico">
                          {plural(pieza.cantidad, 'pieza', 'piezas')}
                        </div>
                      </div>
                      {/* RN-16: el nivel que manda el backend */}
                      <EtiquetaStock estado={pieza.estado_stock} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>

          <div className="resumen-botones">
            <Link to="/clientes" className="boton boton-secundario">
              Ver clientes
            </Link>
            <Link to="/citas/nueva" className="boton boton-principal">
              Agendar cita
            </Link>
          </div>
        </>
      )}
    </section>
  )
}

export default Resumen
