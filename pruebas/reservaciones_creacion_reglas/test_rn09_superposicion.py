from conftest import crear_valida, fecha_futura, insertar_reserva_directa


def _probar(chk, existente_hora, existente_duracion, nueva_hora, nueva_duracion):
    f = fecha_futura()
    insertar_reserva_directa("B009876543", "S01", f, existente_hora, existente_duracion, 2)
    r = crear_valida(fecha=f, hora_inicio=nueva_hora, duracion=nueva_duracion)
    chk.obs(f"existente={existente_hora}/{existente_duracion}h; nueva={nueva_hora}/{nueva_duracion}h; respuesta={r}")
    chk.ok(r.get("exito") is False and "conflicto" in r.get("mensaje", "").lower(), f"no detectó la superposición: {r}")


def test_CP_RN09_01_superposicion_total(bd_p2, chk):
    _probar(chk, "10:00", 2, "10:00", 2)


def test_CP_RN09_02_superposicion_parcial_inicio(bd_p2, chk):
    _probar(chk, "10:00", 2, "09:00", 2)


def test_CP_RN09_03_superposicion_parcial_final(bd_p2, chk):
    _probar(chk, "10:00", 2, "11:00", 2)


def test_CP_RN09_04_nueva_envuelve_existente(bd_p2, chk):
    _probar(chk, "10:00", 1, "09:00", 2)
