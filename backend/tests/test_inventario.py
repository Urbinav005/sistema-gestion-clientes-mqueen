# Pruebas del inventario: fase 2 (P2-01 a P2-39) y niveles de stock de la fase 5 (P5-01 a P5-08).
# Usan los fixtures de conftest.py: nada queda guardado.
from decimal import Decimal

from sqlalchemy import select, text

from app.db import engine
from app.models import CitaPieza

URL = "/api/inventario"
ID_INEXISTENTE = 999999999


def pieza_valida(nombre="PRUEBA Pieza", **cambios):
    """Datos de una pieza válida; se pueden sobrescribir campos con cambios."""
    datos = {
        "nombre": nombre,
        "descripcion": "Pieza de prueba",
        "cantidad": 10,
        "stock_minimo": 5,
        "precio_unitario": "100.00",
    }
    datos.update(cambios)
    return datos


def crear(cliente, **datos):
    """Crea una pieza válida y devuelve el JSON de la respuesta (debe ser 201)."""
    respuesta = cliente.post(URL, json=pieza_valida(**datos))
    assert respuesta.status_code == 201, respuesta.json()
    return respuesta.json()


def tiene_error(respuesta, campo, mensaje):
    """True si la respuesta trae un error de ese campo con ese mensaje."""
    cuerpo = respuesta.json()
    assert isinstance(cuerpo["detail"], str)
    return {"campo": campo, "mensaje": mensaje} in cuerpo["errores"]


# ---------- Alta y consulta ----------

def test_p2_01_crear_pieza_valida(cliente):
    respuesta = cliente.post(URL, json=pieza_valida("PRUEBA Alta"))
    assert respuesta.status_code == 201
    pieza = respuesta.json()
    assert isinstance(pieza["id_pieza"], int)
    assert pieza["nombre"] == "PRUEBA Alta"
    assert pieza["descripcion"] == "Pieza de prueba"
    assert pieza["cantidad"] == 10
    assert pieza["stock_minimo"] == 5
    assert pieza["precio_unitario"] == "100.00"
    assert pieza["stock_bajo"] is False


def test_p2_02_consultar_pieza_creada(cliente):
    creada = crear(cliente, nombre="PRUEBA Consulta")
    respuesta = cliente.get(f"{URL}/{creada['id_pieza']}")
    assert respuesta.status_code == 200
    assert respuesta.json() == creada


def test_p2_03_consultar_pieza_inexistente(cliente):
    respuesta = cliente.get(f"{URL}/{ID_INEXISTENTE}")
    assert respuesta.status_code == 404
    assert respuesta.json() == {"detail": "La pieza no existe", "errores": []}


def test_p2_04_nombre_de_puros_espacios(cliente):
    respuesta = cliente.post(URL, json=pieza_valida("    "))
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "nombre", "El nombre es obligatorio")


def test_p2_05_limpia_espacios_y_descripcion_vacia(cliente):
    pieza = crear(cliente, nombre="  PRUEBA espacios  ", descripcion="   ")
    assert pieza["nombre"] == "PRUEBA espacios"
    assert pieza["descripcion"] is None


def test_p2_06_nombre_repetido_sin_importar_mayusculas(cliente):
    crear(cliente, nombre="PRUEBA Repetida")
    respuesta = cliente.post(URL, json=pieza_valida("PRUEBA REPETIDA"))
    assert respuesta.status_code == 409
    assert tiene_error(respuesta, "nombre", "Ya existe una pieza con ese nombre")


def test_p2_07_cantidad_negativa(cliente):
    # RN-01, RN-04
    respuesta = cliente.post(URL, json=pieza_valida(cantidad=-1))
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "cantidad", "La cantidad no puede ser negativa")


def test_p2_08_stock_minimo_negativo(cliente):
    # RN-04
    respuesta = cliente.post(URL, json=pieza_valida(stock_minimo=-1))
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "stock_minimo", "El stock mínimo no puede ser negativo")


def test_p2_09_cantidad_y_minimo_en_cero(cliente):
    # RN-04: el 0 sí se permite; RN-02: 0 <= 0 es stock bajo
    pieza = crear(cliente, nombre="PRUEBA Ceros", cantidad=0, stock_minimo=0)
    assert pieza["stock_bajo"] is True


def test_p2_10_precio_cero_o_negativo(cliente):
    # RN-03
    for precio in (0, -5):
        respuesta = cliente.post(URL, json=pieza_valida(precio_unitario=precio))
        assert respuesta.status_code == 400
        assert tiene_error(respuesta, "precio_unitario", "El precio debe ser mayor a 0")


def test_p2_11_precio_minimo_valido(cliente):
    # RN-03
    pieza = crear(cliente, nombre="PRUEBA Centavo", precio_unitario="0.01")
    assert pieza["precio_unitario"] == "0.01"


