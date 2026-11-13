// Etiqueta de color con el nivel de stock (RN-16) que manda el backend:
// verde Suficiente, amarilla Stock bajo y roja Crítico.
import { TEXTO_ESTADO } from '../formato.js'

function EtiquetaStock({ estado }) {
  return <span className={`etiqueta etiqueta-${estado}`}>{TEXTO_ESTADO[estado] || estado}</span>
}

export default EtiquetaStock
