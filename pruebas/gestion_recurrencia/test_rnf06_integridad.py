"""RNF-06: cambios rechazados no deben afectar la integridad de SQLite."""
from datetime import date, timedelta
from src.model.reservaciones.servicio import (
    crear_reservaciones_recurrentes, modificar_reservacion,
)


def _instantanea(con):
    # Comparación exacta de datos productivos (reservaciones y auditoría).
    return {
        tabla: [tuple(fila) for fila in con.execute(f'SELECT * FROM {tabla} ORDER BY id')]
        for tabla in ('reservaciones', 'auditoria')
    }


def test_CP_RNF06_01_modificacion_rechazada_conserva_originales(bd_p3, insertar_reserva):
    identificador = insertar_reserva('A001234567', 'S01', 5, '10:00', 1, 2)
    insertar_reserva('B009876543', 'S01', 5, '12:00', 1, 2)
    antes = _instantanea(bd_p3)
    respuesta = modificar_reservacion(identificador, hora_inicio='12:00')
    assert respuesta['exito'] is False, respuesta
    assert _instantanea(bd_p3) == antes


def test_CP_RNF06_02_recurrencia_rechazada_no_deja_parciales(bd_p3, insertar_reserva):
    # Semana 2 tiene un conflicto, semanas 1 y 3 quedarían libres.
    dia = date.today() + timedelta(days=14)
    fecha_conflicto = (dia + timedelta(days=7)).isoformat()
    insertar_reserva('B009876543', 'S01', 21, '10:00', 1, 2)
    antes = _instantanea(bd_p3)
    respuesta = crear_reservaciones_recurrentes(
        'A001234567', 'S01', dia.isoformat(), '10:00', 1, 2, 3,
    )
    assert respuesta['exito'] is False, respuesta
    assert _instantanea(bd_p3) == antes
