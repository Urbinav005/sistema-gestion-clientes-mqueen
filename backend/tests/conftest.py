# Fixtures de pytest para probar contra la base real sin dejar datos guardados.
# Cada prueba corre dentro de una transacción que al final se deshace (ROLLBACK).
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.db import engine, get_db
from app.main import app


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