def test_p2_12_precio_con_tres_decimales(cliente):
    respuesta = cliente.post(URL, json=pieza_valida(precio_unitario="10.999"))
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "precio_unitario", "El precio solo puede tener 2 decimales")


# ---------- Stock bajo, búsqueda y resumen ----------

def test_p2_13_stock_bajo_incluye_el_igual(cliente):
    # RN-02: cantidad <= stock_minimo
    baja = crear(cliente, nombre="PRUEBA Baja", cantidad=2, stock_minimo=5)
    igual = crear(cliente, nombre="PRUEBA Igual", cantidad=5, stock_minimo=5)
    alta = crear(cliente, nombre="PRUEBA Suficiente", cantidad=6, stock_minimo=5)
    assert baja["stock_bajo"] is True
    assert igual["stock_bajo"] is True
    assert alta["stock_bajo"] is False


def test_p2_14_filtro_stock_bajo(cliente):
    # RN-02
    baja = crear(cliente, nombre="PRUEBA Baja", cantidad=2, stock_minimo=5)
    igual = crear(cliente, nombre="PRUEBA Igual", cantidad=5, stock_minimo=5)
    alta = crear(cliente, nombre="PRUEBA Suficiente", cantidad=6, stock_minimo=5)

    bajas = cliente.get(URL, params={"stock_bajo": "true"}).json()
    assert all(p["stock_bajo"] is True for p in bajas)
    ids_bajas = {p["id_pieza"] for p in bajas}
    assert baja["id_pieza"] in ids_bajas
    assert igual["id_pieza"] in ids_bajas

    suficientes = cliente.get(URL, params={"stock_bajo": "false"}).json()
    assert all(p["stock_bajo"] is False for p in suficientes)
    assert alta["id_pieza"] in {p["id_pieza"] for p in suficientes}


def test_p2_15_buscar_sin_distinguir_mayusculas(cliente):
    pieza = crear(cliente, nombre="PRUEBA Zapata Especial")
    encontradas = cliente.get(URL, params={"buscar": "zapata especial"}).json()
    assert pieza["id_pieza"] in {p["id_pieza"] for p in encontradas}

    ninguna = cliente.get(URL, params={"buscar": "xqzw-no-existe"}).json()
    assert ninguna == []


def test_p2_16_porcentaje_no_es_comodin(cliente):
    todas = cliente.get(URL).json()
    con_porcentaje = cliente.get(URL, params={"buscar": "%"}).json()
    assert len(con_porcentaje) < len(todas)


def test_p2_17_buscar_por_descripcion(cliente):
    pieza = crear(cliente, nombre="PRUEBA Por descripcion", descripcion="texto unico qzx")
    encontradas = cliente.get(URL, params={"buscar": "QZX"}).json()
    assert pieza["id_pieza"] in {p["id_pieza"] for p in encontradas}


def test_p2_18_resumen_cambia_al_crear(cliente):
    # RN-05 y RN-02
    antes = cliente.get(f"{URL}/resumen").json()
    crear(cliente, nombre="PRUEBA Resumen", cantidad=3, stock_minimo=5, precio_unitario="10.50")
    despues = cliente.get(f"{URL}/resumen").json()

    assert despues["total_piezas"] == antes["total_piezas"] + 1
    assert despues["stock_bajo"] == antes["stock_bajo"] + 1
    diferencia = Decimal(despues["valor_inventario"]) - Decimal(antes["valor_inventario"])
    assert diferencia == Decimal("31.50")


# ---------- Edición ----------

def test_p2_19_editar_los_cinco_campos(cliente):
    pieza = crear(cliente, nombre="PRUEBA Editar")
    nuevos = {
        "nombre": "PRUEBA Editada",
        "descripcion": "Otra descripcion",
        "cantidad": 1,
        "stock_minimo": 4,
        "precio_unitario": "55.25",
    }
    respuesta = cliente.put(f"{URL}/{pieza['id_pieza']}", json=nuevos)
    assert respuesta.status_code == 200

    leida = cliente.get(f"{URL}/{pieza['id_pieza']}").json()
    for campo, valor in nuevos.items():
        assert leida[campo] == valor
    assert leida["stock_bajo"] is True


def test_p2_20_editar_con_datos_invalidos_no_cambia_nada(cliente):
    # RN-01, RN-03
    pieza = crear(cliente, nombre="PRUEBA Sin cambios")
    url_pieza = f"{URL}/{pieza['id_pieza']}"

    r1 = cliente.put(url_pieza, json=pieza_valida("PRUEBA Sin cambios", cantidad=-5))
    r2 = cliente.put(url_pieza, json=pieza_valida("PRUEBA Sin cambios", precio_unitario=0))
    assert r1.status_code == 400
    assert r2.status_code == 400

    assert cliente.get(url_pieza).json() == pieza


