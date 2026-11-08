"""Fase 7 - Persona 2: verificación de correcciones, rechazos e integración.

Bloque: reservaciones, creación y reglas. Se ejecuta sobre la versión
corregida del Grupo 6 (commit 92e1fd8), con una base SQLite temporal por
caso y sin modificar código productivo.

Casos:
- CP-F7P2-01: verificación de la corrección BUG-P1-DIS-01 (9:00 y 09:00).
- CP-F7P2-02: revisión del rechazo BUG-RES-01 (fecha inexistente).
- CP-F7P2-03: integración creación -> disponibilidad -> panel -> auditoría.
- CP-F7P2-04: creación con la hora sin cero inicial frente a una reservación
  existente (hallazgo nuevo de Fase 7, DEF-F7-P2-01).
"""
from conftest import (
    CARNE_ACTIVO,
    CARNE_ACTIVO_2,
    consultar_disponibilidad,
    crear_reservacion,
    crear_valida,
    fecha_futura,
    foto_reservaciones,
    obtener_conexion,
)
from src.model.auditoria.servicio import consultar_auditoria
from src.model.panel.servicio import consultar_panel


def _foto_auditoria():
    return [tuple(r) for r in obtener_conexion().execute(
        "SELECT id, accion, entidad, entidad_id, detalle FROM auditoria ORDER BY id"
    ).fetchall()]


def test_CP_F7P2_01_disponibilidad_9_y_09_coinciden(bd_p2, chk):
    """BUG-P1-DIS-01: 9:00 y 09:00 deben dar el mismo resultado."""
    fecha = fecha_futura(30)
    base = crear_valida(codigo_sala="S01", fecha=fecha, hora_inicio="09:00")
    chk.ok(base.get("exito") is True, f"no se pudo crear la reservación base de 09:00 a 10:00: {base}")
    antes = foto_reservaciones()

    ocupada_sin_cero = consultar_disponibilidad("S01", fecha, "9:00", 1)
    ocupada_con_cero = consultar_disponibilidad("S01", fecha, "09:00", 1)
    libre_sin_cero = consultar_disponibilidad("S01", fecha, "8:00", 1)
    libre_con_cero = consultar_disponibilidad("S01", fecha, "08:00", 1)
    chk.obs(f"9:00={ocupada_sin_cero}; 09:00={ocupada_con_cero}; 8:00={libre_sin_cero}; 08:00={libre_con_cero}")

    chk.ok(ocupada_sin_cero.get("disponible") is False, "9:00 se informó disponible pese al traslape con 09:00-10:00")
    chk.ok(ocupada_con_cero.get("disponible") is False, "09:00 se informó disponible pese al traslape")
    chk.ok(ocupada_sin_cero == ocupada_con_cero, "9:00 y 09:00 no producen la misma respuesta")
    chk.ok(libre_sin_cero.get("disponible") is True and libre_con_cero.get("disponible") is True,
           "la franja libre de 08:00 a 09:00 no se informó disponible")
    chk.ok(foto_reservaciones() == antes, "la consulta de disponibilidad modificó las reservaciones")


def test_CP_F7P2_02_fecha_inexistente_controlada(bd_p2, chk):
    """BUG-RES-01: 2026-02-30 (y una fecha futura inexistente) se rechazan sin excepción."""
    antes_res = foto_reservaciones()
    antes_aud = _foto_auditoria()
    respuestas = {}
    for fecha in ("2026-02-30", "2027-02-30"):
        try:
            respuestas[fecha] = crear_valida(fecha=fecha)
        except Exception as error:  # se registra en lugar de interrumpir el caso
            respuestas[fecha] = {"excepcion": f"{type(error).__name__}: {error}"}
    chk.obs(f"respuestas={respuestas}")

    for fecha, r in respuestas.items():
        chk.ok("excepcion" not in r, f"{fecha} lanzó una excepción: {r}")
        chk.ok(r.get("exito") is False, f"{fecha} no fue rechazada: {r}")
        chk.ok("fecha" in r.get("mensaje", "").lower(), f"{fecha}: el mensaje no menciona la fecha: {r}")
    chk.ok(foto_reservaciones() == antes_res, "se modificaron las reservaciones")
    chk.ok(_foto_auditoria() == antes_aud, "se registró un evento de auditoría para una solicitud rechazada")


def test_CP_F7P2_03_integracion_creacion_disponibilidad_panel_auditoria(bd_p2, chk):
    """Integración: una reservación válida se refleja en disponibilidad, panel y auditoría."""
    fecha = fecha_futura(30)
    previa = consultar_disponibilidad("S02", fecha, "14:00", 2)
    creada = crear_reservacion(CARNE_ACTIVO_2, "S02", fecha, "14:00", 2, 3)
    despues = consultar_disponibilidad("S02", fecha, "15:00", 1)
    panel = consultar_panel(fecha=fecha, codigo_sala="S02")
    auditoria = consultar_auditoria()
    rid = creada.get("id")
    en_panel = [r for r in panel.get("resultados", []) if r.get("id") == rid]
    eventos = [e for e in auditoria.get("eventos", []) if e.get("entidad_id") == rid]
    chk.obs(f"previa={previa}; creada={creada}; despues={despues}; panel={en_panel}; auditoria={eventos}")

    chk.ok(previa.get("disponible") is True, "la franja no estaba libre antes de reservar")
    chk.ok(creada.get("exito") is True, f"no se creó la reservación: {creada}")
    chk.ok(despues.get("disponible") is False, "la franja de 15:00 a 16:00 sigue disponible tras reservar 14:00-16:00")
    chk.ok(len(en_panel) == 1, "la reservación no aparece una vez en el panel filtrado por fecha y sala")
    if en_panel:
        r = en_panel[0]
        chk.ok((r["carne"], r["sala"], r["hora_inicio"], r["hora_fin"], r["cantidad_personas"], r["estado"])
               == (CARNE_ACTIVO_2, "S02", "14:00", "16:00", 3, "activa"),
               f"los datos del panel no coinciden con lo creado: {r}")
    chk.ok(any(e.get("accion") == "creacion" and e.get("entidad") == "reservacion" for e in eventos),
           "no hay evento de creación en la auditoría para la reservación")


def test_CP_F7P2_04_creacion_hora_sin_cero_respeta_superposicion(bd_p2, chk):
    """Hallazgo nuevo: crear con 9:00 no debe traslapar una reservación de 09:00."""
    fecha = fecha_futura(30)
    base = crear_reservacion(CARNE_ACTIVO, "S01", fecha, "09:00", 1, 2)
    disponibilidad = consultar_disponibilidad("S01", fecha, "9:00", 1)
    nueva = crear_reservacion(CARNE_ACTIVO_2, "S01", fecha, "9:00", 1, 2)
    filas = foto_reservaciones()
    chk.obs(f"base={base}; disponibilidad_9:00={disponibilidad}; nueva={nueva}; reservaciones={filas}")

    chk.ok(base.get("exito") is True, f"no se creó la reservación base: {base}")
    chk.ok(nueva.get("exito") is False, "se creó una segunda reservación en S01 de 9:00 a 10:00, traslapada con 09:00-10:00 (RN-09)")
    chk.ok(all(len(f[4]) == 5 for f in filas), "se guardó una hora de inicio sin normalizar a HH:MM")
