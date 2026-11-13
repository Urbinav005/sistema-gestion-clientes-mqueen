// Aviso de error (rojo) o de éxito (verde). Si no hay texto, no muestra nada.
function Mensaje({ tipo, texto }) {
  if (!texto) {
    return null
  }
  return (
    <div className={`mensaje mensaje-${tipo}`} role={tipo === 'error' ? 'alert' : 'status'}>
      {texto}
    </div>
  )
}

export default Mensaje
