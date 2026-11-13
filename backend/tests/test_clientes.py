# Pruebas de la fase 3 (P3-01 a P3-10): alta, búsqueda, consulta, edición, baja lógica
# y reactivación de clientes. Usan los fixtures de conftest.py: nada queda guardado.
from itertools import count

URL = "/api/clientes"
ID_INEXISTENTE = 999999999
_numero = count(1)


def datos_cliente(nombre="PRUEBA Cliente", **cambios):
    datos = {"nombre": nombre, "telefono": "618 123 4567", "correo": "prueba@correo.com"}
    datos.update(cambios)
    return datos


def crear_cliente(cliente, nombre="PRUEBA Cliente", **cambios):
    respuesta = cliente.post(URL, json=datos_cliente(nombre, **cambios))
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_vehiculo(cliente, id_cliente):
    placas = f"PRU-C{next(_numero):03d}"
    datos = {"id_cliente": id_cliente, "placas": placas, "marca": "Nissan", "modelo": "Versa"}
    respuesta = cliente.post("/api/vehiculos", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_cita(cliente, id_vehiculo):
    datos = {"id_vehiculo": id_vehiculo, "fecha": "2031-01-10T10:00:00", "motivo": "PRUEBA cita"}
    respuesta = cliente.post("/api/citas", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def campos_con_error(respuesta):
    return {e["campo"] for e in respuesta.json()["errores"]}


def ids(lista):
    return {elemento["id_cliente"] for elemento in lista}


def test_p3_01_crear_cliente_limpia_datos(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA José Ñúñez", telefono="618 123 4567", correo="Jose@Correo.COM")
    assert nuevo["nombre"] == "PRUEBA Jose Ñuñez"
    assert nuevo["correo"] == "jose@correo.com"
    assert nuevo["activo"] is True
    assert nuevo["creado_en"]


def test_p3_02_reporta_los_tres_errores(cliente):
    respuesta = cliente.post(URL, json=datos_cliente("", telefono="abc", correo="sin-arroba"))
    assert respuesta.status_code == 400
    assert campos_con_error(respuesta) == {"nombre", "telefono", "correo"}


def test_p3_03_correo_opcional(cliente):
    sin_correo = cliente.post(URL, json={"nombre": "PRUEBA Sin correo", "telefono": "6181234567"})
    con_espacios = cliente.post(URL, json=datos_cliente("PRUEBA Correo vacio", correo="   "))
    assert sin_correo.status_code == 201
    assert con_espacios.status_code == 201
    assert sin_correo.json()["correo"] is None
    assert con_espacios.json()["correo"] is None


def test_p3_04_buscar_por_nombre_y_telefono(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Zúñiga Unico", telefono="618 999 0001")
    por_nombre = cliente.get(URL, params={"buscar": "zuñiga unico"}).json()
    por_telefono = cliente.get(URL, params={"buscar": "618 999 0001"}).json()
    assert nuevo["id_cliente"] in ids(por_nombre)
    assert nuevo["id_cliente"] in ids(por_telefono)


def test_p3_05_consultar_con_vehiculos_y_404(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Con vehiculo")
    vehiculo = crear_vehiculo(cliente, nuevo["id_cliente"])

    detalle = cliente.get(f"{URL}/{nuevo['id_cliente']}")
    assert detalle.status_code == 200
    assert vehiculo["id_vehiculo"] in {v["id_vehiculo"] for v in detalle.json()["vehiculos"]}

    for id_malo in (ID_INEXISTENTE, 2147483648):
        respuesta = cliente.get(f"{URL}/{id_malo}")
        assert respuesta.status_code == 404
        assert respuesta.json()["detail"] == "El cliente no existe"


def test_p3_06_editar_cliente(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Editar")
    cambios = {"nombre": "PRUEBA Editado", "telefono": "618-555-0000", "correo": "otro@correo.com"}
    respuesta = cliente.put(f"{URL}/{nuevo['id_cliente']}", json=cambios)
    assert respuesta.status_code == 200
    for campo, valor in cambios.items():
        assert respuesta.json()[campo] == valor

    assert cliente.put(f"{URL}/{ID_INEXISTENTE}", json=cambios).status_code == 404


def test_p3_07_baja_logica(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Baja")
    assert cliente.delete(f"{URL}/{nuevo['id_cliente']}").status_code == 204

    assert nuevo["id_cliente"] not in ids(cliente.get(URL).json())
    todos = cliente.get(URL, params={"incluir_inactivos": "true"}).json()
    inactivo = [c for c in todos if c["id_cliente"] == nuevo["id_cliente"]]
    assert inactivo and inactivo[0]["activo"] is False
    assert cliente.get(f"{URL}/{nuevo['id_cliente']}").status_code == 200


def test_p3_08_no_dar_de_baja_con_citas_abiertas(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Con cita")
    vehiculo = crear_vehiculo(cliente, nuevo["id_cliente"])
    crear_cita(cliente, vehiculo["id_vehiculo"])

    respuesta = cliente.delete(f"{URL}/{nuevo['id_cliente']}")
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No se puede dar de baja: el cliente tiene citas pendientes o en proceso"
    assert cliente.get(f"{URL}/{nuevo['id_cliente']}").json()["activo"] is True


def test_p3_09_reactivar(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Reactivar")
    cliente.delete(f"{URL}/{nuevo['id_cliente']}")

    respuesta = cliente.post(f"{URL}/{nuevo['id_cliente']}/reactivar")
    assert respuesta.status_code == 200
    assert respuesta.json()["activo"] is True
    assert nuevo["id_cliente"] in ids(cliente.get(URL).json())


def test_p3_10_baja_del_cliente_oculta_sus_vehiculos(cliente):
    nuevo = crear_cliente(cliente, "PRUEBA Oculta vehiculos")
    vehiculo = crear_vehiculo(cliente, nuevo["id_cliente"])
    filtro = {"id_cliente": nuevo["id_cliente"]}

    cliente.delete(f"{URL}/{nuevo['id_cliente']}")
    assert cliente.get("/api/vehiculos", params=filtro).json() == []

    cliente.post(f"{URL}/{nuevo['id_cliente']}/reactivar")
    visibles = cliente.get("/api/vehiculos", params=filtro).json()
    assert [v["id_vehiculo"] for v in visibles] == [vehiculo["id_vehiculo"]]