def test_p2_21_editar_pieza_inexistente(cliente):
    respuesta = cliente.put(f"{URL}/{ID_INEXISTENTE}", json=pieza_valida("PRUEBA Fantasma"))
    assert respuesta.status_code == 404


def test_p2_22_editar_nombre_propio_y_ajeno(cliente):
    a = crear(cliente, nombre="PRUEBA A")
    crear(cliente, nombre="PRUEBA B")
    url_a = f"{URL}/{a['id_pieza']}"

    mismo_nombre = cliente.put(url_a, json=pieza_valida("PRUEBA A"))
    assert mismo_nombre.status_code == 200

    nombre_ajeno = cliente.put(url_a, json=pieza_valida("PRUEBA B"))
    assert nombre_ajeno.status_code == 409


# ---------- Baja ----------

def test_p2_23_eliminar_pieza(cliente):
    pieza = crear(cliente, nombre="PRUEBA Borrar")
    respuesta = cliente.delete(f"{URL}/{pieza['id_pieza']}")
    assert respuesta.status_code == 204
    assert respuesta.content == b""
    assert cliente.get(f"{URL}/{pieza['id_pieza']}").status_code == 404


def test_p2_24_no_eliminar_pieza_usada_en_citas(cliente, db):
    id_usada = db.scalars(select(CitaPieza.id_pieza).limit(1)).first()
    assert id_usada is not None

    respuesta = cliente.delete(f"{URL}/{id_usada}")
    assert respuesta.status_code == 409
    assert respuesta.json()["detail"] == "No se puede eliminar: la pieza ya se usó en citas"
    assert cliente.get(f"{URL}/{id_usada}").status_code == 200


def test_p2_25_eliminar_pieza_inexistente(cliente):
    assert cliente.delete(f"{URL}/{ID_INEXISTENTE}").status_code == 404


# ---------- Aislamiento, errores múltiples y acentos ----------

def test_p2_26_lo_creado_en_la_prueba_no_llega_a_la_base(cliente):
    crear(cliente, nombre="PRUEBA Aislamiento")
    conexion = engine.connect()
    try:
        encontrada = conexion.execute(
            text('SELECT COUNT(*) FROM "BD".inventario WHERE nombre = :nombre'),
            {"nombre": "PRUEBA Aislamiento"},
        ).scalar_one()
    finally:
        conexion.close()
    assert encontrada == 0


def test_p2_27_reporta_todos_los_errores_a_la_vez(cliente):
    # RN-01, RN-03
    respuesta = cliente.post(URL, json=pieza_valida("", cantidad=-1, precio_unitario=0))
    assert respuesta.status_code == 400
    cuerpo = respuesta.json()
    assert cuerpo["detail"] == "Revisa los datos marcados"
    campos = {e["campo"] for e in cuerpo["errores"]}
    assert campos == {"nombre", "cantidad", "precio_unitario"}


def test_p2_28_guarda_sin_acentos_y_conserva_la_enie(cliente):
    pieza = crear(cliente, nombre="PRUEBA Bujía Ñandú", descripcion="Líquido especial")
    assert pieza["nombre"] == "PRUEBA Bujia Ñandu"
    assert pieza["descripcion"] == "Liquido especial"


def test_p2_29_buscar_con_acentos(cliente):
    pieza = crear(cliente, nombre="PRUEBA Bujía Ñandú")
    encontradas = cliente.get(URL, params={"buscar": "bujía ñandú"}).json()
    assert pieza["id_pieza"] in {p["id_pieza"] for p in encontradas}


def test_p2_30_datos_reales_sin_acentos(cliente):
    acentos = set("áéíóúÁÉÍÓÚ")
    for pieza in cliente.get(URL).json():
        textos = pieza["nombre"] + (pieza["descripcion"] or "")
        assert not (set(textos) & acentos), pieza["nombre"]


# ---------- Casos límite (corrección de la revisión) ----------

def test_p2_38_precio_enorme(cliente):
    respuesta = cliente.post(URL, json=pieza_valida("PRUEBA Enorme", precio_unitario="1e30"))
    assert respuesta.status_code == 400
    assert tiene_error(respuesta, "precio_unitario", "El precio es demasiado alto")


def test_p2_39_id_fuera_de_rango(cliente):
    fuera = 2147483648
    respuestas = [
        cliente.get(f"{URL}/{fuera}"),
        cliente.put(f"{URL}/{fuera}", json=pieza_valida("PRUEBA Fuera de rango")),
        cliente.delete(f"{URL}/{fuera}"),
        cliente.get(f"{URL}/0"),
    ]
    for respuesta in respuestas:
        assert respuesta.status_code == 404
        assert respuesta.json()["detail"] == "La pieza no existe"


