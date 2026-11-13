# Endpoint GET /salud: comprueba que la base responde y cuenta las piezas del inventario.
# Solo lee; no modifica nada.
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db import ESQUEMA, get_db

router = APIRouter()


@router.get("/salud")
def salud(db: Session = Depends(get_db)):
    # def (no async def) porque la sesión de SQLAlchemy es síncrona.
    try:
        db.execute(text("SELECT 1"))
        piezas = db.execute(text(f'SELECT COUNT(*) FROM "{ESQUEMA}".inventario')).scalar_one()
    except SQLAlchemyError as error:
        # El error real solo va a la consola del servidor: puede incluir usuario o host.
        print(f"[salud] Error de base de datos: {error}")
        raise HTTPException(status_code=503, detail="No se pudo conectar a la base de datos")
    return {"bd": "ok", "piezas": piezas}
