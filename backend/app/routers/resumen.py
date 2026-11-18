# Endpoint del resumen general (pantalla de inicio): conteos de citas, vehículos, clientes
# e inventario, las próximas citas de hoy y las alertas de stock. Solo lee.
from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Cita, Cliente, Pieza
from app.routers.inventario import ES_CRITICO
from app.schemas import ResumenGeneral

router = APIRouter(prefix="/resumen", tags=["Resumen"])

MAXIMO_ALERTAS = 5


@router.get("", response_model=ResumenGeneral)
def resumen_general(db: Session = Depends(get_db)):
    hoy = date.today()
    # Las citas de hoy: desde las 00:00 hasta antes de las 00:00 de mañana (igual que /api/citas)
    inicio_hoy = datetime.combine(hoy, time.min)
    inicio_manana = inicio_hoy + timedelta(days=1)
    es_de_hoy = (Cita.fecha >= inicio_hoy) & (Cita.fecha < inicio_manana)
    inicio_mes = datetime.combine(hoy.replace(day=1), time.min)

    # RN-06: vehículos distintos con al menos una cita En proceso, de cualquier fecha
    vehiculos_en_taller = db.scalar(
        select(func.count(func.distinct(Cita.id_vehiculo))).where(Cita.estado == "En proceso")
    )

    # RN-06: las canceladas no cuentan como citas del día
    citas_hoy = db.scalar(
        select(func.count(Cita.id_cita)).where(es_de_hoy, Cita.estado != "Cancelada")
    )
    citas_hoy_pendientes = db.scalar(
        select(func.count(Cita.id_cita)).where(es_de_hoy, Cita.estado == "Pendiente")
    )

    # Solo clientes activos: coincide con la lista de Clientes
    clientes_registrados = db.scalar(
        select(func.count(Cliente.id_cliente)).where(Cliente.activo.is_(True))
    )
    clientes_nuevos_mes = db.scalar(
        select(func.count(Cliente.id_cliente)).where(
            Cliente.activo.is_(True), Cliente.creado_en >= inicio_mes
        )
    )

    # RN-02: stock bajo incluye a las críticas
    hay_stock_bajo = Pieza.cantidad <= Pieza.stock_minimo
    stock_bajo = db.scalar(select(func.count(Pieza.id_pieza)).where(hay_stock_bajo))
    # RN-16: la condición de crítico viene de inventario.py (escrita una sola vez)
    stock_critico = db.scalar(select(func.count(Pieza.id_pieza)).where(ES_CRITICO))

    # RN-06: las de hoy que el taller todavía tiene que atender, de la más temprana a la más tarde
    proximas_citas = db.scalars(
        select(Cita)
        .where(es_de_hoy, Cita.estado.in_(["Pendiente", "En proceso"]))
        .order_by(Cita.fecha, Cita.id_cita)
    ).all()

    # RN-02, RN-16: piezas con stock bajo, las críticas primero; luego menor cantidad y nombre
    alertas_inventario = db.scalars(
        select(Pieza)
        .where(hay_stock_bajo)
        .order_by(case((ES_CRITICO, 0), else_=1), Pieza.cantidad, Pieza.nombre)
        .limit(MAXIMO_ALERTAS)
    ).all()

    return {
        "fecha": hoy,
        "vehiculos_en_taller": vehiculos_en_taller,
        "citas_hoy": citas_hoy,
        "citas_hoy_pendientes": citas_hoy_pendientes,
        "clientes_registrados": clientes_registrados,
        "clientes_nuevos_mes": clientes_nuevos_mes,
        "stock_bajo": stock_bajo,
        "stock_critico": stock_critico,
        "proximas_citas": proximas_citas,
        "alertas_inventario": alertas_inventario,
    }
