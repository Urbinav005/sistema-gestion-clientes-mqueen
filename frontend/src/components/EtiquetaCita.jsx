// Etiqueta de color con el estado de una cita (RN-06): amarilla Pendiente,
// azul En proceso, verde Terminada y roja Cancelada.
const CLASE_ESTADO = {
  Pendiente: 'etiqueta-pendiente',
  'En proceso': 'etiqueta-en-proceso',
  Terminada: 'etiqueta-terminada',
  Cancelada: 'etiqueta-cancelada',
}

function EtiquetaCita({ estado }) {
  return <span className={`etiqueta ${CLASE_ESTADO[estado] || ''}`}>{estado}</span>
}

export default EtiquetaCita
