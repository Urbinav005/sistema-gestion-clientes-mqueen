# Conexión a PostgreSQL: lee backend/.env, arma la URL, crea el engine y entrega sesiones.
# No crea ni altera tablas: la base ya existe y tiene datos.
import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

# Ruta explícita a backend/.env, calculada desde este archivo (backend/app/db.py),
# para que funcione igual sin importar desde qué carpeta se ejecute uvicorn o pytest.
RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(RUTA_ENV)

# Único lugar donde se escribe el nombre del esquema. Las tablas viven en "BD", no en public.
ESQUEMA = "BD"


def _leer_obligatoria(nombre):
    """Lee una variable obligatoria del entorno o explica cómo arreglarlo."""
    valor = os.getenv(nombre)
    if not valor:
        raise RuntimeError(
            f"Falta la variable {nombre} en backend/.env. Copia .env.example a .env y llénalo."
        )
    return valor


def armar_url():
    """Arma la URL de conexión con las 5 variables de .env, leídas en el momento de la llamada."""
    usuario = _leer_obligatoria("DB_USUARIO")
    password = _leer_obligatoria("DB_PASSWORD")
    nombre = _leer_obligatoria("DB_NOMBRE")
    host = os.getenv("DB_HOST") or "localhost"
    puerto = int(os.getenv("DB_PUERTO") or "5432")

    # URL.create escapa sola los espacios del nombre y los símbolos de la contraseña.
    return URL.create(
        drivername="postgresql+psycopg",
        username=usuario,
        password=password,
        host=host,
        port=puerto,
        database=nombre,
    )


# Crear el engine no abre conexión; se abre en la primera consulta.
# Por eso uvicorn arranca aunque PostgreSQL esté apagado.
engine = create_engine(armar_url())

SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Entrega una sesión por petición y la cierra siempre al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
