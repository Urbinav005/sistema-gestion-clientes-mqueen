# Pruebas del inicio de sesión (P4-01 a P4-17): login, rutas protegidas, tokens
# y contraseñas con bcrypt. Usan cliente, db y login_real: la protección está activa.
import secrets

import jwt
import pytest
from sqlalchemy import func, select

from app.models import Administrador, Pieza
from app.seguridad import crear_hash, crear_token, verificar_password
from crear_admin import guardar_admin

USUARIO = "prueba_admin"
# Generada al azar en cada corrida: en el repositorio no queda ninguna contraseña escrita
PASSWORD = secrets.token_urlsafe(12)
SIN_SESION = "Inicia sesión para continuar"
SESION_INVALIDA = "Tu sesión expiró o no es válida. Inicia sesión de nuevo"
CREDENCIALES = "Usuario o contraseña incorrectos"
RUTAS_PROTEGIDAS = ["/api/inventario", "/api/clientes", "/api/vehiculos", "/api/citas"]


@pytest.fixture
def admin_guardado(db):
    """Administrador de prueba guardado dentro de la transacción que se deshace."""
    return guardar_admin(db, "PRUEBA Admin", USUARIO, PASSWORD)


def login(cliente, usuario=USUARIO, password=PASSWORD):
    return cliente.post("/api/auth/login", json={"usuario": usuario, "password": password})


def cabecera(cliente, usuario=USUARIO, password=PASSWORD):
    """Inicia sesión y devuelve la cabecera Authorization lista para usarse."""
    respuesta = login(cliente, usuario, password)
    assert respuesta.status_code == 200, respuesta.json()
    return {"Authorization": f"Bearer {respuesta.json()['token']}"}


def test_p4_01_login_correcto(cliente, login_real, admin_guardado):
    # RN-13
    respuesta = login(cliente)
    assert respuesta.status_code == 200
    datos = respuesta.json()
    assert isinstance(datos["token"], str) and datos["token"]
    assert datos["tipo"] == "bearer"
    assert isinstance(datos["expira_en_minutos"], int)
    assert set(datos["administrador"].keys()) == {"id_admin", "nombre", "usuario"}
    assert "password" not in respuesta.text


def test_p4_02_credenciales_incorrectas(cliente, login_real, admin_guardado):
    # RN-13: el mismo mensaje exista o no el usuario
    for usuario, password in ((USUARIO, "otra-clave-123"), ("no_existe_xyz", PASSWORD)):
        respuesta = login(cliente, usuario, password)
        assert respuesta.status_code == 401
        assert respuesta.json() == {"detail": CREDENCIALES, "errores": []}


def test_p4_03_datos_vacios_o_faltantes(cliente, login_real):
    vacios = login(cliente, "  ", "")
    assert vacios.status_code == 400
    assert {e["campo"] for e in vacios.json()["errores"]} == {"usuario", "password"}

    sin_password = cliente.post("/api/auth/login", json={"usuario": USUARIO})
    assert sin_password.status_code == 422
    assert {"campo": "password", "mensaje": "Este campo es obligatorio"} in sin_password.json()["errores"]


def test_p4_04_usuario_con_espacios_y_mayusculas(cliente, login_real, admin_guardado):
    # RN-14
    assert login(cliente, "  PRUEBA_Admin ").status_code == 200


def test_p4_05_sin_token_responde_401(cliente, login_real, db):
    # RN-13
    for ruta in RUTAS_PROTEGIDAS:
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 401
        assert respuesta.json()["detail"] == SIN_SESION

    pieza = {"nombre": "PRUEBA Sin token", "cantidad": 1, "stock_minimo": 1, "precio_unitario": "10.00"}
    respuesta = cliente.post("/api/inventario", json=pieza)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == SIN_SESION
    assert db.scalars(select(Pieza).where(Pieza.nombre == "PRUEBA Sin token")).first() is None


def test_p4_06_con_token_responde_200(cliente, login_real, admin_guardado):
    # RN-13
    autorizacion = cabecera(cliente)
    for ruta in RUTAS_PROTEGIDAS:
        assert cliente.get(ruta, headers=autorizacion).status_code == 200


