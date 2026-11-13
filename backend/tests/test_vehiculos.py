# Pruebas de la fase 3 (P3-11 a P3-19): alta, validaciones, placas repetidas, filtros,
# edición, baja lógica, reactivación e historial de vehículos. Nada queda guardado.
from decimal import Decimal
from itertools import count

URL = "/api/vehiculos"
ID_INEXISTENTE = 999999999
_numero = count(1)


def nuevas_placas():
    return f"PRU-V{next(_numero):03d}"


def crear_cliente(cliente, nombre="PRUEBA Dueño"):
    datos = {"nombre": nombre, "telefono": "6181234567"}
    respuesta = cliente.post("/api/clientes", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def datos_vehiculo(id_cliente, placas=None, **cambios):
    datos = {
        "id_cliente": id_cliente,
        "placas": placas or nuevas_placas(),
        "marca": "Nissan",
        "modelo": "Versa",
        "anio": 2019,
        "kilometraje": 50000,
    }
    datos.update(cambios)
    return datos


def crear_vehiculo(cliente, id_cliente, placas=None, **cambios):
    respuesta = cliente.post(URL, json=datos_vehiculo(id_cliente, placas, **cambios))
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_cita(cliente, id_vehiculo, fecha="2031-01-10T10:00:00", **cambios):
    datos = {"id_vehiculo": id_vehiculo, "fecha": fecha, "motivo": "PRUEBA cita"}
    datos.update(cambios)
    respuesta = cliente.post("/api/citas", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def tiene_error(respuesta, campo, mensaje=None):
    for error in respuesta.json()["errores"]:
        if error["campo"] == campo and (mensaje is None or error["mensaje"] == mensaje):
            return True
    return False


def test_p3_11_crear_vehiculo_limpia_datos(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"], "  pru-001-a ", marca="Hyundái Ñú", modelo="Clío")
    assert vehiculo["placas"] == "PRU-001-A"
    assert vehiculo["marca"] == "Hyundai Ñu"
    assert vehiculo["modelo"] == "Clio"
    assert vehiculo["activo"] is True
    assert vehiculo["cliente"]["nombre"] == dueno["nombre"]


def test_p3_12_cliente_inexistente_o_dado_de_baja(cliente):
    # RN-12
    inexistente = cliente.post(URL, json=datos_vehiculo(ID_INEXISTENTE))
    assert inexistente.status_code == 400
    assert tiene_error(inexistente, "id_cliente", "El cliente no existe")

    dueno = crear_cliente(cliente, "PRUEBA Dado de baja")
    cliente.delete(f"/api/clientes/{dueno['id_cliente']}")
    de_baja = cliente.post(URL, json=datos_vehiculo(dueno["id_cliente"]))
    assert de_baja.status_code == 400
    assert tiene_error(de_baja, "id_cliente", "El cliente está dado de baja")


def test_p3_13_placas_repetidas(cliente):
    dueno = crear_cliente(cliente)
    primero = crear_vehiculo(cliente, dueno["id_cliente"], "PRU-777-Z")

    repetida = cliente.post(URL, json=datos_vehiculo(dueno["id_cliente"], "pru-777-z"))
    assert repetida.status_code == 409
    assert tiene_error(repetida, "placas", "Ya existe un vehículo con esas placas")

    cliente.delete(f"{URL}/{primero['id_vehiculo']}")
    tras_baja = cliente.post(URL, json=datos_vehiculo(dueno["id_cliente"], "PRU-777-Z"))
    assert tras_baja.status_code == 409
    assert "dado de baja" in tras_baja.json()["errores"][0]["mensaje"]


def test_p3_14_anio_y_kilometraje(cliente):
    dueno = crear_cliente(cliente)
    id_c = dueno["id_cliente"]

    for campo, valor in (("anio", 1949), ("anio", 2101), ("kilometraje", -1)):
        respuesta = cliente.post(URL, json=datos_vehiculo(id_c, **{campo: valor}))
        assert respuesta.status_code == 400
        assert tiene_error(respuesta, campo)

    sin_opcionales = {"id_cliente": id_c, "placas": nuevas_placas(), "marca": "Ford", "modelo": "Ka"}
    respuesta = cliente.post(URL, json=sin_opcionales)
    assert respuesta.status_code == 201
    assert respuesta.json()["anio"] is None
    assert respuesta.json()["kilometraje"] is None


def test_p3_15_filtrar_por_cliente_y_buscar(cliente):
    dueno = crear_cliente(cliente)
    uno = crear_vehiculo(cliente, dueno["id_cliente"], "PRU-QX1-A")
    dos = crear_vehiculo(cliente, dueno["id_cliente"])

    del_cliente = cliente.get(URL, params={"id_cliente": dueno["id_cliente"]}).json()
    assert {v["id_vehiculo"] for v in del_cliente} == {uno["id_vehiculo"], dos["id_vehiculo"]}

    buscados = cliente.get(URL, params={"buscar": "qx1"}).json()
    assert uno["id_vehiculo"] in {v["id_vehiculo"] for v in buscados}


def test_p3_16_editar_vehiculo(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    nuevos = datos_vehiculo(dueno["id_cliente"], vehiculo["placas"], marca="Toyota", modelo="Yaris", kilometraje=61000)

    respuesta = cliente.put(f"{URL}/{vehiculo['id_vehiculo']}", json=nuevos)
    assert respuesta.status_code == 200
    assert respuesta.json()["marca"] == "Toyota"
    assert respuesta.json()["modelo"] == "Yaris"
    assert respuesta.json()["kilometraje"] == 61000

    inexistente = cliente.put(f"{URL}/{ID_INEXISTENTE}", json=nuevos)
    assert inexistente.status_code == 404
    assert inexistente.json()["detail"] == "El vehículo no existe"


def test_p3_17_baja_logica_y_citas_abiertas(cliente):
    dueno = crear_cliente(cliente)
    libre = crear_vehiculo(cliente, dueno["id_cliente"])
    ocupado = crear_vehiculo(cliente, dueno["id_cliente"])
    cita = crear_cita(cliente, ocupado["id_vehiculo"])
    cliente.put(f"/api/citas/{cita['id_cita']}/estado", json={"estado": "En proceso"})

    assert cliente.delete(f"{URL}/{libre['id_vehiculo']}").status_code == 204
    visibles = {v["id_vehiculo"] for v in cliente.get(URL, params={"id_cliente": dueno["id_cliente"]}).json()}
    assert libre["id_vehiculo"] not in visibles

    respuesta = cliente.delete(f"{URL}/{ocupado['id_vehiculo']}")
    assert respuesta.status_code == 409
    assert cliente.get(f"{URL}/{ocupado['id_vehiculo']}").json()["activo"] is True


def test_p3_18_reactivar(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    cliente.delete(f"{URL}/{vehiculo['id_vehiculo']}")

    respuesta = cliente.post(f"{URL}/{vehiculo['id_vehiculo']}/reactivar")
    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is True


def test_p3_19_historial_con_totales(cliente):
    # RN-09
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    pieza = cliente.post("/api/inventario", json={
        "nombre": "PRUEBA Pieza historial", "cantidad": 10, "stock_minimo": 2, "precio_unitario": "100.00",
    }).json()

    vieja = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-01-01T09:00:00")
    reciente = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-02-01T09:00:00", costo_mano_obra="200.00")
    agregada = cliente.post(f"/api/citas/{reciente['id_cita']}/piezas", json={"id_pieza": pieza["id_pieza"], "cantidad": 1})
    assert agregada.status_code == 201

    historial = cliente.get(f"{URL}/{vehiculo['id_vehiculo']}/historial").json()
    assert [c["id_cita"] for c in historial] == [reciente["id_cita"], vieja["id_cita"]]
    assert Decimal(historial[0]["total"]) == Decimal("300.00")
    assert Decimal(historial[1]["total"]) == Decimal("0.00")
