"""Fase 5, Persona 3: pruebas RF-09 (CP-RF09-01 a CP-RF09-03)."""
from datetime import date, timedelta

from src.model.reservaciones.servicio import (
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservacion,
)
from src.model.salas.servicio import consultar_disponibilidad


def test_CP_RF09_01_cancela_reserva_activa_y_libera_horario(bd_p3, insertar_reserva):
    """Se cancela y persiste la reserva; el horario puede volver a reservarse."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '10:00', 1, 2)
    fecha = (date.today() + timedelta(days=2)).isoformat()

    respuesta = cancelar_reservacion(identificador)
    assert respuesta['exito'] is True, respuesta
    assert identificador in respuesta['mensaje'], respuesta

    fila = bd_p3.execute('SELECT estado FROM reservaciones WHERE id=?',
                         (int(identificador[1:]),)).fetchone()
    assert fila['estado'] == 'cancelada', fila
    historial = consultar_reservaciones()
    assert historial['exito'] is True, historial
    assert any(r['id'] == identificador and r['estado'] == 'cancelada'
               for r in historial['reservaciones']), historial

    nueva = crear_reservacion('B009876543', 'S01', fecha, '10:00', 1, 2)
    assert nueva['exito'] is True, (
        f'El horario de la reservación cancelada debe quedar disponible: {nueva}'
    )
    assert nueva['id'] != identificador


def test_CP_RF09_02_rechaza_cancelacion_repetida(bd_p3, insertar_reserva):
    """Cancelar dos veces no altera el registro tras el primer cambio."""
    identificador = insertar_reserva('A001234567', 'S01', 2, '11:00')
    primera = cancelar_reservacion(identificador)
    assert primera['exito'] is True, primera
    conteo_antes = bd_p3.execute('SELECT COUNT(*) FROM reservaciones').fetchone()[0]

    segunda = cancelar_reservacion(identificador)
    assert segunda['exito'] is False, segunda
    assert 'ya' in segunda['mensaje'].lower() and 'cancelada' in segunda['mensaje'].lower(), segunda
    fila = bd_p3.execute('SELECT estado FROM reservaciones WHERE id=?',
                         (int(identificador[1:]),)).fetchone()
    assert fila['estado'] == 'cancelada'
    assert bd_p3.execute('SELECT COUNT(*) FROM reservaciones').fetchone()[0] == conteo_antes


def test_CP_RF09_03_rechaza_id_inexistente(bd_p3):
    """Un ID con formato válido que no existe informa el error sin crear cambios."""
    antes = bd_p3.execute('SELECT COUNT(*) FROM reservaciones').fetchone()[0]
    respuesta = cancelar_reservacion('R9999')
    assert respuesta['exito'] is False, respuesta
    assert 'no existe' in respuesta['mensaje'].lower(), respuesta
    despues = bd_p3.execute('SELECT COUNT(*) FROM reservaciones').fetchone()[0]
    assert despues == antes