def test_p4_07_tokens_no_validos(cliente, login_real, admin_guardado):
    # RN-13
    falso = jwt.encode({"sub": str(admin_guardado.id_admin), "usuario": USUARIO}, "otra-clave-de-al-menos-32-caracteres-x", algorithm="HS256")
    for valor in ("Bearer no-es-un-token", f"Bearer {falso}"):
        respuesta = cliente.get("/api/inventario", headers={"Authorization": valor})
        assert respuesta.status_code == 401
        assert respuesta.json()["detail"] == SESION_INVALIDA

    basico = cliente.get("/api/inventario", headers={"Authorization": "Basic abc"})
    assert basico.status_code == 401
    assert basico.json()["detail"] == SIN_SESION


def test_p4_08_token_vencido(cliente, login_real, admin_guardado):
    # RN-13
    vencido = crear_token(admin_guardado, minutos=-1)
    respuesta = cliente.get("/api/inventario", headers={"Authorization": f"Bearer {vencido}"})
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == SESION_INVALIDA


def test_p4_09_rutas_abiertas(cliente, login_real, admin_guardado):
    assert cliente.get("/api/salud").status_code == 200
    assert cliente.get("/docs").status_code == 200
    assert login(cliente).status_code == 200


def test_p4_10_quien_soy(cliente, login_real, admin_guardado):
    # RN-13
    con_token = cliente.get("/api/auth/yo", headers=cabecera(cliente))
    assert con_token.status_code == 200
    assert con_token.json() == {"id_admin": admin_guardado.id_admin, "nombre": "PRUEBA Admin", "usuario": USUARIO}

    assert cliente.get("/api/auth/yo").status_code == 401


def test_p4_11_hash_bcrypt(db, admin_guardado):
    # RN-15
    guardado = db.get(Administrador, admin_guardado.id_admin).password_hash
    assert guardado.startswith("$2")
    assert len(guardado) == 60
    assert guardado != PASSWORD
    assert verificar_password(PASSWORD, guardado) is True
    assert verificar_password("otra-clave-123", guardado) is False
    assert crear_hash(PASSWORD) != crear_hash(PASSWORD)


def test_p4_12_guardar_otra_vez_actualiza(cliente, login_real, db, admin_guardado):
    # RN-14: no se duplica
    nueva = secrets.token_urlsafe(12)
    guardar_admin(db, "PRUEBA Admin renombrado", USUARIO.upper(), nueva)
    filas = db.scalars(
        select(Administrador).where(func.lower(Administrador.usuario) == USUARIO)
    ).all()
    assert len(filas) == 1
    assert filas[0].nombre == "PRUEBA Admin renombrado"
    assert login(cliente, USUARIO, nueva).status_code == 200
    assert login(cliente, USUARIO, PASSWORD).status_code == 401


def test_p4_13_hash_que_no_es_bcrypt(cliente, login_real, db, admin_guardado):
    # RN-15: un hash que no es bcrypt (32 caracteres, como un MD5) nunca permite entrar
    admin_guardado.password_hash = "a" * 32
    db.flush()
    respuesta = login(cliente, USUARIO, "password")
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == CREDENCIALES


def test_p4_14_validaciones_de_guardar_admin(db):
    # RN-15
    casos = [
        ("prueba_corta", "1234567", "La contraseña debe tener al menos 8 caracteres"),
        ("prueba_larga", "a" * 73, "La contraseña es demasiado larga (máximo 72 bytes)"),
        ("con espacio", "Clave-valida-1", "El usuario es obligatorio, sin espacios y de máximo 50 caracteres"),
    ]
    for usuario, password, mensaje in casos:
        with pytest.raises(ValueError) as error:
            guardar_admin(db, "PRUEBA Invalido", usuario, password)
        assert str(error.value) == mensaje

    nombres = db.scalars(select(Administrador.nombre).where(Administrador.nombre == "PRUEBA Invalido")).all()
    assert nombres == []


def test_p4_15_token_de_admin_borrado(cliente, login_real, db, admin_guardado):
    # RN-13
    autorizacion = cabecera(cliente)
    db.delete(admin_guardado)
    db.flush()
    respuesta = cliente.get("/api/inventario", headers=autorizacion)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == SESION_INVALIDA


def test_p4_16_password_muy_larga(cliente, login_real, admin_guardado):
    respuesta = login(cliente, USUARIO, "x" * 100)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == CREDENCIALES


def test_p4_17_datos_reales_todos_bcrypt(db):
    # RN-15: no queda ninguna contraseña con un hash viejo
    hashes = db.scalars(select(Administrador.password_hash)).all()
    assert len(hashes) >= 1
    assert all(h.startswith("$2") for h in hashes)
