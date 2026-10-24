"""RF-14: seis casos de gestión de recurrencia de la Fase 4, Grupo 4.

La BD de cada prueba es temporal (fixture bd_p3 en conftest.py).
No se modifica el código productivo del Grupo 6.
"""
from datetime import date, timedelta

from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservaciones_recurrentes,
    previsualizar_reservaciones_recurrentes,
)

CARNE = "A001234567"


def datos_serie(semanas=3):
    return {
        "carne": CARNE,
        "codigo_sala": "S01",
        "fecha": (date.today() + timedelta(days=14)).isoformat(),
        "hora_inicio": "10:00",
        "duracion": 1,
        "cantidad_personas": 2,
        "semanas": semanas,
    }


def reservas_serie(serie_id):
    resultado = consultar_reservaciones()
    assert resultado["exito"], resultado["mensaje"]
    return [r for r in resultado["reservaciones"] if r["serie_id"] == serie_id]


def test_CP_RF14_01_previsualiza_serie_sin_guardar(bd_p3):
    """CP-RF14-01: resumen previo de tres ocurrencias, sin escritura."""
    anterior = bd_p3.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0]
    resumen = previsualizar_reservaciones_recurrentes(**datos_serie())
    posterior = bd_p3.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0]
    assert resumen["exito"], resumen["mensaje"]
    assert resumen["puede_crear"] is True
    assert len(resumen["ocurrencias"]) == 3
    assert all(o["disponible"] for o in resumen["ocurrencias"])
    assert posterior == anterior, "Previsualizar no debe guardar ninguna reservación"


def test_CP_RF14_02_crea_serie_tres_ocurrencias(bd_p3):
    """CP-RF14-02: tres fechas semanales, tres ID únicos y una serie."""
    previo = previsualizar_reservaciones_recurrentes(**datos_serie())
    assert previo["puede_crear"], previo["mensaje"]
    resultado = crear_reservaciones_recurrentes(**datos_serie())
    assert resultado["exito"], resultado["mensaje"]
    assert len(resultado["ids"]) == 3
    assert len(set(resultado["ids"])) == 3
    serie = reservas_serie(resultado["serie_id"])
    assert len(serie) == 3
    assert set(r["id"] for r in serie) == set(resultado["ids"])
    assert all(r["estado"] == "activa" for r in serie)
    fechas = sorted(date.fromisoformat(r["fecha"]) for r in serie)
    assert [(fechas[i + 1] - fechas[i]).days for i in range(2)] == [7, 7]


def test_CP_RF14_03_rechaza_una_y_nueve_semanas(bd_p3):
    """CP-RF14-03: fuera de límites 2–8 no debe crear filas."""
    for semanas in (1, 9):
        respuesta = crear_reservaciones_recurrentes(**datos_serie(semanas))
        assert respuesta["exito"] is False, f"Debió rechazarse {semanas} semanas"
    cantidad = bd_p3.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0]
    assert cantidad == 0, "Las series inválidas no deben persistir ocurrencias"


def test_CP_RF14_04_conflicto_no_guarda_serie(bd_p3, insertar_reserva):
    """CP-RF14-04: una fecha ocupada impide guardar la serie entera."""
    # La segunda semana de la serie se encuentra ocupada por otra persona.
    existente = insertar_reserva("B009876543", "S01", 21, "10:00")
    antes = [tuple(r) for r in bd_p3.execute("SELECT * FROM reservaciones ORDER BY id")]
    resumen = previsualizar_reservaciones_recurrentes(**datos_serie())
    assert len(resumen["ocurrencias"]) == 3
    assert resumen["puede_crear"] is False
    assert resumen["ocurrencias"][1]["disponible"] is False
    resultado = crear_reservaciones_recurrentes(**datos_serie())
    assert resultado["exito"] is False
    despues = [tuple(r) for r in bd_p3.execute("SELECT * FROM reservaciones ORDER BY id")]
    assert despues == antes, "Ante un conflicto no deben persistirse cambios parciales"


def test_CP_RF14_05_cancela_solo_una_ocurrencia(bd_p3):
    """CP-RF14-05: cancelar la segunda no afecta la primera y tercera."""
    creada = crear_reservaciones_recurrentes(**datos_serie())
    assert creada["exito"], creada["mensaje"]
    primera, segunda, tercera = creada["ids"]
    cancelacion = cancelar_reservacion(segunda)
    assert cancelacion["exito"], cancelacion["mensaje"]
    serie = {r["id"]: r for r in reservas_serie(creada["serie_id"])}
    assert set(serie) == {primera, segunda, tercera}
    assert [serie[x]["estado"] for x in (primera, segunda, tercera)] == [
        "activa", "cancelada", "activa"
    ]


def test_CP_RF14_06_cancela_ocurrencias_futuras(bd_p3):
    """CP-RF14-06: desde la segunda, cancelar segunda, tercera y cuarta."""
    creada = crear_reservaciones_recurrentes(**datos_serie(semanas=4))
    assert creada["exito"], creada["mensaje"]
    ids = creada["ids"]
    assert len(ids) == 4
    respuesta = cancelar_ocurrencias_futuras(ids[1])
    assert respuesta["exito"], respuesta["mensaje"]
    assert respuesta["cantidad_cancelada"] == 3
    assert set(respuesta["ids"]) == set(ids[1:])
    serie = {r["id"]: r for r in reservas_serie(creada["serie_id"])}
    assert set(serie) == set(ids)
    assert serie[ids[0]]["estado"] == "activa"
    assert all(serie[id_]["estado"] == "cancelada" for id_ in ids[1:])
