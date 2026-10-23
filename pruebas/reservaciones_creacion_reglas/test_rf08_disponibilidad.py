from conftest import consultar_disponibilidad, fecha_futura, foto_reservaciones, insertar_reserva_directa


def test_CP_RF08_01_disponible_sin_conflicto(bd_p2, chk):
    r = consultar_disponibilidad("S01", fecha_futura(), "10:00", 1)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("disponible") is True, f"una sala libre se reportó no disponible: {r}")


def test_CP_RF08_02_no_disponible_con_conflicto(bd_p2, chk):
    f = fecha_futura()
    insertar_reserva_directa("A001234567", "S01", f, "10:00", 2, 2)
    r = consultar_disponibilidad("S01", f, "11:00", 1)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("disponible") is False, "se reportó disponible un horario superpuesto")
    chk.ok("conflicto" in r.get("motivo", "").lower(), f"el motivo no identifica el conflicto: {r}")


def test_CP_RF08_03_consulta_no_modifica_almacenamiento(bd_p2, chk):
    f = fecha_futura()
    insertar_reserva_directa("A001234567", "S02", f, "12:00", 1, 2)
    antes = foto_reservaciones()
    r = consultar_disponibilidad("S01", f, "10:00", 1)
    despues = foto_reservaciones()
    chk.obs(f"respuesta={r}; antes={antes}; después={despues}")
    chk.ok(antes == despues, "consultar disponibilidad modificó las reservaciones")
