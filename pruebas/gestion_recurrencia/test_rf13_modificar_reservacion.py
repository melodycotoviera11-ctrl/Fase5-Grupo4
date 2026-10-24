"""Fase 5, Persona 3: RF-13, casos CP-RF13-01 a CP-RF13-05.

Pruebas cruzadas contra el servicio original del Grupo 6.
Cada prueba emplea la BD SQLite temporal definida en conftest.py.
"""
from datetime import date, timedelta

from src.model.reservaciones.servicio import modificar_reservacion, consultar_reservaciones


def _reserva_por_id(identificador):
    respuesta = consultar_reservaciones()
    assert respuesta['exito'] is True, respuesta
    return next(r for r in respuesta['reservaciones'] if r['id'] == identificador)


def test_CP_RF13_01_modificacion_valida_conserva_id(bd_p3, insertar_reserva):
    """Modifica sala, fecha, inicio, duración y personas; preserva ID."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '10:00', 1, 2)
    nueva_fecha = (date.today() + timedelta(days=4)).isoformat()

    respuesta = modificar_reservacion(
        identificador, codigo_sala='S02', fecha=nueva_fecha,
        hora_inicio='12:00', duracion=2, cantidad_personas=5,
    )

    assert respuesta['exito'] is True, respuesta
    assert respuesta['id'] == identificador
    reserva = _reserva_por_id(identificador)
    assert reserva['id'] == identificador
    assert reserva['sala'] == 'S02'
    assert reserva['fecha'] == nueva_fecha
    assert reserva['hora_inicio'] == '12:00'
    assert reserva['hora_fin'] == '14:00'
    assert reserva['duracion_horas'] == 2
    assert reserva['cantidad_personas'] == 5
    assert reserva['estado'] == 'activa'
    assert len(consultar_reservaciones()['reservaciones']) == 1


def test_CP_RF13_02_conflicto_preserva_datos_originales(bd_p3, insertar_reserva):
    """Modificar hacia un horario ocupado debe rechazarse sin cambios."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '08:00', 1, 2)
    insertar_reserva('B009876543', 'S01', 2, '10:00', 2, 3)
    antes = _reserva_por_id(identificador).copy()

    respuesta = modificar_reservacion(identificador, hora_inicio='11:00', duracion=1)

    assert respuesta['exito'] is False, respuesta
    assert 'conflict' in respuesta['mensaje'].lower() or 'ocupad' in respuesta['mensaje'].lower() or 'disponib' in respuesta['mensaje'].lower(), respuesta
    assert _reserva_por_id(identificador) == antes
    assert len(consultar_reservaciones()['reservaciones']) == 2


def test_CP_RF13_03_no_modifica_reservacion_cancelada(bd_p3, insertar_reserva):
    """Una reserva cancelada debe mantenerse intacta."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '10:00', 1, 2, 'cancelada')
    antes = _reserva_por_id(identificador).copy()

    respuesta = modificar_reservacion(identificador, hora_inicio='12:00')

    assert respuesta['exito'] is False, respuesta
    assert 'cancelad' in respuesta['mensaje'].lower(), respuesta
    assert _reserva_por_id(identificador) == antes


def test_CP_RF13_04_no_conflicto_con_la_misma_reserva(bd_p3, insertar_reserva):
    """Al modificar una reserva se debe excluir su propio ID del conflicto."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '10:00', 1, 2)

    respuesta = modificar_reservacion(identificador, cantidad_personas=3)

    assert respuesta['exito'] is True, respuesta
    reserva = _reserva_por_id(identificador)
    assert reserva['id'] == identificador
    assert reserva['hora_inicio'] == '10:00'
    assert reserva['cantidad_personas'] == 3
    assert len(consultar_reservaciones()['reservaciones']) == 1


def test_CP_RF13_05_rechaza_capacidad_superada(bd_p3, insertar_reserva):
    """No permite ampliar personas por encima de capacidad de S01 (4)."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '10:00', 1, 2)
    antes = _reserva_por_id(identificador).copy()

    respuesta = modificar_reservacion(identificador, cantidad_personas=5)

    assert respuesta['exito'] is False, respuesta
    assert 'capacidad' in respuesta['mensaje'].lower(), respuesta
    assert _reserva_por_id(identificador) == antes
