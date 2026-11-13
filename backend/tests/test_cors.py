# Pruebas de la fase 5 (P5-09 y P5-10): el navegador solo puede llamar a la API
# desde el frontend del equipo (CORS). No tocan datos.
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)

FRONTEND = "http://localhost:5173"


def preflight(origen):
    """La pregunta previa que hace el navegador antes de mandar el token."""
    return cliente.options(
        "/api/inventario",
        headers={
            "Origin": origen,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )


def test_p5_09_cors_autoriza_al_frontend():
    respuesta = preflight(FRONTEND)
    assert respuesta.status_code == 200
    assert respuesta.headers["access-control-allow-origin"] == FRONTEND


def test_p5_10_cors_rechaza_otros_origenes():
    ajeno = preflight("http://sitio-ajeno.com")
    assert "access-control-allow-origin" not in ajeno.headers

    salud = cliente.get("/api/salud", headers={"Origin": FRONTEND})
    assert salud.status_code == 200
    assert salud.headers["access-control-allow-origin"] == FRONTEND
