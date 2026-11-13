# Crea la aplicación FastAPI de Mqueen y registra sus routers.
# CORS se agrega en la fase 5.
from fastapi import FastAPI

from app.errores import registrar_manejadores
from app.routers import citas, clientes, inventario, salud, vehiculos

app = FastAPI(title="Mqueen · Inventario Auto Green")
registrar_manejadores(app)

app.include_router(salud.router, prefix="/api")
app.include_router(inventario.router, prefix="/api")
app.include_router(clientes.router, prefix="/api")
app.include_router(vehiculos.router, prefix="/api")
app.include_router(citas.router, prefix="/api")
