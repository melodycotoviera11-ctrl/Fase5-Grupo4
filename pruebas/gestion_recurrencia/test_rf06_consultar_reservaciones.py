"""Fase 5, Persona 3: RF-06, CP-RF06-01 y CP-RF06-02."""
from src.model.reservaciones.servicio import consultar_reservaciones


def test_CP_RF06_01_historial_activo_cancelado_y_ordenado(bd_p3, insertar_reserva):
    """Debe consultar reservas activas/canceladas y ordenar por fecha y hora."""
    # Se insertan deliberadamente fuera de orden para comprobar el ORDER BY.
    id_tarde = insertar_reserva('A001234567', 'S01', 3, '16:00', 2, 2)
    id_cancelada = insertar_reserva('B009876543', 'S02', 1, '10:00', 1, 3, 'cancelada')
    id_temprano = insertar_reserva('A001234567', 'S03', 1, '08:00', 1, 1)

    respuesta = consultar_reservaciones()
    assert respuesta['exito'] is True, respuesta
    reservas = respuesta['reservaciones']
    assert len(reservas) == 3, reservas
    assert [r['id'] for r in reservas] == [id_temprano, id_cancelada, id_tarde]
    assert [r['estado'] for r in reservas] == ['activa', 'cancelada', 'activa']
    campos = {'id', 'carne', 'estudiante', 'sala', 'fecha', 'hora_inicio',
              'hora_fin', 'cantidad_personas', 'estado'}
    assert all(campos <= set(r) for r in reservas), reservas
    assert reservas[0]['hora_fin'] == '09:00'
    assert reservas[2]['hora_fin'] == '18:00'


def test_CP_RF06_02_consulta_sin_reservaciones(bd_p3):
    """Sin reservaciones debe informar el estado vacío, no fallar."""
    respuesta = consultar_reservaciones()
    assert respuesta['exito'] is True, respuesta
    assert respuesta['reservaciones'] == []
    assert 'no hay reservaciones' in respuesta['mensaje'].lower(), respuesta
