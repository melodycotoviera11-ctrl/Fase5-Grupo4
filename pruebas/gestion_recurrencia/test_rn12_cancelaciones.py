"""RN-12: reservas canceladas conservan historial y liberan horario."""
from datetime import date, timedelta
from src.model.reservaciones.servicio import (
    cancelar_reservacion, consultar_reservaciones, crear_reservacion,
)


def _por_id(identificador):
    respuesta = consultar_reservaciones()
    assert respuesta['exito'], respuesta
    return next(r for r in respuesta['reservaciones'] if r['id'] == identificador)


def test_CP_RN12_01_cancelada_permanece_en_historial(bd_p3, insertar_reserva):
    identificador = insertar_reserva('A001234567', 'S01', 3, '10:00', 1, 2)
    antes = _por_id(identificador)
    respuesta = cancelar_reservacion(identificador)
    assert respuesta['exito'] is True, respuesta
    despues = _por_id(identificador)
    assert despues['estado'] == 'cancelada'
    assert despues['id'] == identificador
    for campo in ('carne', 'sala', 'fecha', 'hora_inicio', 'hora_fin', 'cantidad_personas'):
        assert despues[campo] == antes[campo], campo
    assert len(consultar_reservaciones()['reservaciones']) == 1


def test_CP_RN12_02_cancelacion_libera_horario(bd_p3, insertar_reserva):
    identificador = insertar_reserva('A001234567', 'S01', 3, '10:00', 1, 2)
    assert cancelar_reservacion(identificador)['exito'] is True
    fecha = (date.today() + timedelta(days=3)).isoformat()
    respuesta = crear_reservacion('B009876543', 'S01', fecha, '10:00', 1, 2)
    assert respuesta['exito'] is True, respuesta
    assert respuesta['id'] != identificador
    reservas = {r['id']: r for r in consultar_reservaciones()['reservaciones']}
    assert len(reservas) == 2
    assert reservas[identificador]['estado'] == 'cancelada'
    assert reservas[respuesta['id']]['estado'] == 'activa'
