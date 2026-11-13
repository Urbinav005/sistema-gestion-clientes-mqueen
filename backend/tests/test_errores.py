# Pruebas de la fase 2 (P2-31 a P2-37): formato único de error de la API, en español.
# Revisan errores de tipo (422), rutas inexistentes (404), base caída (503) e imprevistos (500).
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db import get_db
from app.main import app

URL = "/api/inventario"


def revisar_formato(respuesta):
    """Toda respuesta de error es JSON con detail (texto) y errores (lista)."""
    assert respuesta.headers["content-type"].startswith("application/json")
    cuerpo = respuesta.json()
    assert isinstance(cuerpo["detail"], str)
    assert isinstance(cuerpo["errores"], list)
    return cuerpo


def test_p2_31_texto_en_campo_entero(cliente):
    datos = {"nombre": "PRUEBA Tipo", "cantidad": "abc", "stock_minimo": 1, "precio_unitario": "10.00"}
    respuesta = cliente.post(URL, json=datos)
    assert respuesta.status_code == 422
    cuerpo = revisar_formato(respuesta)
    assert cuerpo["detail"] == "Revisa los datos marcados"
    assert cuerpo["errores"] == [{"campo": "cantidad", "mensaje": "Debe ser un número entero"}]
    # Ningún texto en inglés de Pydantic
    assert "Input should" not in respuesta.text


def test_p2_32_campos_faltantes(cliente):
    respuesta = cliente.post(URL, json={"cantidad": 1, "stock_minimo": 1})
    assert respuesta.status_code == 422
    cuerpo = revisar_formato(respuesta)
    assert {"campo": "nombre", "mensaje": "Este campo es obligatorio"} in cuerpo["errores"]
    assert {"campo": "precio_unitario", "mensaje": "Este campo es obligatorio"} in cuerpo["errores"]


def test_p2_33_id_que_no_es_numero(cliente):
    respuesta = cliente.get(f"{URL}/abc")
    assert respuesta.status_code == 422
    cuerpo = revisar_formato(respuesta)
    assert {"campo": "id_pieza", "mensaje": "Debe ser un número entero"} in cuerpo["errores"]


def test_p2_34_cuerpo_que_no_es_json(cliente):
    respuesta = cliente.post(URL, content="{mal", headers={"Content-Type": "application/json"})
    assert respuesta.status_code == 422
    cuerpo = revisar_formato(respuesta)
    assert {"campo": "cuerpo", "mensaje": "Los datos enviados no tienen un formato válido"} in cuerpo["errores"]


def test_p2_35_ruta_inexistente(cliente):
    respuesta = cliente.get("/api/no-existe")
    assert respuesta.status_code == 404
    revisar_formato(respuesta)
    assert respuesta.json() == {"detail": "La ruta no existe", "errores": []}


def test_p2_40_sin_cuerpo_o_con_lista(cliente):
    sin_cuerpo = cliente.post(URL)
    con_lista = cliente.post(URL, json=[1, 2])
    for respuesta in (sin_cuerpo, con_lista):
        assert respuesta.status_code == 422
        cuerpo = revisar_formato(respuesta)
        assert len(cuerpo["errores"]) == 1
        assert cuerpo["errores"][0]["campo"] == "cuerpo"
        assert "body" not in respuesta.text


def test_p2_41_caracter_nulo_en_el_nombre(cliente):
    datos = {"nombre": "PRUEBA \x00 nulo", "cantidad": 1, "stock_minimo": 1, "precio_unitario": "10.00"}
    respuesta = cliente.post(URL, json=datos)
    assert respuesta.status_code == 400
    cuerpo = revisar_formato(respuesta)
    assert cuerpo["detail"] == "Alguno de los datos enviados no es válido"


class SesionQueFalla:
    """Sesión falsa: cualquier consulta lanza el error que se le indique."""

    def __init__(self, error):
        self.error = error

    def scalars(self, *args, **kwargs):
        raise self.error

    def execute(self, *args, **kwargs):
        raise self.error

    def scalar(self, *args, **kwargs):
        raise self.error

    def get(self, *args, **kwargs):
        raise self.error

    def close(self):
        pass


def test_p2_36_base_caida(cliente):
    def get_db_caida():
        yield SesionQueFalla(OperationalError("SELECT", {}, Exception("conexión rechazada")))

    app.dependency_overrides[get_db] = get_db_caida
    try:
        respuesta = cliente.get(URL)
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 503
    cuerpo = revisar_formato(respuesta)
    assert cuerpo["detail"] == "No se pudo conectar a la base de datos"


def test_p2_37_error_inesperado_no_muestra_detalles():
    def get_db_rota():
        yield SesionQueFalla(RuntimeError("secreto interno"))

    app.dependency_overrides[get_db] = get_db_rota
    try:
        # raise_server_exceptions=False: el TestClient devuelve el 500 en vez de relanzar el error
        cliente_propio = TestClient(app, raise_server_exceptions=False)
        respuesta = cliente_propio.get(URL)
    finally:
        app.dependency_overrides.clear()

    assert respuesta.status_code == 500
    cuerpo = revisar_formato(respuesta)
    assert cuerpo["detail"] == "Ocurrió un error inesperado. Intenta de nuevo."
    assert "secreto interno" not in respuesta.text
