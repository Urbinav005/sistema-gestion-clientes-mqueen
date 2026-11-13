# Fixtures de pytest para probar contra la base real sin dejar datos guardados.
# Cada prueba corre dentro de una transacción que al final se deshace (ROLLBACK).
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.main import app
from app.models import Administrador
from app.seguridad import admin_actual


@pytest.fixture(autouse=True)
def admin_de_prueba():
    """En todas las pruebas, las rutas protegidas aceptan a un administrador de mentira."""

    def admin_falso():
        # No se guarda en la base: solo existe durante la prueba
        return Administrador(id_admin=0, nombre="PRUEBA Admin falso", usuario="prueba_falso")

    app.dependency_overrides[admin_actual] = admin_falso
    yield
    app.dependency_overrides.pop(admin_actual, None)


@pytest.fixture
def login_real(admin_de_prueba):
    """Quita el administrador de mentira: la protección funciona de verdad."""
    app.dependency_overrides.pop(admin_actual, None)


@pytest.fixture
def db():
    """Sesión ligada a una transacción externa que siempre se deshace al terminar."""
    conexion = engine.connect()
    transaccion = conexion.begin()
    # create_savepoint: el db.commit() de los endpoints solo confirma un punto de guardado;
    # la transacción de afuera sigue abierta y se deshace abajo.
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
    try:
        yield sesion
    finally:
        sesion.close()
        transaccion.rollback()
        conexion.close()


@pytest.fixture
def cliente(db):
    """TestClient cuya API usa la sesión del fixture db."""

    def get_db_de_prueba():
        yield db

    app.dependency_overrides[get_db] = get_db_de_prueba
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()
