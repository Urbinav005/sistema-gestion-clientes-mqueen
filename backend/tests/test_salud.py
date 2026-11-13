# Pruebas de la fase 0: endpoint /api/salud y construcción de la URL de conexión.
# P0-1 necesita PostgreSQL encendido y backend/.env lleno; P0-2 y P0-3 no tocan la base.
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import armar_url, get_db
from app.main import app

cliente = TestClient(app)


def test_p0_1_salud_con_bd_encendida():
    # P0-1: no se compara contra 12 porque el inventario cambiará en otras fases.
    respuesta = cliente.get("/api/salud")
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert datos["bd"] == "ok"
    assert isinstance(datos["piezas"], int)
    assert datos["piezas"] >= 0


class SesionCaida:
    """Sesión falsa que simula que PostgreSQL no contesta."""

    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("conexión rechazada"))

    def close(self):
        pass


def test_p0_2_salud_con_bd_caida():
    # P0-2: se reemplaza get_db por una sesión que siempre falla.
    def get_db_caida():
        yield SesionCaida()

    app.dependency_overrides[get_db] = get_db_caida
    try:
        respuesta = cliente.get("/api/salud")
    finally:
        # Limpiar para no afectar a otras pruebas.
        app.dependency_overrides.clear()

    assert respuesta.status_code == 503
    assert respuesta.json()["detail"] == "No se pudo conectar a la base de datos"


def test_p0_3_armar_url_con_espacios_y_arroba(monkeypatch):
    # P0-3: el nombre con espacios y la contraseña con @ deben llegar exactos.
    monkeypatch.setenv("DB_USUARIO", "postgres")
    monkeypatch.setenv("DB_PASSWORD", "mi@clave#1")
    monkeypatch.setenv("DB_HOST", "localhost")
    monkeypatch.setenv("DB_PUERTO", "5432")
    monkeypatch.setenv("DB_NOMBRE", "Boceto de BD para Mqueen")

    url = armar_url()

    assert url.drivername == "postgresql+psycopg"
    assert url.database == "Boceto de BD para Mqueen"
    assert url.password == "mi@clave#1"
    assert url.username == "postgres"
    assert url.port == 5432
