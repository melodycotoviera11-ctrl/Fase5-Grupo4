from conftest import crear_valida, foto_reservaciones


def test_CP_RF05_01_creacion_valida(bd_p2, chk):
    r = crear_valida()
    filas = foto_reservaciones()
    chk.obs(f"respuesta={r}; filas={filas}")
    chk.ok(r.get("exito") is True, f"se rechazó una reservación válida: {r}")
    chk.ok(r.get("id") == "R0001", f"ID inesperado: {r.get('id')}")
    chk.ok(len(filas) == 1 and filas[0][7] == "activa", "no quedó exactamente una reservación activa")
    chk.ok("R0001" in r.get("mensaje", ""), "la confirmación no muestra el ID asignado")


def test_CP_RF05_02_ids_unicos_automaticos(bd_p2, chk):
    r1 = crear_valida(codigo_sala="S01", hora_inicio="10:00")
    r2 = crear_valida(codigo_sala="S02", hora_inicio="12:00")
    chk.obs(f"r1={r1}; r2={r2}")
    chk.ok(r1.get("exito") and r2.get("exito"), "alguna reservación válida no se creó")
    chk.ok(r1.get("id") == "R0001" and r2.get("id") == "R0002", "los IDs no son automáticos/secuenciales")
    chk.ok(r1.get("id") != r2.get("id"), "los IDs se repitieron")
