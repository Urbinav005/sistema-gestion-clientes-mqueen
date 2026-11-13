# Endpoints de citas: lista con filtros, consulta, alta, edición, cambio de estado,
# ticket, y agregar o quitar piezas descontando o devolviendo el stock en una sola transacción.
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorApi
from app.models import Cita, CitaPieza, Pieza, Vehiculo
from app.schemas import (
    CitaActualizar,
    CitaCrear,
    CitaEstado,
    CitaSalida,
    PiezaDeCita,
    TicketSalida,
)
from app.utiles import ID_MAXIMO, obtener_o_404, quitar_acentos

router = APIRouter(prefix="/citas", tags=["Citas"])

LARGO_MOTIVO = 255
TOPE_DINERO = Decimal("99999999.99")
TOPE_CANTIDAD = 999999
MENSAJE_NO_EXISTE = "La cita no existe"

# RN-06: los únicos estados válidos
ESTADOS_VALIDOS = ["Pendiente", "En proceso", "Terminada", "Cancelada"]
MENSAJE_ESTADO = "El estado debe ser Pendiente, En proceso, Terminada o Cancelada"
# RN-11: Terminada y Cancelada no pueden pasar a ningún otro estado
CAMBIOS_PERMITIDOS = {
    "Pendiente": ["En proceso", "Cancelada"],
    "En proceso": ["Terminada", "Cancelada"],
    "Terminada": [],
    "Cancelada": [],
}
ESTADOS_CERRADOS = ["Terminada", "Cancelada"]


def buscar_cita(db, id_cita):
    """Devuelve la cita o lanza 404."""
    return obtener_o_404(db, Cita, id_cita, MENSAJE_NO_EXISTE)


def revisar_cita_abierta(cita):
    # RN-11: una cita Terminada o Cancelada queda cerrada
    if cita.estado in ESTADOS_CERRADOS:
        raise ErrorApi(409, f"La cita está {cita.estado} y ya no se puede modificar")


def validar_motivo_y_costo(datos, errores):
    """Limpia el motivo y revisa motivo y costo de mano de obra; agrega los problemas a errores."""
    datos.motivo = quitar_acentos(datos.motivo.strip())
    if datos.motivo == "":
        errores.append({"campo": "motivo", "mensaje": "El motivo es obligatorio"})
    elif len(datos.motivo) > LARGO_MOTIVO:
        errores.append({"campo": "motivo", "mensaje": "El motivo no puede tener más de 255 caracteres"})

    costo = datos.costo_mano_obra
    if costo < 0:
        errores.append({"campo": "costo_mano_obra", "mensaje": "El costo de mano de obra no puede ser negativo"})
    # El tope va antes que los decimales: quantize falla con números enormes
    elif costo > TOPE_DINERO:
        errores.append({"campo": "costo_mano_obra", "mensaje": "El costo de mano de obra es demasiado alto"})
    elif costo != costo.quantize(Decimal("0.01")):
        errores.append({"campo": "costo_mano_obra", "mensaje": "El costo de mano de obra solo puede tener 2 decimales"})


def armar_ticket(cita, aviso=None):
    """Arma el ticket de la cita: encabezado, renglones ordenados por pieza y totales (RN-09)."""
    renglones = [
        {
            "id_pieza": renglon.id_pieza,
            "nombre": renglon.pieza.nombre,
            "cantidad": renglon.cantidad,
            # RN-08: el precio congelado del renglón, no el precio actual de la pieza
            "precio_unitario": renglon.precio_unitario,
            "importe": renglon.importe,
        }
        for renglon in cita.piezas
    ]
    renglones.sort(key=lambda r: r["nombre"])
    return {
        "id_cita": cita.id_cita,
        "fecha": cita.fecha,
        "motivo": cita.motivo,
        "estado": cita.estado,
        "vehiculo": cita.vehiculo,
        "renglones": renglones,
        "costo_mano_obra": cita.costo_mano_obra,
        "subtotal_piezas": cita.subtotal_piezas,
        "total": cita.total,
        "aviso": aviso,
    }


