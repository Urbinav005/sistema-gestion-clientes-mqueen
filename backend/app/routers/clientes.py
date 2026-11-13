# Endpoints de clientes: lista con búsqueda, consulta con vehículos, alta, edición,
# baja lógica y reactivación. Nada se borra de verdad: la baja pone activo = false.
import re

from fastapi import APIRouter, Depends
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorApi
from app.models import Cita, Cliente, Vehiculo
from app.schemas import ClienteActualizar, ClienteCrear, ClienteDetalle, ClienteSalida
from app.utiles import obtener_o_404, quitar_acentos

router = APIRouter(prefix="/clientes", tags=["Clientes"])

LARGO_NOMBRE = 100
LARGO_TELEFONO = 15
LARGO_CORREO = 100
MIN_DIGITOS_TELEFONO = 7
# Dígitos, espacios, +, - y paréntesis
PATRON_TELEFONO = re.compile(r"^[0-9 +\-()]+$")
# algo@algo.algo, sin espacios y con un solo @
PATRON_CORREO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MENSAJE_NO_EXISTE = "El cliente no existe"


def limpiar_y_validar_cliente(datos):
    """Limpia los textos y revisa todos los campos; reporta todos los problemas juntos."""
    datos.nombre = quitar_acentos(datos.nombre.strip())
    datos.telefono = datos.telefono.strip()
    if datos.correo is not None:
        # El correo no pierde acentos; se guarda en minúsculas y vacío = nulo
        datos.correo = datos.correo.strip().lower() or None

    errores = []

    if datos.nombre == "":
        errores.append({"campo": "nombre", "mensaje": "El nombre es obligatorio"})
    elif len(datos.nombre) > LARGO_NOMBRE:
        errores.append({"campo": "nombre", "mensaje": "El nombre no puede tener más de 100 caracteres"})

    digitos = sum(1 for c in datos.telefono if c.isdigit())
    if datos.telefono == "":
        errores.append({"campo": "telefono", "mensaje": "El teléfono es obligatorio"})
    elif not PATRON_TELEFONO.match(datos.telefono):
        errores.append({"campo": "telefono", "mensaje": "El teléfono solo puede llevar números, espacios, +, - y paréntesis"})
    elif digitos < MIN_DIGITOS_TELEFONO or len(datos.telefono) > LARGO_TELEFONO:
        errores.append({"campo": "telefono", "mensaje": "El teléfono debe tener entre 7 dígitos y 15 caracteres"})

    if datos.correo is not None:
        if len(datos.correo) > LARGO_CORREO:
            errores.append({"campo": "correo", "mensaje": "El correo no puede tener más de 100 caracteres"})
        elif not PATRON_CORREO.match(datos.correo):
            errores.append({"campo": "correo", "mensaje": "El correo no tiene un formato válido"})

    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)
    return datos


@router.get("", response_model=list[ClienteSalida])
def listar_clientes(
    buscar: str | None = None,
    incluir_inactivos: bool = False,
    db: Session = Depends(get_db),
):
    consulta = select(Cliente).order_by(Cliente.nombre)

    if not incluir_inactivos:
        consulta = consulta.where(Cliente.activo.is_(True))

    if buscar is not None:
        texto = quitar_acentos(buscar.strip())
        if texto:
            consulta = consulta.where(
                or_(
                    Cliente.nombre.icontains(texto, autoescape=True),
                    Cliente.telefono.icontains(texto, autoescape=True),
                    Cliente.correo.icontains(texto, autoescape=True),
                )
            )

    return db.scalars(consulta).all()


@router.get("/{id_cliente}", response_model=ClienteDetalle)
def obtener_cliente(id_cliente: int, db: Session = Depends(get_db)):
    # Por id sí se devuelven clientes inactivos, para que los tickets viejos sigan funcionando
    return obtener_o_404(db, Cliente, id_cliente, MENSAJE_NO_EXISTE)


@router.post("", response_model=ClienteSalida, status_code=201)
def crear_cliente(datos: ClienteCrear, db: Session = Depends(get_db)):
    limpiar_y_validar_cliente(datos)
    cliente = Cliente(**datos.model_dump())
    db.add(cliente)
    db.commit()
    # refresh: lee creado_en y activo, que los pone la base
    db.refresh(cliente)
    return cliente


@router.put("/{id_cliente}", response_model=ClienteSalida)
def actualizar_cliente(id_cliente: int, datos: ClienteActualizar, db: Session = Depends(get_db)):
    cliente = obtener_o_404(db, Cliente, id_cliente, MENSAJE_NO_EXISTE)
    limpiar_y_validar_cliente(datos)

    cliente.nombre = datos.nombre
    cliente.telefono = datos.telefono
    cliente.correo = datos.correo
    db.commit()
    db.refresh(cliente)
    return cliente


@router.delete("/{id_cliente}", status_code=204)
def dar_de_baja_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = obtener_o_404(db, Cliente, id_cliente, MENSAJE_NO_EXISTE)

    # No se da de baja a quien tiene trabajo abierto en el taller
    abiertas = db.scalar(
        select(func.count(Cita.id_cita))
        .join(Vehiculo, Cita.id_vehiculo == Vehiculo.id_vehiculo)
        .where(Vehiculo.id_cliente == id_cliente)
        .where(Cita.estado.in_(["Pendiente", "En proceso"]))
    )
    if abiertas > 0:
        raise ErrorApi(409, "No se puede dar de baja: el cliente tiene citas pendientes o en proceso")

    # Baja lógica: no se borra nada; sus vehículos quedan ocultos porque su cliente está inactivo
    cliente.activo = False
    db.commit()


@router.post("/{id_cliente}/reactivar", response_model=ClienteSalida)
def reactivar_cliente(id_cliente: int, db: Session = Depends(get_db)):
    cliente = obtener_o_404(db, Cliente, id_cliente, MENSAJE_NO_EXISTE)
    cliente.activo = True
    db.commit()
    db.refresh(cliente)
    return cliente
