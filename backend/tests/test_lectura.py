# Pruebas de la fase 1: lectura de inventario, clientes y citas, relaciones del ORM
# y que la estructura de la base sigue intacta. Todas leen la base real; ninguna escribe.
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy import select, text

from app.db import SessionLocal
from app.main import app
from app.models import CitaPieza

cliente = TestClient(app)

LLAVES_PIEZA = {"id_pieza", "nombre", "descripcion", "cantidad", "stock_minimo", "precio_unitario", "stock_bajo"}
LLAVES_CLIENTE = {"id_cliente", "nombre", "telefono", "correo", "creado_en", "activo"}
LLAVES_CITA = {"id_cita", "id_vehiculo", "fecha", "motivo", "estado", "costo_mano_obra", "vehiculo", "total"}
ESTADOS_VALIDOS = {"Pendiente", "En proceso", "Terminada", "Cancelada"}


def test_p1_1_listar_inventario():
    respuesta = cliente.get("/api/inventario")
    assert respuesta.status_code == 200
    piezas = respuesta.json()
    assert isinstance(piezas, list)
    assert len(piezas) > 0
    assert set(piezas[0].keys()) == LLAVES_PIEZA

    # La lista trae tantas piezas como cuenta /api/salud
    total = cliente.get("/api/salud").json()["piezas"]
    assert len(piezas) == total


def test_p1_2_dinero_como_texto_con_2_decimales():
    piezas = cliente.get("/api/inventario").json()
    for pieza in piezas:
        precio = pieza["precio_unitario"]
        assert isinstance(precio, str)
        # as_tuple().exponent == -2 significa exactamente 2 decimales
        assert Decimal(precio).as_tuple().exponent == -2


def test_p1_3_listar_clientes():
    respuesta = cliente.get("/api/clientes")
    assert respuesta.status_code == 200
    clientes = respuesta.json()
    assert isinstance(clientes, list)
    assert len(clientes) > 0
    assert set(clientes[0].keys()) == LLAVES_CLIENTE
    for c in clientes:
        assert "password_hash" not in c
        assert "vehiculos" not in c


def test_p1_4_listar_citas_con_estados_validos():
    respuesta = cliente.get("/api/citas")
    assert respuesta.status_code == 200
    citas = respuesta.json()
    assert isinstance(citas, list)
    assert len(citas) > 0
    assert set(citas[0].keys()) == LLAVES_CITA
    # RN-06: solo los cuatro estados válidos
    for cita in citas:
        assert cita["estado"] in ESTADOS_VALIDOS


def test_p1_5_relaciones_del_orm():
    # RN-12: se recorre renglón → cita → vehículo → cliente, sin pasar por la API
    db = SessionLocal()
    try:
        renglon = db.scalars(select(CitaPieza).limit(1)).first()
        assert renglon is not None
        assert isinstance(renglon.pieza.nombre, str)
        assert isinstance(renglon.cita.vehiculo.cliente.nombre, str)
        assert renglon in renglon.cita.piezas
    finally:
        db.close()


def test_p1_6_estructura_intacta():
    # El esquema BD debe seguir con sus 6 tablas: la app no crea ni borra tablas
    db = SessionLocal()
    try:
        total = db.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'BD'")
        ).scalar_one()
        assert total == 6
    finally:
        db.close()
