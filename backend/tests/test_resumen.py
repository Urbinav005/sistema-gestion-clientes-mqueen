# Pruebas de la fase 6.5 (P65-01 a P65-08): resumen general del taller.
# Cada prueba compara el resumen antes y después de crear sus datos. Nada queda guardado.
from datetime import date, datetime, time, timedelta
from itertools import count

URL = "/api/resumen"
LLAVES = {
    "fecha", "vehiculos_en_taller", "citas_hoy", "citas_hoy_pendientes", "clientes_registrados",
    "clientes_nuevos_mes", "stock_bajo", "stock_critico", "proximas_citas", "alertas_inventario",
}
_numero = count(1)


# ---------- Ayudas ----------

def hoy_a_las(hora, minuto=0, dias=0):
    """Texto de fecha local sin zona: hoy (o dentro de 'dias') a esa hora."""
    fecha = datetime.combine(date.today() + timedelta(days=dias), time(hora, minuto))
    return fecha.isoformat()


def resumen(cliente):
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200, respuesta.json()
    return respuesta.json()


def crear_cliente(cliente, nombre="PRUEBA Cliente resumen"):
    respuesta = cliente.post("/api/clientes", json={"nombre": nombre, "telefono": "6181234567"})
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_vehiculo(cliente):
    """Crea un cliente y un vehículo de prueba; devuelve el vehículo."""
    dueno = crear_cliente(cliente)
    datos = {"id_cliente": dueno["id_cliente"], "placas": f"PRU-R{next(_numero):03d}", "marca": "Nissan", "modelo": "Versa"}
    respuesta = cliente.post("/api/vehiculos", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_cita(cliente, id_vehiculo, fecha, estado="Pendiente"):
    """Crea una cita y la lleva al estado pedido por el camino permitido (RN-11)."""
    datos = {"id_vehiculo": id_vehiculo, "fecha": fecha, "motivo": "PRUEBA resumen"}
    respuesta = cliente.post("/api/citas", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    cita = respuesta.json()
    camino = {
        "Pendiente": [],
        "En proceso": ["En proceso"],
        "Terminada": ["En proceso", "Terminada"],
        "Cancelada": ["Cancelada"],
    }[estado]
    for paso in camino:
        cambio = cliente.put(f"/api/citas/{cita['id_cita']}/estado", json={"estado": paso})
        assert cambio.status_code == 200, cambio.json()
    return cita


def crear_pieza(cliente, cantidad, stock_minimo):
    datos = {
        "nombre": f"PRUEBA Pieza resumen {next(_numero)}",
        "cantidad": cantidad,
        "stock_minimo": stock_minimo,
        "precio_unitario": "100.00",
    }
    respuesta = cliente.post("/api/inventario", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


# ---------- Pruebas ----------

def test_p65_01_forma_del_resumen(cliente):
    datos = resumen(cliente)
    assert set(datos.keys()) == LLAVES
    assert datos["fecha"] == date.today().isoformat()
    for llave in LLAVES - {"fecha", "proximas_citas", "alertas_inventario"}:
        assert isinstance(datos[llave], int), llave
    assert isinstance(datos["proximas_citas"], list)
    assert isinstance(datos["alertas_inventario"], list)


def test_p65_02_pide_sesion(cliente, login_real):
    # RN-13
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 401
    assert respuesta.json()["detail"] == "Inicia sesión para continuar"


def test_p65_03_vehiculos_en_taller(cliente):
    # RN-06: un vehículo cuenta una sola vez aunque tenga dos citas En proceso
    antes = resumen(cliente)
    en_taller = crear_vehiculo(cliente)
    crear_cita(cliente, en_taller["id_vehiculo"], hoy_a_las(9), "En proceso")
    crear_cita(cliente, en_taller["id_vehiculo"], hoy_a_las(11), "En proceso")
    otro = crear_vehiculo(cliente)
    crear_cita(cliente, otro["id_vehiculo"], hoy_a_las(10))
    despues = resumen(cliente)
    assert despues["vehiculos_en_taller"] == antes["vehiculos_en_taller"] + 1


def test_p65_04_citas_de_hoy(cliente):
    # RN-06: las canceladas no cuentan; las de mañana tampoco
    antes = resumen(cliente)
    vehiculo = crear_vehiculo(cliente)
    crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(9))
    crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(10), "En proceso")
    crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(11), "Cancelada")
    crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(9, dias=1))
    despues = resumen(cliente)
    assert despues["citas_hoy"] == antes["citas_hoy"] + 2
    assert despues["citas_hoy_pendientes"] == antes["citas_hoy_pendientes"] + 1


def test_p65_05_proximas_citas(cliente):
    # RN-06: solo las de hoy Pendientes o En proceso, por hora
    vehiculo = crear_vehiculo(cliente)
    tarde = crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(16))
    temprano = crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(9), "En proceso")
    terminada = crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(12), "Terminada")
    manana = crear_cita(cliente, vehiculo["id_vehiculo"], hoy_a_las(8, dias=1))

    proximas = resumen(cliente)["proximas_citas"]
    ids = [c["id_cita"] for c in proximas]
    assert ids.index(temprano["id_cita"]) < ids.index(tarde["id_cita"])
    assert terminada["id_cita"] not in ids
    assert manana["id_cita"] not in ids
    for cita in proximas:
        if cita["id_cita"] in (tarde["id_cita"], temprano["id_cita"]):
            assert cita["vehiculo"]["cliente"]["nombre"]
            assert "total" in cita


def test_p65_06_clientes_registrados(cliente):
    antes = resumen(cliente)
    nuevo = crear_cliente(cliente, "PRUEBA Cliente nuevo resumen")
    con_cliente = resumen(cliente)
    assert con_cliente["clientes_registrados"] == antes["clientes_registrados"] + 1
    assert con_cliente["clientes_nuevos_mes"] == antes["clientes_nuevos_mes"] + 1

    cliente.delete(f"/api/clientes/{nuevo['id_cliente']}")
    de_baja = resumen(cliente)
    assert de_baja["clientes_registrados"] == antes["clientes_registrados"]
    assert de_baja["clientes_nuevos_mes"] == antes["clientes_nuevos_mes"]


def test_p65_07_stock_y_alertas(cliente):
    # RN-02, RN-16
    antes = resumen(cliente)
    crear_pieza(cliente, cantidad=0, stock_minimo=6)
    crear_pieza(cliente, cantidad=5, stock_minimo=6)
    despues = resumen(cliente)
    assert despues["stock_bajo"] == antes["stock_bajo"] + 2
    assert despues["stock_critico"] == antes["stock_critico"] + 1

    alertas = despues["alertas_inventario"]
    assert len(alertas) == min(5, despues["stock_bajo"])
    estados = [p["estado_stock"] for p in alertas]
    assert set(estados) <= {"bajo", "critico"}
    # Ninguna crítica después de una baja
    if "bajo" in estados:
        assert "critico" not in estados[estados.index("bajo"):]


def test_p65_08_coincide_con_las_otras_pantallas(cliente):
    datos = resumen(cliente)
    inventario = cliente.get("/api/inventario/resumen").json()
    assert datos["stock_bajo"] == inventario["stock_bajo"]
    assert datos["stock_critico"] == inventario["critico"]

    assert datos["clientes_registrados"] == len(cliente.get("/api/clientes").json())

    citas = cliente.get("/api/citas", params={"fecha": date.today().isoformat()}).json()
    assert datos["citas_hoy"] == sum(1 for c in citas if c["estado"] != "Cancelada")
