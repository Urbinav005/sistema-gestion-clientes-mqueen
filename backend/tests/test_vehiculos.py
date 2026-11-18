# Pruebas de vehículos: fase 3 (P3-11 a P3-19 y P3-44) y fase 6 (P6-03 a P6-07).
# Alta, placas, filtros, baja, reactivación, historial y última visita. Nada queda guardado.
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


# ---------- Mejora de la fase 3: placas de un vehículo cuyo cliente está de baja ----------

def test_p3_44_placas_con_cliente_dado_de_baja(cliente):
    dueno = crear_cliente(cliente, "PRUEBA Dueño de baja")
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    cliente.delete(f"/api/clientes/{dueno['id_cliente']}")

    otro = crear_cliente(cliente, "PRUEBA Otro dueño")
    respuesta = cliente.post(URL, json=datos_vehiculo(otro["id_cliente"], vehiculo["placas"]))
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"].endswith("Reactiva al cliente.")


# ---------- Fase 6: última visita, búsqueda por cliente y cliente de baja ----------

def test_p6_03_ultima_visita_solo_con_cita_en_proceso(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    url_vehiculo = f"{URL}/{vehiculo['id_vehiculo']}"
    assert vehiculo["ultima_visita"] is None

    cita = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-03-05T10:30:00")
    assert cliente.get(url_vehiculo).json()["ultima_visita"] is None

    cliente.put(f"/api/citas/{cita['id_cita']}/estado", json={"estado": "En proceso"})
    assert cliente.get(url_vehiculo).json()["ultima_visita"] == "2031-03-05T10:30:00"


def test_p6_04_cita_cancelada_no_es_visita(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    terminada = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-04-01T09:00:00")
    cancelada = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-05-01T09:00:00")
    cliente.put(f"/api/citas/{terminada['id_cita']}/estado", json={"estado": "En proceso"})
    cliente.put(f"/api/citas/{terminada['id_cita']}/estado", json={"estado": "Terminada"})
    cliente.put(f"/api/citas/{cancelada['id_cita']}/estado", json={"estado": "Cancelada"})

    consultado = cliente.get(f"{URL}/{vehiculo['id_vehiculo']}").json()
    assert consultado["ultima_visita"] == "2031-04-01T09:00:00"


def test_p6_05_ultima_visita_es_la_mas_reciente(cliente):
    dueno = crear_cliente(cliente)
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    vieja = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-06-01T09:00:00")
    reciente = crear_cita(cliente, vehiculo["id_vehiculo"], "2031-07-01T16:00:00")
    cliente.put(f"/api/citas/{vieja['id_cita']}/estado", json={"estado": "En proceso"})
    cliente.put(f"/api/citas/{vieja['id_cita']}/estado", json={"estado": "Terminada"})
    cliente.put(f"/api/citas/{reciente['id_cita']}/estado", json={"estado": "En proceso"})

    esperada = "2031-07-01T16:00:00"
    assert cliente.get(f"{URL}/{vehiculo['id_vehiculo']}").json()["ultima_visita"] == esperada
    lista = cliente.get(URL, params={"id_cliente": dueno["id_cliente"]}).json()
    assert [v["ultima_visita"] for v in lista] == [esperada]


def test_p6_06_buscar_por_nombre_del_cliente(cliente):
    dueno = crear_cliente(cliente, "PRUEBA Ramón Núñez")
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])

    por_cliente = cliente.get(URL, params={"buscar": "ramón núñez"}).json()
    por_placas = cliente.get(URL, params={"buscar": vehiculo["placas"]}).json()
    for lista in (por_cliente, por_placas):
        assert [v["id_vehiculo"] for v in lista].count(vehiculo["id_vehiculo"]) == 1


def test_p6_07_activo_del_cliente_en_el_vehiculo(cliente):
    dueno = crear_cliente(cliente, "PRUEBA Cliente corto")
    vehiculo = crear_vehiculo(cliente, dueno["id_cliente"])
    url_vehiculo = f"{URL}/{vehiculo['id_vehiculo']}"
    assert cliente.get(url_vehiculo).json()["cliente"]["activo"] is True

    cliente.delete(f"/api/clientes/{dueno['id_cliente']}")
    assert cliente.get(url_vehiculo).json()["cliente"]["activo"] is False

    con_inactivos = cliente.get(URL, params={"incluir_inactivos": "true"}).json()
    encontrado = next(v for v in con_inactivos if v["id_vehiculo"] == vehiculo["id_vehiculo"])
    assert encontrado["activo"] is True
    assert encontrado["cliente"]["activo"] is False
