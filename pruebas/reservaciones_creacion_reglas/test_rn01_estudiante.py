from conftest import crear_valida, foto_reservaciones


def test_CP_RN01_01_rechaza_estudiante_inexistente(bd_p2, chk):
    antes = foto_reservaciones()
    r = crear_valida(carne="Z999999999")
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False, "se aceptó un estudiante inexistente")
    chk.ok("no existe" in r.get("mensaje", "").lower(), f"mensaje inesperado: {r}")
    chk.ok(foto_reservaciones() == antes, "el intento inválido alteró las reservaciones")


def test_CP_RN01_02_rechaza_estudiante_inactivo(bd_p2, chk):
    antes = foto_reservaciones()
    r = crear_valida(carne="C004567890")
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False, "se aceptó una reservación para estudiante inactivo")
    chk.ok("activo" in r.get("mensaje", "").lower(), f"mensaje inesperado: {r}")
    chk.ok(foto_reservaciones() == antes, "el intento inválido alteró las reservaciones")
