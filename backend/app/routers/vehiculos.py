# Endpoints de vehículos: lista con búsqueda y filtros, consulta, historial de citas,
# alta, edición, baja lógica y reactivación. Las placas se guardan en mayúsculas.
from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorApi
from app.models import Cita, Cliente, Vehiculo
from app.schemas import CitaSalida, VehiculoActualizar, VehiculoCrear, VehiculoSalida
from app.utiles import ID_MAXIMO, obtener_o_404, quitar_acentos

router = APIRouter(prefix="/vehiculos", tags=["Vehiculos"])

LARGO_PLACAS = 15
LARGO_MARCA_MODELO = 50
ANIO_MINIMO = 1950
ANIO_MAXIMO = 2100
TOPE_KILOMETRAJE = 9999999
MENSAJE_NO_EXISTE = "El vehículo no existe"


def limpiar_y_validar_vehiculo(db, datos):
    """Limpia los textos y revisa todos los campos; reporta todos los problemas juntos."""
    datos.placas = quitar_acentos(datos.placas.strip()).upper()
    datos.marca = quitar_acentos(datos.marca.strip())
    datos.modelo = quitar_acentos(datos.modelo.strip())

    errores = []

    # RN-12: todo vehículo pertenece a un cliente que existe
    cliente = None
    if 1 <= datos.id_cliente <= ID_MAXIMO:
        cliente = db.get(Cliente, datos.id_cliente)
    if cliente is None:
        errores.append({"campo": "id_cliente", "mensaje": "El cliente no existe"})
    elif not cliente.activo:
        errores.append({"campo": "id_cliente", "mensaje": "El cliente está dado de baja"})

    if datos.placas == "":
        errores.append({"campo": "placas", "mensaje": "Las placas son obligatorias"})
    elif len(datos.placas) > LARGO_PLACAS:
        errores.append({"campo": "placas", "mensaje": "Las placas no pueden tener más de 15 caracteres"})

    if datos.marca == "":
        errores.append({"campo": "marca", "mensaje": "La marca es obligatoria"})
    elif len(datos.marca) > LARGO_MARCA_MODELO:
        errores.append({"campo": "marca", "mensaje": "La marca no puede tener más de 50 caracteres"})

    if datos.modelo == "":
        errores.append({"campo": "modelo", "mensaje": "El modelo es obligatorio"})
    elif len(datos.modelo) > LARGO_MARCA_MODELO:
        errores.append({"campo": "modelo", "mensaje": "El modelo no puede tener más de 50 caracteres"})

    if datos.anio is not None and not (ANIO_MINIMO <= datos.anio <= ANIO_MAXIMO):
        errores.append({"campo": "anio", "mensaje": "El año debe estar entre 1950 y 2100"})

    if datos.kilometraje is not None:
        if datos.kilometraje < 0:
            errores.append({"campo": "kilometraje", "mensaje": "El kilometraje no puede ser negativo"})
        elif datos.kilometraje > TOPE_KILOMETRAJE:
            errores.append({"campo": "kilometraje", "mensaje": "El kilometraje no puede pasar de 9999999"})

    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)
    return datos


def revisar_placas_repetidas(db, placas, id_excluir=None):
    """Lanza 409 si otro vehículo ya tiene esas placas."""
    consulta = select(Vehiculo).where(func.upper(Vehiculo.placas) == placas)
    if id_excluir is not None:
        consulta = consulta.where(Vehiculo.id_vehiculo != id_excluir)
    otro = db.scalars(consulta).first()
    if otro is None:
        return

    # Un vehículo cuenta como activo solo si él y su cliente están activos
    if otro.activo and otro.cliente.activo:
        mensaje = "Ya existe un vehículo con esas placas"
    else:
        mensaje = "Ya existe un vehículo con esas placas, pero está dado de baja. Reactívalo."
    raise ErrorApi(409, mensaje, [{"campo": "placas", "mensaje": mensaje}])


