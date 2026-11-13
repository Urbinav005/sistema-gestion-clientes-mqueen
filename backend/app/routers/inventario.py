# Endpoints del inventario: lista con búsqueda y filtro, resumen, consulta, alta, edición y baja.
# Aplica las reglas RN-01 a RN-05. Los textos se guardan sin acentos (la ñ se conserva).
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorApi
from app.models import CitaPieza, Pieza
from app.schemas import PiezaActualizar, PiezaCrear, PiezaSalida, ResumenInventario
from app.utiles import obtener_o_404, quitar_acentos

router = APIRouter(prefix="/inventario", tags=["Inventario"])

# Límites de las columnas y topes acordados (no son reglas de negocio)
LARGO_NOMBRE = 100
LARGO_DESCRIPCION = 255
TOPE_CANTIDAD = 999999
TOPE_PRECIO = Decimal("99999999.99")


def limpiar_y_validar(datos):
    """Limpia los textos y revisa todas las reglas; si hay problemas, los reporta todos juntos."""
    datos.nombre = quitar_acentos(datos.nombre.strip())
    if datos.descripcion is not None:
        datos.descripcion = quitar_acentos(datos.descripcion.strip()) or None

    errores = []

    # Un solo problema por campo: el primero que aplique
    if datos.nombre == "":
        errores.append({"campo": "nombre", "mensaje": "El nombre es obligatorio"})
    elif len(datos.nombre) > LARGO_NOMBRE:
        errores.append({"campo": "nombre", "mensaje": "El nombre no puede tener más de 100 caracteres"})

    if datos.descripcion is not None and len(datos.descripcion) > LARGO_DESCRIPCION:
        errores.append({"campo": "descripcion", "mensaje": "La descripción no puede tener más de 255 caracteres"})

    # RN-01, RN-04: la cantidad nunca puede ser negativa
    if datos.cantidad < 0:
        errores.append({"campo": "cantidad", "mensaje": "La cantidad no puede ser negativa"})
    elif datos.cantidad > TOPE_CANTIDAD:
        errores.append({"campo": "cantidad", "mensaje": "La cantidad no puede pasar de 999999"})

    # RN-04: el stock mínimo no puede ser negativo
    if datos.stock_minimo < 0:
        errores.append({"campo": "stock_minimo", "mensaje": "El stock mínimo no puede ser negativo"})
    elif datos.stock_minimo > TOPE_CANTIDAD:
        errores.append({"campo": "stock_minimo", "mensaje": "El stock mínimo no puede pasar de 999999"})

    # RN-03: el precio debe ser mayor a 0
    precio = datos.precio_unitario
    if precio <= 0:
        errores.append({"campo": "precio_unitario", "mensaje": "El precio debe ser mayor a 0"})
    # El tope va antes que los decimales: quantize falla con números de más de 28 dígitos
    elif precio > TOPE_PRECIO:
        errores.append({"campo": "precio_unitario", "mensaje": "El precio es demasiado alto"})
    elif precio != precio.quantize(Decimal("0.01")):
        errores.append({"campo": "precio_unitario", "mensaje": "El precio solo puede tener 2 decimales"})

    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)
    return datos


def revisar_nombre_repetido(db, nombre, id_excluir=None):
    """Lanza 409 si otra pieza ya tiene ese nombre (sin distinguir mayúsculas)."""
    consulta = select(Pieza.id_pieza).where(func.lower(Pieza.nombre) == nombre.lower())
    if id_excluir is not None:
        consulta = consulta.where(Pieza.id_pieza != id_excluir)
    if db.scalars(consulta).first() is not None:
        mensaje = "Ya existe una pieza con ese nombre"
        raise ErrorApi(409, mensaje, [{"campo": "nombre", "mensaje": mensaje}])


def buscar_pieza(db, id_pieza):
    """Devuelve la pieza o lanza 404."""
    return obtener_o_404(db, Pieza, id_pieza, "La pieza no existe")


@router.get("", response_model=list[PiezaSalida])
def listar_inventario(
    buscar: str | None = None,
    stock_bajo: bool | None = None,
    db: Session = Depends(get_db),
):
    consulta = select(Pieza).order_by(Pieza.nombre)

    if buscar is not None:
        texto = quitar_acentos(buscar.strip())
        if texto:
            # autoescape: % y _ se buscan como caracteres normales, no como comodines
            consulta = consulta.where(
                Pieza.nombre.icontains(texto, autoescape=True)
                | Pieza.descripcion.icontains(texto, autoescape=True)
            )

    # RN-02: filtro de stock bajo, hecho en la consulta
    if stock_bajo is True:
        consulta = consulta.where(Pieza.cantidad <= Pieza.stock_minimo)
    elif stock_bajo is False:
        consulta = consulta.where(Pieza.cantidad > Pieza.stock_minimo)

    return db.scalars(consulta).all()


# Va antes de /{id_pieza}: si no, FastAPI tomaría "resumen" como un id
@router.get("/resumen", response_model=ResumenInventario)
def resumen_inventario(db: Session = Depends(get_db)):
    total_piezas = db.scalar(select(func.count(Pieza.id_pieza)))
    # RN-02: cuántas piezas tienen stock bajo
    stock_bajo = db.scalar(
        select(func.count(Pieza.id_pieza)).where(Pieza.cantidad <= Pieza.stock_minimo)
    )
    # RN-05: valor del inventario = suma de cantidad × precio_unitario
    valor = db.scalar(
        select(func.coalesce(func.sum(Pieza.cantidad * Pieza.precio_unitario), 0))
    )
    return {
        "total_piezas": total_piezas,
        "stock_bajo": stock_bajo,
        "valor_inventario": Decimal(valor).quantize(Decimal("0.01")),
    }


@router.get("/{id_pieza}", response_model=PiezaSalida)
def obtener_pieza(id_pieza: int, db: Session = Depends(get_db)):
    return buscar_pieza(db, id_pieza)


@router.post("", response_model=PiezaSalida, status_code=201)
def crear_pieza(datos: PiezaCrear, db: Session = Depends(get_db)):
    limpiar_y_validar(datos)
    revisar_nombre_repetido(db, datos.nombre)

    pieza = Pieza(**datos.model_dump())
    db.add(pieza)
    db.commit()
    db.refresh(pieza)
    return pieza


@router.put("/{id_pieza}", response_model=PiezaSalida)
def actualizar_pieza(id_pieza: int, datos: PiezaActualizar, db: Session = Depends(get_db)):
    pieza = buscar_pieza(db, id_pieza)
    limpiar_y_validar(datos)
    revisar_nombre_repetido(db, datos.nombre, id_excluir=id_pieza)

    # Ajuste manual: se reemplazan los 5 campos
    pieza.nombre = datos.nombre
    pieza.descripcion = datos.descripcion
    pieza.cantidad = datos.cantidad
    pieza.stock_minimo = datos.stock_minimo
    pieza.precio_unitario = datos.precio_unitario
    db.commit()
    db.refresh(pieza)
    return pieza


@router.delete("/{id_pieza}", status_code=204)
def eliminar_pieza(id_pieza: int, db: Session = Depends(get_db)):
    pieza = buscar_pieza(db, id_pieza)

    usos = db.scalar(select(func.count(CitaPieza.id_cita)).where(CitaPieza.id_pieza == id_pieza))
    if usos > 0:
        raise ErrorApi(409, "No se puede eliminar: la pieza ya se usó en citas")

    db.delete(pieza)
    db.commit()
