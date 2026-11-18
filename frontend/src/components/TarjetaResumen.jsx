// Tarjeta de número: título, valor grande y subtítulo. El tono (azul, verde, amarillo,
// rojo o naranja) da el color del cuadrito; simbolo, si viene, reemplaza su letra.
const SIMBOLO = { azul: 'P', verde: '✓', amarillo: '!', rojo: '!', naranja: '!' }

function TarjetaResumen({ titulo, valor, subtitulo, tono, simbolo }) {
  return (
    <div className="tarjeta tarjeta-resumen">
      <div className="tarjeta-resumen-encabezado">
        <span className={`tarjeta-resumen-icono tono-${tono}`} aria-hidden="true">
          {simbolo || SIMBOLO[tono]}
        </span>
        <span className="tarjeta-resumen-titulo">{titulo}</span>
      </div>
      <div className="tarjeta-resumen-valor">{valor}</div>
      <div className="tarjeta-resumen-subtitulo">{subtitulo}</div>
    </div>
  )
}

export default TarjetaResumen
