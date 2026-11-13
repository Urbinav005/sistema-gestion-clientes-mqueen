# Modelos ORM de SQLAlchemy: mapean las 6 tablas que ya existen en el esquema "BD".
# Solo describen las tablas; nunca las crean (prohibido create_all).
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func, text, true
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.db import ESQUEMA

CENTAVO = Decimal("0.01")


class Base(DeclarativeBase):
    """Clase base de todos los modelos."""


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = {"schema": ESQUEMA}

    id_cliente: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    telefono: Mapped[str] = mapped_column(String(15))
    correo: Mapped[str | None] = mapped_column(String(100))
    # server_default: si no se manda, la base pone el valor (no crea nada)
    creado_en: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # Baja lógica: false = dado de baja
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())

    vehiculos: Mapped[list["Vehiculo"]] = relationship(back_populates="cliente")


class Vehiculo(Base):
    __tablename__ = "vehiculos"
    __table_args__ = {"schema": ESQUEMA}

    id_vehiculo: Mapped[int] = mapped_column(Integer, primary_key=True)
    # RN-12: todo vehículo pertenece a un cliente
    id_cliente: Mapped[int] = mapped_column(ForeignKey(f"{ESQUEMA}.clientes.id_cliente"))
    placas: Mapped[str] = mapped_column(String(15))
    marca: Mapped[str] = mapped_column(String(50))
    modelo: Mapped[str] = mapped_column(String(50))
    anio: Mapped[int | None] = mapped_column(Integer)
    kilometraje: Mapped[int | None] = mapped_column(Integer)
    # Baja lógica: false = dado de baja
    activo: Mapped[bool] = mapped_column(Boolean, server_default=true())

    cliente: Mapped["Cliente"] = relationship(back_populates="vehiculos")
    citas: Mapped[list["Cita"]] = relationship(back_populates="vehiculo")


class Cita(Base):
    __tablename__ = "citas"
    __table_args__ = {"schema": ESQUEMA}

    id_cita: Mapped[int] = mapped_column(Integer, primary_key=True)
    # RN-12: toda cita pertenece a un vehículo
    id_vehiculo: Mapped[int] = mapped_column(ForeignKey(f"{ESQUEMA}.vehiculos.id_vehiculo"))
    fecha: Mapped[datetime] = mapped_column(DateTime)
    motivo: Mapped[str] = mapped_column(String(255))
    # RN-06: la base solo acepta Pendiente, En proceso, Terminada o Cancelada
    estado: Mapped[str] = mapped_column(String(20), server_default=text("'Pendiente'"))
    costo_mano_obra: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), server_default=text("0"))

    vehiculo: Mapped["Vehiculo"] = relationship(back_populates="citas")
    piezas: Mapped[list["CitaPieza"]] = relationship(back_populates="cita")

    @property
    def subtotal_piezas(self):
        # RN-10: una cita cancelada no cobra sus piezas
        if self.estado == "Cancelada":
            return Decimal("0.00")
        suma = sum((renglon.importe for renglon in self.piezas), Decimal("0"))
        return suma.quantize(CENTAVO)

    @property
    def total(self):
        # RN-09: total = mano de obra + suma de los renglones; RN-10: cancelada vale 0
        if self.estado == "Cancelada":
            return Decimal("0.00")
        mano_obra = self.costo_mano_obra or Decimal("0")
        return (mano_obra + self.subtotal_piezas).quantize(CENTAVO)


class Pieza(Base):
    """Una fila de la tabla inventario: una refacción del taller."""

    __tablename__ = "inventario"
    __table_args__ = {"schema": ESQUEMA}

    id_pieza: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(String(255))
    cantidad: Mapped[int] = mapped_column(Integer)
    stock_minimo: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    usos: Mapped[list["CitaPieza"]] = relationship(back_populates="pieza")

    @property
    def stock_bajo(self):
        # RN-02: hay stock bajo cuando la cantidad es menor o igual al stock mínimo
        return self.cantidad <= self.stock_minimo


class CitaPieza(Base):
    """Una fila de citas_inventario: una pieza usada en una cita (renglón del ticket)."""

    __tablename__ = "citas_inventario"
    __table_args__ = {"schema": ESQUEMA}

    id_cita: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA}.citas.id_cita"), primary_key=True
    )
    id_pieza: Mapped[int] = mapped_column(
        ForeignKey(f"{ESQUEMA}.inventario.id_pieza"), primary_key=True
    )
    cantidad: Mapped[int] = mapped_column(Integer)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    cita: Mapped["Cita"] = relationship(back_populates="piezas")
    pieza: Mapped["Pieza"] = relationship(back_populates="usos")

    @property
    def importe(self):
        """cantidad × precio congelado del renglón."""
        return (self.cantidad * self.precio_unitario).quantize(CENTAVO)


class Administrador(Base):
    __tablename__ = "administrador"
    __table_args__ = {"schema": ESQUEMA}

    id_admin: Mapped[int] = mapped_column(Integer, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(100))
    usuario: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(String(255))
