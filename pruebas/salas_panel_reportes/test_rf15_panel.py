"""Fase 5, Persona 4: RF-15 Mostrar panel y disponibilidad (capa lógica y controlador, sin clics)."""
from datetime import date, datetime, time, timedelta

from src.controller.controller import ControladorAplicacion
from src.model.panel.servicio import consultar_panel
from src.model.reservaciones.servicio import cancelar_reservacion, crear_reservacion, modificar_reservacion
from src.model.salas.servicio import registrar_sala

from apoyo_p4 import fecha_rel, insertar_reserva

D = date.today() + timedelta(days=30)
AHORA = datetime.combine(D, time(9, 30))


def _iso(dias):
    return (D + timedelta(days=dias)).isoformat()


def _escenario():
    """Datos DS-P4-PANEL alrededor de la fecha de referencia D (09:30)."""
    return {
        "hoy_pasada": insertar_reserva("A001234567", "S01", _iso(0), "08:00", personas=2),
        "hoy_futura": insertar_reserva("B009876543", "S02", _iso(0), "10:00", 2, 3),
        "hoy_cancelada": insertar_reserva("A001234567", "S01", _iso(0), "14:00", personas=1, estado="cancelada"),
        "manana": insertar_reserva("B009876543", "S03", _iso(1), "09:00", personas=4),
        "ayer": insertar_reserva("A001234567", "S02", _iso(-1), "10:00", personas=2),
    }


def test_CP_RF15_01_contenido_del_panel(bd_p4, chk):
    """Muestra reservaciones del día, próximas y ocupación por sala."""
    ids = _escenario()
    p = consultar_panel(ahora=AHORA)
    hoy = [r["id"] for r in p["reservaciones_hoy"]]
    prox = [r["id"] for r in p["proximas_reservaciones"]]
    ocup = {o["codigo"]: o["reservaciones_activas"] for o in p["ocupacion_salas"]}
    chk.obs(f"hoy={hoy}; próximas={prox}; ocupación={ocup}")
    chk.ok(p["exito"] is True, f"el panel no respondió con éxito: {p.get('mensaje')}")
    chk.ok({ids["hoy_pasada"], ids["hoy_futura"]} <= set(hoy) and ids["manana"] not in hoy
           and ids["ayer"] not in hoy, "las reservaciones del día no corresponden a la fecha de referencia")
    chk.ok(prox == [ids["hoy_futura"], ids["manana"]],
           "las próximas reservaciones deben ser solo las activas posteriores a la hora de referencia, en orden")
    chk.ok(sorted(ocup) == ["S01", "S02", "S03", "S04", "S05"], "la ocupación no incluye todas las salas")
    chk.ok(ocup.get("S01") == 1 and ocup.get("S02") == 1 and ocup.get("S03") == 0,
           "la ocupación del día no cuenta solo las reservaciones activas")


def test_CP_RF15_02_filtros_combinados(bd_p4, chk):
    """Fecha, sala y estado pueden combinarse (AND) y se normalizan."""
    ids = _escenario()
    casos = [
        ({"fecha": _iso(0)}, {ids["hoy_pasada"], ids["hoy_futura"], ids["hoy_cancelada"]}),
        ({"fecha": _iso(0), "codigo_sala": "S01"}, {ids["hoy_pasada"], ids["hoy_cancelada"]}),
        ({"fecha": _iso(0), "codigo_sala": "S01", "estado": "cancelada"}, {ids["hoy_cancelada"]}),
        ({"codigo_sala": "S02", "estado": "activa"}, {ids["hoy_futura"], ids["ayer"]}),
        ({"codigo_sala": " s01 ", "estado": " ACTIVA "}, {ids["hoy_pasada"]}),
    ]
    for filtros, esperado in casos:
        r = consultar_panel(ahora=AHORA, **filtros)
        obtenido = {x["id"] for x in r["resultados"]}
        chk.obs(f"{filtros} -> {sorted(obtenido)}")
        chk.ok(r["exito"] and obtenido == esperado, f"filtro {filtros}: esperado {sorted(esperado)}")


