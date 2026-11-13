# Manejo de errores de toda la API: la excepción ErrorApi y los manejadores que hacen
# que cualquier error responda {"detail": "...", "errores": [...]} en español.
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DataError, IntegrityError, OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorApi(Exception):
    """Error que lanzan los routers con un código, un mensaje y, opcionalmente, errores por campo."""

    def __init__(self, status_code, mensaje, errores=None):
        super().__init__(mensaje)
        self.status_code = status_code
        self.mensaje = mensaje
        self.errores = errores or []


def respuesta_error(status_code, detail, errores=None):
    """Arma la respuesta con el formato único de error."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail, "errores": errores or []},
    )


def traducir_tipo(tipo):
    """Convierte el 'type' de un error de Pydantic en un mensaje en español."""
    if tipo == "missing":
        return "Este campo es obligatorio"
    if tipo.startswith("int_"):
        return "Debe ser un número entero"
    if tipo.startswith("decimal_") or tipo.startswith("float_"):
        return "Debe ser un número"
    if tipo.startswith("string_"):
        return "Debe ser texto"
    if tipo.startswith("bool_"):
        return "Debe ser verdadero o falso"
    return "Valor no válido"


def registrar_manejadores(app):
    """Registra en la app los manejadores de error."""

    @app.exception_handler(ErrorApi)
    def manejar_error_api(request: Request, exc: ErrorApi):
        return respuesta_error(exc.status_code, exc.mensaje, exc.errores)

    @app.exception_handler(RequestValidationError)
    def manejar_validacion(request: Request, exc: RequestValidationError):
        errores = []
        for error in exc.errors():
            tipo = error.get("type", "")
            if tipo == "json_invalid":
                errores.append({"campo": "cuerpo", "mensaje": "Los datos enviados no tienen un formato válido"})
                continue
            loc = error.get("loc") or ["cuerpo"]
            campo = str(loc[-1])
            # Falta todo el cuerpo o no es un objeto: se nombra en español
            if campo == "body":
                campo = "cuerpo"
            errores.append({"campo": campo, "mensaje": traducir_tipo(tipo)})
        return respuesta_error(422, "Revisa los datos marcados", errores)

    @app.exception_handler(StarletteHTTPException)
    def manejar_http(request: Request, exc: StarletteHTTPException):
        if exc.status_code == 404:
            detail = exc.detail if exc.detail and exc.detail != "Not Found" else "La ruta no existe"
            return respuesta_error(404, detail)
        if exc.status_code == 405:
            return respuesta_error(405, "Esa acción no está permitida en esta ruta")
        return respuesta_error(exc.status_code, str(exc.detail))

    @app.exception_handler(OperationalError)
    def manejar_bd_caida(request: Request, exc: OperationalError):
        print(f"[errores] La base no responde: {exc}")
        return respuesta_error(503, "No se pudo conectar a la base de datos")

    @app.exception_handler(IntegrityError)
    def manejar_integridad(request: Request, exc: IntegrityError):
        print(f"[errores] La base rechazó el dato: {exc}")
        return respuesta_error(409, "No se pudo guardar porque los datos chocan con otro registro")

    @app.exception_handler(DataError)
    def manejar_dato_invalido(request: Request, exc: DataError):
        print(f"[errores] La base no pudo guardar un dato: {exc}")
        return respuesta_error(400, "Alguno de los datos enviados no es válido")

    @app.exception_handler(Exception)
    def manejar_inesperado(request: Request, exc: Exception):
        print(f"[errores] Error inesperado: {exc!r}")
        return respuesta_error(500, "Ocurrió un error inesperado. Intenta de nuevo.")
