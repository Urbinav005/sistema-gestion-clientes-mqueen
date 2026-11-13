# Registra o actualiza al administrador del sistema. Se ejecuta a mano desde backend/,
# con el entorno virtual activado: python crear_admin.py
from getpass import getpass

from sqlalchemy import func, select

from app.db import SessionLocal
from app.models import Administrador
from app.seguridad import MAXIMO_BYTES_PASSWORD, crear_hash

LARGO_NOMBRE = 100
LARGO_USUARIO = 50
MINIMO_PASSWORD = 8


def guardar_admin(db, nombre, usuario, password):
    """Crea al administrador o, si el usuario ya existe, le actualiza nombre y contraseña."""
    nombre = nombre.strip()
    usuario = usuario.strip().lower()

    if nombre == "" or len(nombre) > LARGO_NOMBRE:
        raise ValueError("El nombre es obligatorio y no puede tener más de 100 caracteres")
    if usuario == "" or len(usuario) > LARGO_USUARIO or any(c.isspace() for c in usuario):
        raise ValueError("El usuario es obligatorio, sin espacios y de máximo 50 caracteres")
    if len(password) < MINIMO_PASSWORD:
        raise ValueError("La contraseña debe tener al menos 8 caracteres")
    if len(password.encode("utf-8")) > MAXIMO_BYTES_PASSWORD:
        raise ValueError("La contraseña es demasiado larga (máximo 72 bytes)")

    # RN-14: el usuario es único; si ya existe se actualiza en vez de duplicarlo
    admin = db.scalars(
        select(Administrador).where(func.lower(Administrador.usuario) == usuario)
    ).first()
    if admin is None:
        admin = Administrador(nombre=nombre, usuario=usuario)
        db.add(admin)
    else:
        admin.nombre = nombre

    # RN-15: se guarda el hash bcrypt, nunca la contraseña
    admin.password_hash = crear_hash(password)
    db.commit()
    db.refresh(admin)
    return admin


if __name__ == "__main__":
    nombre = input("Nombre del administrador: ")
    usuario = input("Usuario: ")
    # getpass: la contraseña no se ve al escribirla
    password = getpass("Contraseña: ")
    confirmacion = getpass("Repite la contraseña: ")

    if password != confirmacion:
        print("Las contraseñas no coinciden. No se guardó nada.")
    else:
        sesion = SessionLocal()
        try:
            admin = guardar_admin(sesion, nombre, usuario, password)
            print(f"Administrador guardado: {admin.usuario}")
        except ValueError as error:
            print(f"No se guardó: {error}")
        finally:
            sesion.close()