# ---------- Fase 5: niveles de stock (RN-16) ----------

def estados_con_minimo(cliente, prefijo, stock_minimo, cantidades):
    """Crea una pieza por cantidad y devuelve las piezas creadas, en el mismo orden."""
    return [
        crear(cliente, nombre=f"{prefijo} {cantidad}", cantidad=cantidad, stock_minimo=stock_minimo)
        for cantidad in cantidades
    ]


def test_p5_01_niveles_con_minimo_par(cliente):
    piezas = estados_con_minimo(cliente, "PRUEBA Nivel par", 6, [0, 3, 4, 6, 7])
    assert [p["estado_stock"] for p in piezas] == ["critico", "critico", "bajo", "bajo", "suficiente"]


def test_p5_02_niveles_con_minimo_impar(cliente):
    piezas = estados_con_minimo(cliente, "PRUEBA Nivel impar", 5, [2, 3, 5, 6])
    assert [p["estado_stock"] for p in piezas] == ["critico", "bajo", "bajo", "suficiente"]


def test_p5_03_niveles_con_minimo_cero_y_uno(cliente):
    cero_cero = crear(cliente, nombre="PRUEBA Minimo 0 cant 0", cantidad=0, stock_minimo=0)
    cero_uno = crear(cliente, nombre="PRUEBA Minimo 0 cant 1", cantidad=1, stock_minimo=0)
    uno_uno = crear(cliente, nombre="PRUEBA Minimo 1 cant 1", cantidad=1, stock_minimo=1)
    assert cero_cero["estado_stock"] == "critico"
    assert cero_uno["estado_stock"] == "suficiente"
    assert uno_uno["estado_stock"] == "bajo"


def test_p5_04_stock_bajo_coincide_con_estado(cliente):
    piezas = estados_con_minimo(cliente, "PRUEBA Coincide", 6, [0, 3, 4, 6, 7])
    for pieza in piezas:
        assert pieza["stock_bajo"] == (pieza["estado_stock"] in ("bajo", "critico")), pieza


def test_p5_05_resumen_cuenta_cada_nivel(cliente):
    antes = cliente.get(f"{URL}/resumen").json()
    crear(cliente, nombre="PRUEBA Resumen critica", cantidad=1, stock_minimo=6)
    crear(cliente, nombre="PRUEBA Resumen baja", cantidad=5, stock_minimo=6)
    crear(cliente, nombre="PRUEBA Resumen suficiente", cantidad=9, stock_minimo=6)
    despues = cliente.get(f"{URL}/resumen").json()

    assert despues["critico"] == antes["critico"] + 1
    assert despues["bajo"] == antes["bajo"] + 1
    assert despues["suficiente"] == antes["suficiente"] + 1
    assert despues["total_piezas"] == antes["total_piezas"] + 3
    assert despues["stock_bajo"] == antes["stock_bajo"] + 2


def test_p5_06_resumen_real_cuadra(cliente):
    resumen = cliente.get(f"{URL}/resumen").json()
    assert resumen["suficiente"] + resumen["bajo"] + resumen["critico"] == resumen["total_piezas"]
    assert resumen["bajo"] + resumen["critico"] == resumen["stock_bajo"]


def test_p5_07_filtro_por_estado(cliente):
    critica = crear(cliente, nombre="PRUEBA Filtro critica", cantidad=0, stock_minimo=6)
    baja = crear(cliente, nombre="PRUEBA Filtro baja", cantidad=4, stock_minimo=6)
    suficiente = crear(cliente, nombre="PRUEBA Filtro suficiente", cantidad=7, stock_minimo=6)

    def ids(estado):
        respuesta = cliente.get(URL, params={"buscar": "PRUEBA", "estado_stock": estado})
        assert respuesta.status_code == 200
        return [p["id_pieza"] for p in respuesta.json()]

    assert ids("critico") == [critica["id_pieza"]]
    assert ids("bajo") == [baja["id_pieza"]]
    assert ids("suficiente") == [suficiente["id_pieza"]]
    # Se limpia y se pasa a minúsculas: responde igual que "critico"
    assert ids(" CRITICO ") == ids("critico")


def test_p5_08_filtro_de_estado_invalido(cliente):
    respuesta = cliente.get(URL, params={"estado_stock": "otro"})
    assert respuesta.status_code == 400
    mensaje = "El filtro de estado solo acepta: suficiente, bajo o critico"
    assert respuesta.json()["detail"] == mensaje
    assert tiene_error(respuesta, "estado_stock", mensaje)
