# Crea la aplicación FastAPI de Mqueen y registra sus routers.
# Las rutas de negocio exigen la sesión del administrador; salud y login quedan abiertas.
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.errores import registrar_manejadores
from app.routers import auth, citas, clientes, inventario, salud, vehiculos
from app.seguridad import admin_actual

app = FastAPI(title="Mqueen · Inventario Auto Green")

# El frontend (Vite) corre en otro puerto: hay que autorizarlo
ORIGENES_FRONTEND = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGENES_FRONTEND,
    allow_methods=["*"],
    allow_headers=["*"],
)
registrar_manejadores(app)

# Abiertas: diagnóstico de la conexión e inicio de sesión
app.include_router(salud.router, prefix="/api")
app.include_router(auth.router, prefix="/api")

# RN-13: protegidas todas sus rutas, las actuales y las que se agreguen
protegida = [Depends(admin_actual)]
app.include_router(inventario.router, prefix="/api", dependencies=protegida)
app.include_router(clientes.router, prefix="/api", dependencies=protegida)
app.include_router(vehiculos.router, prefix="/api", dependencies=protegida)
app.include_router(citas.router, prefix="/api", dependencies=protegida)
