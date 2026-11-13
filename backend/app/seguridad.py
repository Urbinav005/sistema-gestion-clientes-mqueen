# Seguridad del administrador: contraseñas con bcrypt, tokens JWT y la dependencia
# admin_actual, que protege las rutas de la API.
import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db import get_db  # importar db también carga backend/.env
from app.errores import ErrorApi
from app.models import Administrador
from app.utiles import ID_MAXIMO

LARGO_MINIMO_SECRETO = 32
MAXIMO_BYTES_PASSWORD = 72  # bcrypt no acepta contraseñas más largas
ALGORITMO = "HS256"

JWT_SECRETO = os.getenv("JWT_SECRETO") or ""
if len(JWT_SECRETO) < LARGO_MINIMO_SECRETO:
    raise RuntimeError(
        "Falta la variable JWT_SECRETO en backend/.env (mínimo 32 caracteres). "
        "Genera una con el comando que viene en .env.example."
    )
JWT_MINUTOS = int(os.getenv("JWT_MINUTOS") or "480")

MENSAJE_SIN_SESION = "Inicia sesión para continuar"
MENSAJE_SESION_INVALIDA = "Tu sesión expiró o no es válida. Inicia sesión de nuevo"


def crear_hash(password):
    """Devuelve el hash bcrypt de la contraseña. Cada llamada usa una sal distinta."""
    # RN-15: nunca se guarda la contraseña, solo su hash
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_password(password, hash_guardado):
    """True si la contraseña corresponde al hash. Nunca lanza error: ante cualquier duda, False."""
    datos = password.encode("utf-8")
    if len(datos) > MAXIMO_BYTES_PASSWORD:
        return False
    try:
        return bcrypt.checkpw(datos, hash_guardado.encode("utf-8"))
    except ValueError:
        # RN-15: un hash que no es bcrypt (por ejemplo, MD5) nunca permite entrar
        return False


# Hash fijo de relleno: si el usuario no existe, se verifica contra este hash
# para que la respuesta tarde lo mismo exista o no el usuario
HASH_DE_RELLENO = crear_hash("relleno-para-igualar-tiempos")


def crear_token(admin, minutos=None):
    """Crea un token JWT firmado con HS256 que dice quién es el administrador y hasta cuándo vale."""
    # RN-13: el token solo se entrega a un registro de administrador
    if minutos is None:
        minutos = JWT_MINUTOS
    datos = {
        "sub": str(admin.id_admin),
        "usuario": admin.usuario,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=minutos),
    }
    return jwt.encode(datos, JWT_SECRETO, algorithm=ALGORITMO)


# auto_error=False: si falta la cabecera, devuelve None y el 401 lo armamos nosotros en español
esquema_bearer = HTTPBearer(auto_error=False)


def admin_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer),
    db: Session = Depends(get_db),
):
    """Dependencia que protege las rutas: devuelve el administrador dueño del token o responde 401."""
    # RN-13: sin token de administrador no se usa la API
    if credenciales is None or credenciales.scheme.lower() != "bearer":
        raise ErrorApi(401, MENSAJE_SIN_SESION)

    try:
        datos = jwt.decode(credenciales.credentials, JWT_SECRETO, algorithms=[ALGORITMO])
        id_admin = int(datos["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        # Firma que no coincide, token vencido, mal formado o sin id
        raise ErrorApi(401, MENSAJE_SESION_INVALIDA)

    admin = None
    if 1 <= id_admin <= ID_MAXIMO:
        admin = db.get(Administrador, id_admin)
    if admin is None:
        # El token es válido, pero ese administrador ya no existe
        raise ErrorApi(401, MENSAJE_SESION_INVALIDA)
    return admin
