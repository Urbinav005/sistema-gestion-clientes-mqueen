// Tarjeta de número del inventario: título, valor grande y subtítulo.
// El tono (azul, verde, amarillo o rojo) da el color del cuadrito de la izquierda.
const SIMBOLO = { azul: 'P', verde: '✓', amarillo: '!', rojo: '!' }

function TarjetaResumen({ titulo, valor, subtitulo, tono }) {
  return (
    <div className="tarjeta tarjeta-resumen">
      <div className="tarjeta-resumen-encabezado">
        <span className={`tarjeta-resumen-icono tono-${tono}`} aria-hidden="true">
          {SIMBOLO[tono]}
        </span>
        <span className="tarjeta-resumen-titulo">{titulo}</span>
      </div>
      <div className="tarjeta-resumen-valor">{valor}</div>
      <div className="tarjeta-resumen-subtitulo">{subtitulo}</div>
    </div>
  )
}

export default TarjetaResumen