def devolver_al_stock(db, id_pieza, cantidad):
    """Suma unidades a la existencia de una pieza, en la base (sin leer y restar en Python)."""
    db.execute(
        update(Pieza)
        .where(Pieza.id_pieza == id_pieza)
        .values(cantidad=Pieza.cantidad + cantidad)
    )


@router.get("", response_model=list[CitaSalida])
def listar_citas(
    estado: str | None = None,
    fecha: date | None = None,
    id_vehiculo: int | None = None,
    db: Session = Depends(get_db),
):
    # Si dos citas tienen la misma fecha, desempata el id más alto
    consulta = select(Cita).order_by(Cita.fecha.desc(), Cita.id_cita.desc())

    if estado is not None:
        # RN-06: solo se filtra por un estado válido
        if estado not in ESTADOS_VALIDOS:
            raise ErrorApi(400, "Revisa los datos marcados", [{"campo": "estado", "mensaje": MENSAJE_ESTADO}])
        consulta = consulta.where(Cita.estado == estado)

    if fecha is not None:
        # Las citas de ese día: desde las 00:00 hasta antes de las 00:00 del día siguiente
        inicio = datetime.combine(fecha, time.min)
        consulta = consulta.where(Cita.fecha >= inicio, Cita.fecha < inicio + timedelta(days=1))

    if id_vehiculo is not None:
        consulta = consulta.where(Cita.id_vehiculo == id_vehiculo)

    return db.scalars(consulta).all()


@router.get("/{id_cita}", response_model=CitaSalida)
def obtener_cita(id_cita: int, db: Session = Depends(get_db)):
    return buscar_cita(db, id_cita)


@router.post("", response_model=CitaSalida, status_code=201)
def crear_cita(datos: CitaCrear, db: Session = Depends(get_db)):
    errores = []

    # RN-12: toda cita pertenece a un vehículo que existe
    vehiculo = None
    if 1 <= datos.id_vehiculo <= ID_MAXIMO:
        vehiculo = db.get(Vehiculo, datos.id_vehiculo)
    if vehiculo is None:
        errores.append({"campo": "id_vehiculo", "mensaje": "El vehículo no existe"})
    elif not (vehiculo.activo and vehiculo.cliente.activo):
        errores.append({"campo": "id_vehiculo", "mensaje": "El vehículo está dado de baja"})

    validar_motivo_y_costo(datos, errores)

    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)

    # El estado no se manda: la base lo pone en 'Pendiente'
    cita = Cita(**datos.model_dump())
    db.add(cita)
    db.commit()
    db.refresh(cita)
    return cita


@router.put("/{id_cita}", response_model=CitaSalida)
def actualizar_cita(id_cita: int, datos: CitaActualizar, db: Session = Depends(get_db)):
    cita = buscar_cita(db, id_cita)
    revisar_cita_abierta(cita)

    errores = []
    validar_motivo_y_costo(datos, errores)
    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)

    cita.fecha = datos.fecha
    cita.motivo = datos.motivo
    cita.costo_mano_obra = datos.costo_mano_obra
    db.commit()
    db.refresh(cita)
    return cita


@router.put("/{id_cita}/estado", response_model=CitaSalida)
def cambiar_estado(id_cita: int, datos: CitaEstado, db: Session = Depends(get_db)):
    cita = buscar_cita(db, id_cita)
    nuevo = datos.estado

    # RN-06: solo los cuatro estados válidos
    if nuevo not in ESTADOS_VALIDOS:
        raise ErrorApi(400, "Revisa los datos marcados", [{"campo": "estado", "mensaje": MENSAJE_ESTADO}])

    # RN-11: solo los cambios de la tabla; Terminada y Cancelada no cambian
    if nuevo not in CAMBIOS_PERMITIDOS[cita.estado]:
        raise ErrorApi(409, f"No se puede pasar de {cita.estado} a {nuevo}")

    if nuevo == "Cancelada":
        # RN-10: las piezas regresan al stock; los renglones se conservan como historial
        for renglon in cita.piezas:
            devolver_al_stock(db, renglon.id_pieza, renglon.cantidad)

    cita.estado = nuevo
    # RN-07: el cambio de estado y las devoluciones se guardan juntos
    db.commit()
    db.refresh(cita)
    return cita


