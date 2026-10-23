from conftest import crear_valida, fecha_futura, insertar_reserva_directa


def test_CP_RN10_01_permite_consecutiva_posterior(bd_p2, chk):
    f = fecha_futura()
    insertar_reserva_directa("B009876543", "S01", f, "10:00", 1, 2)
    r = crear_valida(fecha=f, hora_inicio="11:00", duracion=1)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is True, f"rechazó una reservación consecutiva posterior: {r}")


def test_CP_RN10_02_permite_consecutiva_anterior(bd_p2, chk):
    f = fecha_futura()
    insertar_reserva_directa("B009876543", "S01", f, "10:00", 2, 2)
    r = crear_valida(fecha=f, hora_inicio="08:00", duracion=2)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is True, f"rechazó una reservación consecutiva anterior: {r}")