@router.get("", response_model=list[VehiculoSalida])
def listar_vehiculos(
    buscar: str | None = None,
    id_cliente: int | None = None,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
):
    consulta = (
        select(Vehiculo)
        .join(Cliente, Vehiculo.id_cliente == Cliente.id_cliente)
        .order_by(Vehiculo.placas)
    )

    # Activo = el vehículo y su cliente están activos
    if not incluir_inactivos:
        consulta = consulta.where(Vehiculo.activo.is_(True), Cliente.activo.is_(True))

    if id_cliente is not None:
        consulta = consulta.where(Vehiculo.id_cliente == id_cliente)

    if buscar is not None:
        texto = quitar_acentos(buscar.strip())
        if texto:
            consulta = consulta.where(
                or_(
                    Vehiculo.placas.icontains(texto, autoescape=True),
                    Vehiculo.marca.icontains(texto, autoescape=True),
                    Vehiculo.modelo.icontains(texto, autoescape=True),
                )
            )

    return db.scalars(consulta).all()


@router.get("/{id_vehiculo}", response_model=VehiculoSalida)
def obtener_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    return obtener_o_404(db, Vehiculo, id_vehiculo, MENSAJE_NO_EXISTE)


@router.get("/{id_vehiculo}/historial", response_model=list[CitaSalida])
def historial_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    # RF-12: todas las citas del vehículo, la más reciente primero
    obtener_o_404(db, Vehiculo, id_vehiculo, MENSAJE_NO_EXISTE)
    consulta = (
        select(Cita)
        .where(Cita.id_vehiculo == id_vehiculo)
        .order_by(Cita.fecha.desc(), Cita.id_cita.desc())
    )
    return db.scalars(consulta).all()


@router.post("", response_model=VehiculoSalida, status_code=201)
def crear_vehiculo(datos: VehiculoCrear, db: Session = Depends(get_db)):
    limpiar_y_validar_vehiculo(db, datos)
    revisar_placas_repetidas(db, datos.placas)

    vehiculo = Vehiculo(**datos.model_dump())
    db.add(vehiculo)
    db.commit()
    # refresh: lee activo, que lo pone la base
    db.refresh(vehiculo)
    return vehiculo


@router.put("/{id_vehiculo}", response_model=VehiculoSalida)
def actualizar_vehiculo(id_vehiculo: int, datos: VehiculoActualizar, db: Session = Depends(get_db)):
    vehiculo = obtener_o_404(db, Vehiculo, id_vehiculo, MENSAJE_NO_EXISTE)
    limpiar_y_validar_vehiculo(db, datos)
    revisar_placas_repetidas(db, datos.placas, id_excluir=id_vehiculo)

    vehiculo.id_cliente = datos.id_cliente
    vehiculo.placas = datos.placas
    vehiculo.marca = datos.marca
    vehiculo.modelo = datos.modelo
    vehiculo.anio = datos.anio
    vehiculo.kilometraje = datos.kilometraje
    db.commit()
    db.refresh(vehiculo)
    return vehiculo


@router.delete("/{id_vehiculo}", status_code=204)
def dar_de_baja_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    vehiculo = obtener_o_404(db, Vehiculo, id_vehiculo, MENSAJE_NO_EXISTE)

    abiertas = db.scalar(
        select(func.count(Cita.id_cita))
        .where(Cita.id_vehiculo == id_vehiculo)
        .where(Cita.estado.in_(["Pendiente", "En proceso"]))
    )
    if abiertas > 0:
        raise ErrorApi(409, "No se puede dar de baja: el vehículo tiene citas pendientes o en proceso")

    # Baja lógica: no se borra nada
    vehiculo.activo = False
    db.commit()


@router.post("/{id_vehiculo}/reactivar", response_model=VehiculoSalida)
def reactivar_vehiculo(id_vehiculo: int, db: Session = Depends(get_db)):
    vehiculo = obtener_o_404(db, Vehiculo, id_vehiculo, MENSAJE_NO_EXISTE)
    vehiculo.activo = True
    db.commit()
    db.refresh(vehiculo)
    return vehiculo
