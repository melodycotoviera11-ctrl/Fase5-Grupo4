"""Fase 5, Persona 3: RF-07, CP-RF07-01 a CP-RF07-04."""

from src.model.estudiantes.servicio import buscar_reservaciones_estudiante


def test_CP_RF07_01_busca_reservaciones_por_carne(bd_p3, insertar_reserva):
    """Muestra reservas activas y canceladas del estudiante indicado, ordenadas."""
    id_futura = insertar_reserva('A001234567', 'S01', 5, '10:00', 1, 2)
    id_cancelada = insertar_reserva('A001234567', 'S02', 2, '09:00', 1, 3, 'cancelada')
    insertar_reserva('B009876543', 'S03', 1, '08:00', 1, 1)

    exito, mensaje, reservas = buscar_reservaciones_estudiante('A001234567')

    assert exito is True, mensaje
    assert len(reservas) == 2, reservas
    assert [r['id'] for r in reservas] == [int(id_cancelada[1:]), int(id_futura[1:])], reservas
    assert [r['estado'] for r in reservas] == ['cancelada', 'activa'], reservas
    assert all(r['sala'] in ('S01', 'S02') for r in reservas), reservas


def test_CP_RF07_02_estudiante_sin_reservaciones(bd_p3):
    """Un estudiante existente sin reservas obtiene mensaje informativo."""
    exito, mensaje, reservas = buscar_reservaciones_estudiante('A001234567')

    assert exito is True, mensaje
    assert reservas == [], reservas
    assert 'no tiene reservaciones' in mensaje.lower(), mensaje


def test_CP_RF07_03_busqueda_ignora_mayusculas_minusculas(bd_p3, insertar_reserva):
    """Buscar con carné minúsculo devuelve las mismas reservas."""
    insertar_reserva('A001234567', 'S01', 1, '10:00', 1, 2)

    superior = buscar_reservaciones_estudiante('A001234567')
    inferior = buscar_reservaciones_estudiante('a001234567')

    assert superior[0] is True and inferior[0] is True
    assert superior[2] == inferior[2], (superior, inferior)
    assert len(inferior[2]) == 1


def test_CP_RF07_04_carne_inexistente(bd_p3):
    """Distingue un carné inexistente de uno sin reservas."""
    exito, mensaje, reservas = buscar_reservaciones_estudiante('Z999999999')

    assert exito is False
    assert reservas == [], reservas
    assert 'no existe' in mensaje.lower(), mensaje
