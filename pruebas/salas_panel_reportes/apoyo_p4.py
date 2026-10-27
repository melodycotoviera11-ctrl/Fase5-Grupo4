"""Funciones de apoyo de la Persona 4 (nombre único para no chocar con otros bloques)."""
from datetime import date, timedelta

from src.db.conexion import obtener_conexion


def fecha_rel(dias):
    """Fecha relativa a hoy en formato AAAA-MM-DD."""
    return (date.today() + timedelta(days=dias)).isoformat()


def insertar_reserva(carne, sala, fecha, hora, duracion=1, personas=1, estado="activa", serie_id=None):
    """Inserción directa para preparar precondiciones (no pasa por reglas de negocio)."""
    con = obtener_conexion()
    cur = con.execute(
        """
        INSERT INTO reservaciones
            (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, cantidad_personas, estado, serie_id)
        VALUES ((SELECT id FROM estudiantes WHERE carne = ?),
                (SELECT id FROM salas WHERE codigo = ?), ?, ?, ?, ?, ?, ?)
        """,
        (carne, sala, fecha, hora, duracion, personas, estado, serie_id),
    )
    con.commit()
    return f"R{cur.lastrowid:04d}"


def foto(tabla):
    """Copia completa de una tabla para comparar antes/después."""
    return [tuple(r) for r in obtener_conexion().execute(f"SELECT * FROM {tabla} ORDER BY id").fetchall()]


def eventos_auditoria():
    return [dict(r) for r in obtener_conexion().execute(
        "SELECT id, fecha_hora, accion, entidad, entidad_id, detalle FROM auditoria ORDER BY id").fetchall()]
