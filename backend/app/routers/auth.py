# Endpoints de inicio de sesión: POST /auth/login entrega el token y GET /auth/yo
# dice quién es el administrador dueño del token.
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.errores import ErrorApi
from app.models import Administrador
from app.schemas import AdminSalida, LoginEntrada, TokenSalida
from app.seguridad import HASH_DE_RELLENO, JWT_MINUTOS, admin_actual, crear_token, verificar_password

router = APIRouter(prefix="/auth", tags=["Sesion"])

MENSAJE_CREDENCIALES = "Usuario o contraseña incorrectos"


@router.post("/login", response_model=TokenSalida)
def iniciar_sesion(datos: LoginEntrada, db: Session = Depends(get_db)):
    usuario = datos.usuario.strip()

    errores = []
    if usuario == "":
        errores.append({"campo": "usuario", "mensaje": "El usuario es obligatorio"})
    if datos.password == "":
        errores.append({"campo": "password", "mensaje": "La contraseña es obligatoria"})
    if errores:
        raise ErrorApi(400, "Revisa los datos marcados", errores)

    # RN-14: el usuario es único; se busca sin distinguir mayúsculas
    admin = db.scalars(
        select(Administrador).where(func.lower(Administrador.usuario) == usuario.lower())
    ).first()

    if admin is None:
        # Se verifica igual contra un hash de relleno para que tarde lo mismo
        verificar_password(datos.password, HASH_DE_RELLENO)
        raise ErrorApi(401, MENSAJE_CREDENCIALES)

    # RN-15: se compara contra el hash bcrypt, nunca contra texto plano
    if not verificar_password(datos.password, admin.password_hash):
        # Mismo mensaje que si no existiera: no se revela qué usuarios hay
        raise ErrorApi(401, MENSAJE_CREDENCIALES)

    # RN-13: solo un administrador recibe token
    return {
        "token": crear_token(admin),
        "tipo": "bearer",
        "expira_en_minutos": JWT_MINUTOS,
        "administrador": admin,
    }


@router.get("/yo", response_model=AdminSalida)
def quien_soy(admin: Administrador = Depends(admin_actual)):
    return admin
