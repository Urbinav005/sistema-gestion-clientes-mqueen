# Pruebas de la fase 3 (P3-20 a P3-42): citas, cambios de estado, piezas usadas con descuento
# y devolución de stock, y ticket. Usan los fixtures de conftest.py: nada queda guardado.
from decimal import Decimal
from itertools import count

URL = "/api/citas"
ID_INEXISTENTE = 999999999
ACENTOS = set("áéíóúÁÉÍÓÚ")
_numero = count(1)


# ---------- Ayudas ----------

def crear_vehiculo(cliente):
    """Crea un cliente y un vehículo de prueba; devuelve el vehículo."""
    dueno = cliente.post("/api/clientes", json={"nombre": "PRUEBA Dueño cita", "telefono": "6181234567"}).json()
    datos = {"id_cliente": dueno["id_cliente"], "placas": f"PRU-T{next(_numero):03d}", "marca": "Nissan", "modelo": "Versa"}
    respuesta = cliente.post("/api/vehiculos", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_cita(cliente, id_vehiculo=None, fecha="2031-01-10T10:00:00", **cambios):
    if id_vehiculo is None:
        id_vehiculo = crear_vehiculo(cliente)["id_vehiculo"]
    datos = {"id_vehiculo": id_vehiculo, "fecha": fecha, "motivo": "PRUEBA servicio"}
    datos.update(cambios)
    respuesta = cliente.post(URL, json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def crear_pieza(cliente, nombre=None, cantidad=10, stock_minimo=2, precio="100.00"):
    datos = {
        "nombre": nombre or f"PRUEBA Pieza cita {next(_numero)}",
        "cantidad": cantidad,
        "stock_minimo": stock_minimo,
        "precio_unitario": precio,
    }
    respuesta = cliente.post("/api/inventario", json=datos)
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def existencia(cliente, id_pieza):
    return cliente.get(f"/api/inventario/{id_pieza}").json()["cantidad"]


def agregar(cliente, id_cita, id_pieza, cantidad):
    return cliente.post(f"{URL}/{id_cita}/piezas", json={"id_pieza": id_pieza, "cantidad": cantidad})


def cambiar_estado(cliente, id_cita, estado):
    return cliente.put(f"{URL}/{id_cita}/estado", json={"estado": estado})


def ticket(cliente, id_cita):
    return cliente.get(f"{URL}/{id_cita}/ticket").json()


def tiene_error(respuesta, campo, mensaje=None):
    for error in respuesta.json()["errores"]:
        if error["campo"] == campo and (mensaje is None or error["mensaje"] == mensaje):
            return True
    return False


def cita_terminada(cliente):
    cita = crear_cita(cliente)
    cambiar_estado(cliente, cita["id_cita"], "En proceso")
    cambiar_estado(cliente, cita["id_cita"], "Terminada")
    return cita


# ---------- Alta, filtros y edición ----------

def test_p3_20_crear_cita(cliente):
    # RN-09
    vehiculo = crear_vehiculo(cliente)
    cita = crear_cita(cliente, vehiculo["id_vehiculo"], motivo="Afinación mayor", costo_mano_obra="250.00")
    assert cita["estado"] == "Pendiente"
    assert cita["motivo"] == "Afinacion mayor"
    assert cita["total"] == "250.00"
    assert cita["vehiculo"]["placas"] == vehiculo["placas"]
    assert cita["vehiculo"]["cliente"]["id_cliente"] == vehiculo["id_cliente"]

    sin_costo = crear_cita(cliente, vehiculo["id_vehiculo"])
    assert sin_costo["costo_mano_obra"] == "0.00"


def test_p3_21_validaciones_de_alta(cliente):
    # RN-12
    base = {"fecha": "2031-01-10T10:00:00", "motivo": "PRUEBA"}
    inexistente = cliente.post(URL, json={**base, "id_vehiculo": ID_INEXISTENTE})
    assert inexistente.status_code == 400
    assert tiene_error(inexistente, "id_vehiculo", "El vehículo no existe")

    vehiculo = crear_vehiculo(cliente)
    cliente.delete(f"/api/vehiculos/{vehiculo['id_vehiculo']}")
    de_baja = cliente.post(URL, json={**base, "id_vehiculo": vehiculo["id_vehiculo"]})
    assert de_baja.status_code == 400
    assert tiene_error(de_baja, "id_vehiculo", "El vehículo está dado de baja")

    otro = crear_vehiculo(cliente)
    malos = cliente.post(URL, json={**base, "id_vehiculo": otro["id_vehiculo"], "motivo": "  ", "costo_mano_obra": -1})
    assert malos.status_code == 400
    assert tiene_error(malos, "motivo")
    assert tiene_error(malos, "costo_mano_obra")


def test_p3_22_filtros_de_la_lista(cliente):
    cita = crear_cita(cliente, fecha="2031-03-15T10:00:00")
    por_fecha = cliente.get(URL, params={"fecha": "2031-03-15"}).json()
    por_estado = cliente.get(URL, params={"estado": "Pendiente"}).json()
    por_vehiculo = cliente.get(URL, params={"id_vehiculo": cita["id_vehiculo"]}).json()

    for lista in (por_fecha, por_estado, por_vehiculo):
        assert cita["id_cita"] in {c["id_cita"] for c in lista}
    assert all(c["fecha"].startswith("2031-03-15") for c in por_fecha)


def test_p3_23_estado_invalido(cliente):
    # RN-06
    cita = crear_cita(cliente)
    cambio = cambiar_estado(cliente, cita["id_cita"], "Completada")
    filtro = cliente.get(URL, params={"estado": "Completada"})
    for respuesta in (cambio, filtro):
        assert respuesta.status_code == 400
        assert tiene_error(respuesta, "estado")


def test_p3_24_flujo_normal_de_estados(cliente):
    # RN-06
    cita = crear_cita(cliente)
    assert cambiar_estado(cliente, cita["id_cita"], "En proceso").status_code == 200
    final = cambiar_estado(cliente, cita["id_cita"], "Terminada")
    assert final.status_code == 200
    assert final.json()["estado"] == "Terminada"


def test_p3_25_cambios_no_permitidos(cliente):
    # RN-11
    pendiente = crear_cita(cliente)
    terminada = cita_terminada(cliente)
    cancelada = crear_cita(cliente)
    cambiar_estado(cliente, cancelada["id_cita"], "Cancelada")

    casos = [
        (pendiente, "Terminada"),
        (terminada, "En proceso"),
        (cancelada, "Pendiente"),
        (pendiente, "Pendiente"),
    ]
    for cita, nuevo in casos:
        respuesta = cambiar_estado(cliente, cita["id_cita"], nuevo)
        assert respuesta.status_code == 409
        assert respuesta.json()["detail"].startswith("No se puede pasar de")


def test_p3_26_editar_cita_abierta_y_cerrada(cliente):
    # RN-11
    cambios = {"fecha": "2031-05-05T12:30:00", "motivo": "PRUEBA cambio", "costo_mano_obra": "99.90"}
    abierta = crear_cita(cliente)
    respuesta = cliente.put(f"{URL}/{abierta['id_cita']}", json=cambios)
    assert respuesta.status_code == 200
    assert respuesta.json()["fecha"] == "2031-05-05T12:30:00"
    assert respuesta.json()["motivo"] == "PRUEBA cambio"
    assert respuesta.json()["costo_mano_obra"] == "99.90"

    cerrada = cita_terminada(cliente)
    antes = cliente.get(f"{URL}/{cerrada['id_cita']}").json()
    rechazo = cliente.put(f"{URL}/{cerrada['id_cita']}", json=cambios)
    assert rechazo.status_code == 409
    assert cliente.get(f"{URL}/{cerrada['id_cita']}").json() == antes


# ---------- Piezas de una cita ----------

def test_p3_27_agregar_pieza_descuenta_stock(cliente):
    # RN-07, RN-08
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    respuesta = agregar(cliente, cita["id_cita"], pieza["id_pieza"], 3)
    assert respuesta.status_code == 201
    renglones = respuesta.json()["renglones"]
    assert len(renglones) == 1
    assert renglones[0]["cantidad"] == 3
    assert renglones[0]["precio_unitario"] == "100.00"
    assert renglones[0]["importe"] == "300.00"
    assert existencia(cliente, pieza["id_pieza"]) == 7


def test_p3_28_precio_congelado(cliente):
    # RN-08
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    agregar(cliente, cita["id_cita"], pieza["id_pieza"], 1)
    cliente.put(f"/api/inventario/{pieza['id_pieza']}", json={
        "nombre": pieza["nombre"], "cantidad": 9, "stock_minimo": 2, "precio_unitario": "150.00",
    })
    assert ticket(cliente, cita["id_cita"])["renglones"][0]["precio_unitario"] == "100.00"


def test_p3_29_stock_insuficiente(cliente):
    # RN-01
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    respuesta = agregar(cliente, cita["id_cita"], pieza["id_pieza"], 11)
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "cantidad", "Stock insuficiente: solo hay 10")
    assert existencia(cliente, pieza["id_pieza"]) == 10
    assert ticket(cliente, cita["id_cita"])["renglones"] == []


def test_p3_30_usar_toda_la_existencia(cliente):
    # RN-01
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    assert agregar(cliente, cita["id_cita"], pieza["id_pieza"], 10).status_code == 201
    assert existencia(cliente, pieza["id_pieza"]) == 0


def test_p3_31_misma_pieza_suma_al_renglon(cliente):
    # RN-07, RN-08
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    agregar(cliente, cita["id_cita"], pieza["id_pieza"], 2)
    cliente.put(f"/api/inventario/{pieza['id_pieza']}", json={
        "nombre": pieza["nombre"], "cantidad": 8, "stock_minimo": 2, "precio_unitario": "150.00",
    })
    respuesta = agregar(cliente, cita["id_cita"], pieza["id_pieza"], 3)
    renglones = respuesta.json()["renglones"]
    assert len(renglones) == 1
    assert renglones[0]["cantidad"] == 5
    assert renglones[0]["precio_unitario"] == "100.00"
    assert existencia(cliente, pieza["id_pieza"]) == 5


def test_p3_32_datos_invalidos_al_agregar(cliente):
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    for cantidad in (0, -1):
        respuesta = agregar(cliente, cita["id_cita"], pieza["id_pieza"], cantidad)
        assert respuesta.status_code == 400
        assert tiene_error(respuesta, "cantidad")

    sin_pieza = agregar(cliente, cita["id_cita"], ID_INEXISTENTE, 1)
    assert sin_pieza.status_code == 400
    assert tiene_error(sin_pieza, "id_pieza", "La pieza no existe")

    sin_cita = agregar(cliente, ID_INEXISTENTE, pieza["id_pieza"], 1)
    assert sin_cita.status_code == 404
    assert sin_cita.json()["detail"] == "La cita no existe"


def test_p3_33_aviso_de_stock_bajo(cliente):
    # RN-02
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    con_aviso = agregar(cliente, cita["id_cita"], pieza["id_pieza"], 8).json()
    assert con_aviso["aviso"].startswith("Stock bajo: quedan 2")

    otra_cita = crear_cita(cliente)
    otra_pieza = crear_pieza(cliente)
    sin_aviso = agregar(cliente, otra_cita["id_cita"], otra_pieza["id_pieza"], 1).json()
    assert sin_aviso["aviso"] is None


def test_p3_34_no_agregar_a_cita_cerrada(cliente):
    # RN-11
    pieza = crear_pieza(cliente)
    terminada = cita_terminada(cliente)
    cancelada = crear_cita(cliente)
    cambiar_estado(cliente, cancelada["id_cita"], "Cancelada")

    for cita in (terminada, cancelada):
        assert agregar(cliente, cita["id_cita"], pieza["id_pieza"], 1).status_code == 409
    assert existencia(cliente, pieza["id_pieza"]) == 10


def test_p3_35_quitar_pieza_devuelve_stock(cliente):
    # RN-07
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    agregar(cliente, cita["id_cita"], pieza["id_pieza"], 4)

    respuesta = cliente.delete(f"{URL}/{cita['id_cita']}/piezas/{pieza['id_pieza']}")
    assert respuesta.status_code == 200
    assert respuesta.json()["renglones"] == []
    assert existencia(cliente, pieza["id_pieza"]) == 10


def test_p3_36_quitar_pieza_ausente_o_de_cita_cerrada(cliente):
    # RN-11
    cita = crear_cita(cliente)
    pieza = crear_pieza(cliente)
    ausente = cliente.delete(f"{URL}/{cita['id_cita']}/piezas/{pieza['id_pieza']}")
    assert ausente.status_code == 404
    assert ausente.json()["detail"] == "La cita no tiene esa pieza"

    agregar(cliente, cita["id_cita"], pieza["id_pieza"], 1)
    cambiar_estado(cliente, cita["id_cita"], "En proceso")
    cambiar_estado(cliente, cita["id_cita"], "Terminada")
    cerrada = cliente.delete(f"{URL}/{cita['id_cita']}/piezas/{pieza['id_pieza']}")
    assert cerrada.status_code == 409
    assert len(ticket(cliente, cita["id_cita"])["renglones"]) == 1


# ---------- Cancelación y ticket ----------

def test_p3_37_cancelar_devuelve_las_piezas(cliente):
    # RN-10
    cita = crear_cita(cliente)
    pieza_a = crear_pieza(cliente)
    pieza_b = crear_pieza(cliente)
    agregar(cliente, cita["id_cita"], pieza_a["id_pieza"], 3)
    agregar(cliente, cita["id_cita"], pieza_b["id_pieza"], 2)

    respuesta = cambiar_estado(cliente, cita["id_cita"], "Cancelada")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "Cancelada"
    assert existencia(cliente, pieza_a["id_pieza"]) == 10
    assert existencia(cliente, pieza_b["id_pieza"]) == 10

    datos = ticket(cliente, cita["id_cita"])
    assert len(datos["renglones"]) == 2
    assert datos["subtotal_piezas"] == "0.00"
    assert datos["total"] == "0.00"


def test_p3_38_cancelar_cita_en_proceso_sin_piezas(cliente):
    # RN-10
    cita = crear_cita(cliente)
    cambiar_estado(cliente, cita["id_cita"], "En proceso")
    respuesta = cambiar_estado(cliente, cita["id_cita"], "Cancelada")
    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "Cancelada"


def test_p3_39_ticket_completo(cliente):
    # RN-09
    cita = crear_cita(cliente, costo_mano_obra="300.00")
    pieza_b = crear_pieza(cliente, "PRUEBA B Ticket", precio="50.50")
    pieza_a = crear_pieza(cliente, "PRUEBA A Ticket", precio="100.00")
    agregar(cliente, cita["id_cita"], pieza_b["id_pieza"], 1)
    agregar(cliente, cita["id_cita"], pieza_a["id_pieza"], 2)

    datos = ticket(cliente, cita["id_cita"])
    assert [r["nombre"] for r in datos["renglones"]] == ["PRUEBA A Ticket", "PRUEBA B Ticket"]
    assert [r["importe"] for r in datos["renglones"]] == ["200.00", "50.50"]
    assert datos["subtotal_piezas"] == "250.50"
    assert datos["total"] == "550.50"
    assert datos["vehiculo"]["placas"] == cita["vehiculo"]["placas"]
    assert datos["vehiculo"]["cliente"]["nombre"]
    assert datos["aviso"] is None


def test_p3_40_ticket_y_cita_inexistentes(cliente):
    for ruta in (f"{URL}/{ID_INEXISTENTE}/ticket", f"{URL}/{ID_INEXISTENTE}"):
        respuesta = cliente.get(ruta)
        assert respuesta.status_code == 404
        assert respuesta.json()["detail"] == "La cita no existe"


def test_p3_41_las_citas_no_se_borran(cliente):
    cita = crear_cita(cliente)
    respuesta = cliente.delete(f"{URL}/{cita['id_cita']}")
    assert respuesta.status_code == 405
    assert respuesta.json()["detail"] == "Esa acción no está permitida en esta ruta"
    assert cliente.get(f"{URL}/{cita['id_cita']}").status_code == 200


def test_p3_42_datos_reales(cliente):
    # RN-09
    citas = cliente.get(URL).json()
    assert len(citas) > 0
    for cita in citas:
        assert isinstance(cita["total"], str)
        assert Decimal(cita["total"]).as_tuple().exponent == -2
        assert cita["vehiculo"]["cliente"]["nombre"]
        assert not (set(cita["motivo"]) & ACENTOS)
        assert not (set(cita["vehiculo"]["cliente"]["nombre"]) & ACENTOS)

    primera = citas[0]
    assert ticket(cliente, primera["id_cita"])["total"] == primera["total"]
