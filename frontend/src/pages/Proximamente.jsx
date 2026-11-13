// Aviso para las secciones del menú que todavía no tienen pantalla.
function Proximamente({ titulo }) {
  return (
    <section>
      <h1 className="pagina-titulo">{titulo}</h1>
      <p className="pagina-subtitulo">Esta sección estará disponible próximamente.</p>
    </section>
  )
}

export default Proximamente
