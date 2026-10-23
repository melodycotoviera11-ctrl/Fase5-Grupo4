from conftest import CARNE_ACTIVO, crear_valida, crear_reservaciones_recurrentes, fecha_futura


def test_CP_RN11_01_maximo_tres_activas(bd_p2, chk):
    resultados = [
        crear_valida(codigo_sala="S01", fecha=fecha_futura(30), hora_inicio="10:00"),
        crear_valida(codigo_sala="S02", fecha=fecha_futura(31), hora_inicio="10:00"),
        crear_valida(codigo_sala="S03", fecha=fecha_futura(32), hora_inicio="10:00"),
    ]
    cuarto = crear_valida(codigo_sala="S05", fecha=fecha_futura(33), hora_inicio="10:00", cantidad_personas=1)
    chk.obs(f"primeras={resultados}; cuarta={cuarto}")
    chk.ok(all(r.get("exito") is True for r in resultados), "alguna de las primeras tres reservaciones válidas falló")
    chk.ok(cuarto.get("exito") is False and "3" in cuarto.get("mensaje", ""), f"se permitió superar el máximo de tres: {cuarto}")


def test_CP_RN11_02_recurrencias_respetan_maximo_tres(bd_p2, chk):
    serie = crear_reservaciones_recurrentes(
        CARNE_ACTIVO, "S01", fecha_futura(30), "10:00", 1, 2, 3
    )
    adicional = crear_valida(codigo_sala="S02", fecha=fecha_futura(31), hora_inicio="12:00")
    chk.obs(f"serie={serie}; adicional={adicional}")
    chk.ok(serie.get("exito") is True and len(serie.get("ids", [])) == 3, f"no se creó la serie de 3 ocurrencias: {serie}")
    chk.ok(adicional.get("exito") is False and "3" in adicional.get("mensaje", ""),
           "las 3 ocurrencias recurrentes no consumieron el máximo de 3 reservaciones activas")
