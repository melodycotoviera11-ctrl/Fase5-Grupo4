
"""Fase 7 - Integración de estudiantes y reservaciones."""

from datetime import date, timedelta

from src.db.conexion import obtener_conexion
from src.model.reservaciones.servicio import crear_reservacion


def test_integracion_estudiantes_reservaciones(bd_inicial):
    conexion = obtener_conexion()

    # Fecha futura para evitar reservar en el pasado.
    fecha = (date.today() + timedelta(days=14)).isoformat()

    # Verificar los estados iniciales de los estudiantes.
    estudiantes = conexion.execute(
        "SELECT carne, estado FROM estudiantes"
    ).fetchall()

    estados = {fila["carne"]: fila["estado"] for fila in estudiantes}

    assert estados["B009876543"] == "activo"
    assert estados["C004567890"] == "inactivo"

    # Carlos (activo) intenta reservar.
    resultado_carlos = crear_reservacion(
        carne="B009876543",
        codigo_sala="S01",
        fecha=fecha,
        hora_inicio="09:00",
        duracion=1,
        cantidad_personas=2
    )

    assert resultado_carlos["exito"] is True, resultado_carlos

    # Daniela (inactiva) intenta reservar.
    resultado_daniela = crear_reservacion(
        carne="C004567890",
        codigo_sala="S02",
        fecha=fecha,
        hora_inicio="11:00",
        duracion=1,
        cantidad_personas=2
    )

    assert resultado_daniela["exito"] is False, resultado_daniela

    # Solo debe existir la reservación válida de Carlos.
    reservaciones = conexion.execute(
        "SELECT COUNT(*) FROM reservaciones"
    ).fetchone()[0]

    assert reservaciones == 1

    print("\nINTEGRACIÓN FASE 7:")
    print("Carlos (activo): reservación permitida")
    print("Daniela (inactiva): reservación rechazada")
    print("Reservaciones almacenadas:", reservaciones)