# Funciones compartidas por los routers: quitar acentos, el id máximo y buscar por id o responder 404.
from app.errores import ErrorApi

# Máximo de un integer de PostgreSQL: un id mayor no puede existir
ID_MAXIMO = 2147483647

TABLA_ACENTOS = str.maketrans("áéíóúüÁÉÍÓÚÜ", "aeiouuAEIOUU")


def quitar_acentos(texto):
    """Cambia las vocales con acento o diéresis por la vocal sola. La ñ se conserva."""
    return texto.translate(TABLA_ACENTOS)


def obtener_o_404(db, modelo, id, mensaje):
    """Devuelve el registro con ese id o lanza ErrorApi(404, mensaje)."""
    # Fuera de rango no se consulta la base: la consulta fallaría con un 500
    if id < 1 or id > ID_MAXIMO:
        raise ErrorApi(404, mensaje)
    registro = db.get(modelo, id)
    if registro is None:
        raise ErrorApi(404, mensaje)
    return registro
