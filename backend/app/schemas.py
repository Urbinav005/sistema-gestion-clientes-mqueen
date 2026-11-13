# Modelos Pydantic de salida: definen qué datos regresa la API en formato JSON.
# El dinero va como Decimal (sale como texto "95.00"), nunca como float.
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PiezaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_pieza: int
    nombre: str
    descripcion: str | None
    cantidad: int
    stock_minimo: int
    precio_unitario: Decimal
    stock_bajo: bool


class PiezaCrear(BaseModel):
    # Solo tipos: las reglas (RN-01, RN-03, RN-04) se revisan en el router
    nombre: str
    descripcion: str | None = None
    cantidad: int
    stock_minimo: int
    precio_unitario: Decimal


class PiezaActualizar(PiezaCrear):
    """PUT reemplaza la pieza completa: pide los mismos campos que el alta."""


class ResumenInventario(BaseModel):
    total_piezas: int
    stock_bajo: int
    valor_inventario: Decimal


# ---------- Clientes ----------

class ClienteCorto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cliente: int
    nombre: str
    telefono: str


class ClienteSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cliente: int
    nombre: str
    telefono: str
    correo: str | None
    creado_en: datetime
    activo: bool


class ClienteCrear(BaseModel):
    # Solo tipos: las reglas se revisan en el router
    nombre: str
    telefono: str
    correo: str | None = None


class ClienteActualizar(ClienteCrear):
    """PUT reemplaza los datos del cliente: pide los mismos campos que el alta."""


# ---------- Vehículos ----------

class VehiculoCorto(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_vehiculo: int
    placas: str
    marca: str
    modelo: str
    anio: int | None
    cliente: ClienteCorto


class VehiculoSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_vehiculo: int
    id_cliente: int
    placas: str
    marca: str
    modelo: str
    anio: int | None
    kilometraje: int | None
    activo: bool
    cliente: ClienteCorto


class ClienteDetalle(ClienteSalida):
    """Un cliente con sus vehículos."""

    vehiculos: list[VehiculoSalida]


class VehiculoCrear(BaseModel):
    # Solo tipos: las reglas (RN-12 y límites) se revisan en el router
    id_cliente: int
    placas: str
    marca: str
    modelo: str
    anio: int | None = None
    kilometraje: int | None = None


class VehiculoActualizar(VehiculoCrear):
    """PUT reemplaza los datos del vehículo: pide los mismos campos que el alta."""


# ---------- Citas y ticket ----------

class CitaSalida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id_cita: int
    id_vehiculo: int
    fecha: datetime
    motivo: str
    estado: str
    costo_mano_obra: Decimal | None
    vehiculo: VehiculoCorto
    total: Decimal


class RenglonTicket(BaseModel):
    id_pieza: int
    nombre: str
    cantidad: int
    precio_unitario: Decimal
    importe: Decimal


class TicketSalida(BaseModel):
    id_cita: int
    fecha: datetime
    motivo: str
    estado: str
    vehiculo: VehiculoCorto
    renglones: list[RenglonTicket]
    costo_mano_obra: Decimal | None
    subtotal_piezas: Decimal
    total: Decimal
    aviso: str | None


class CitaCrear(BaseModel):
    # Solo tipos: las reglas se revisan en el router. El estado no se manda: nace Pendiente
    id_vehiculo: int
    fecha: datetime
    motivo: str
    costo_mano_obra: Decimal = Decimal("0")


class CitaActualizar(BaseModel):
    # No permite cambiar el vehículo
    fecha: datetime
    motivo: str
    costo_mano_obra: Decimal


class CitaEstado(BaseModel):
    estado: str


class PiezaDeCita(BaseModel):
    id_pieza: int
    cantidad: int