def test_CP_RF15_03_estado_vacio_comprensible(bd_p4, chk):
    """Sin resultados se presenta un estado vacío comprensible, sin error."""
    _escenario()
    r = consultar_panel(fecha=_iso(10), codigo_sala="S05", estado="cancelada", ahora=AHORA)
    chk.obs(f"exito={r['exito']}; mensaje={r['mensaje']!r}; resultados={r['resultados']}")
    chk.ok(r["exito"] is True and r["resultados"] == [], "la consulta sin coincidencias no devolvió lista vacía")
    chk.ok("no hay" in r["mensaje"].lower(), "el mensaje de estado vacío no es comprensible")


def test_CP_RF15_04_se_actualiza_tras_crear_modificar_cancelar(bd_p4, chk):
    """El panel (vía controlador de la interfaz) refleja cada operación inmediatamente."""
    ctl = ControladorAplicacion()
    f = fecha_rel(3)
    creada = crear_reservacion("A001234567", "S01", f, "10:00", 1, 2)
    chk.ok(creada["exito"], f"no se pudo crear la reservación: {creada}")
    rid = creada.get("id")
    p1 = ctl.obtener_panel(fecha=f)
    chk.ok(any(x["id"] == rid and x["sala"] == "S01" for x in p1["resultados"]), "el panel no muestra la reserva creada")

    mod = modificar_reservacion(rid, codigo_sala="S02", hora_inicio="11:00")
    p2 = ctl.obtener_panel(fecha=f, codigo_sala="S02")
    p2_vieja = ctl.obtener_panel(fecha=f, codigo_sala="S01")
    chk.ok(mod["exito"] and any(x["id"] == rid and x["hora_inicio"] == "11:00" for x in p2["resultados"]),
           "el panel no refleja la modificación")
    chk.ok(not p2_vieja["resultados"], "la reserva sigue apareciendo en la sala anterior")

    can = cancelar_reservacion(rid)
    p3 = ctl.obtener_panel(fecha=f)
    estado = next((x["estado"] for x in p3["resultados"] if x["id"] == rid), None)
    chk.ok(can["exito"] and estado == "cancelada", "el panel no refleja la cancelación")
    chk.ok(all(x["id"] != rid for x in p3["proximas_reservaciones"]), "la reserva cancelada sigue en próximas")
    chk.obs(f"creada={rid}; tras modificar={[(x['id'], x['sala'], x['hora_inicio']) for x in p2['resultados']]}; "
            f"tras cancelar estado={estado}")


def test_CP_RF15_05_filtros_invalidos_no_rompen(bd_p4, chk):
    """Filtros inválidos devuelven un mensaje controlado (RNF-05)."""
    casos = [{"fecha": "15/05/2030"}, {"fecha": "2030-02-30"}, {"estado": "pendiente"}, {"codigo_sala": 5}]
    for filtros in casos:
        try:
            r = consultar_panel(**filtros)
            chk.obs(f"{filtros} -> exito={r['exito']}, mensaje={r['mensaje']!r}")
            chk.ok(r["exito"] is False and r["mensaje"], f"filtro inválido aceptado: {filtros}")
        except Exception as e:  # noqa: BLE001
            chk.ok(False, f"excepción con {filtros}: {type(e).__name__}: {e}")


def test_CP_RF15_06_filtro_por_sala_registrada_por_rf12(bd_p4, chk):
    """El filtro por sala debe encontrar las reservas de cualquier sala que RF-12 permitió registrar."""
    reg = registrar_sala("s06", "Sala registrada en minúscula", 4)
    chk.obs(f"registro sala 's06' -> {reg}")
    if not reg["exito"]:
        chk.obs("RF-12 no permite el código en minúscula; no hay inconsistencia que verificar")
        return
    creada = crear_reservacion("A001234567", "s06", fecha_rel(3), "10:00", 1, 2)
    r = consultar_panel(codigo_sala="s06")
    chk.obs(f"reserva={creada}; filtros aplicados={r['filtros']}; resultados={[x['id'] for x in r['resultados']]}")
    chk.ok(creada["exito"] and any(x["id"] == creada.get("id") for x in r["resultados"]),
           "la reserva de la sala 's06' no aparece al filtrar el panel por esa sala")