@router.get("/{id_cita}/ticket", response_model=TicketSalida)
def ticket_cita(id_cita: int, db: Session = Depends(get_db)):
    # RN-09: encabezado, renglones y total
    cita = buscar_cita(db, id_cita)
    return armar_ticket(cita)


@router.post("/{id_cita}/piezas", response_model=TicketSalida, status_code=201)
def agregar_pieza(id_cita: int, datos: PiezaDeCita, db: Session = Depends(get_db)):
    # 1. La cita existe y está abierta (RN-11)
    cita = buscar_cita(db, id_cita)
    revisar_cita_abierta(cita)

    # 2 y 3. Cantidad válida y pieza existente; se juntan los dos problemas
    errores = []
    if datos.cantidad < 1:
        errores.append({"campo": "cantidad", "mensaje": "La cantidad debe ser al menos 1"})
    elif datos.cantidad > TOPE_CANTIDAD:
        errores.append({"campo": "cantidad", "mensaje": "La cantidad no puede pasar de 999999"})

    pieza = None
    if 1 <= datos.id_pieza <= ID_MAXIMO:
        pieza = db.get(Pieza, datos.id_pieza)
    if pieza is None:
        errores.append({"campo": "id_pieza", "mensaje": "La pieza no existe"})

    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)

    # 4. RN-01, RN-07: descuento atómico. Solo descuenta si alcanza (cantidad >= n);
    # así dos peticiones al mismo tiempo no pueden dejar el stock negativo
    resultado = db.execute(
        update(Pieza)
        .where(Pieza.id_pieza == datos.id_pieza, Pieza.cantidad >= datos.cantidad)
        .values(cantidad=Pieza.cantidad - datos.cantidad)
        .returning(Pieza.cantidad, Pieza.stock_minimo)
    ).first()

    if resultado is None:
        # RN-01: no alcanzó; el UPDATE no cambió nada y no se hace commit
        db.refresh(pieza)
        mensaje = f"Stock insuficiente: solo hay {pieza.cantidad}"
        raise ErrorApi(400, "Revisa los datos marcados", [{"campo": "cantidad", "mensaje": mensaje}])

    queda, minimo = resultado

    # 5. RN-08: el renglón copia el precio vigente al crearse y no se vuelve a tocar
    renglon = db.get(CitaPieza, (id_cita, datos.id_pieza))
    if renglon is None:
        renglon = CitaPieza(
            id_cita=id_cita,
            id_pieza=datos.id_pieza,
            cantidad=datos.cantidad,
            precio_unitario=pieza.precio_unitario,
        )
        db.add(renglon)
    else:
        renglon.cantidad = renglon.cantidad + datos.cantidad

    # 6. RN-07: descuento y renglón en una sola transacción
    db.commit()

    # 7. RN-02: aviso si la pieza quedó en el mínimo o por debajo
    aviso = None
    if queda <= minimo:
        aviso = f"Stock bajo: quedan {queda} de {pieza.nombre}"
    return armar_ticket(cita, aviso)


@router.delete("/{id_cita}/piezas/{id_pieza}", response_model=TicketSalida)
def quitar_pieza(id_cita: int, id_pieza: int, db: Session = Depends(get_db)):
    cita = buscar_cita(db, id_cita)
    revisar_cita_abierta(cita)

    renglon = None
    if 1 <= id_pieza <= ID_MAXIMO:
        renglon = db.get(CitaPieza, (id_cita, id_pieza))
    if renglon is None:
        raise ErrorApi(404, "La cita no tiene esa pieza")

    # RN-07: devolver el stock y borrar el renglón en una sola transacción
    devolver_al_stock(db, id_pieza, renglon.cantidad)
    db.delete(renglon)
    db.commit()
    return armar_ticket(cita)
