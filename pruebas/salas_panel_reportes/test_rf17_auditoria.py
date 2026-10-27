"""Fase 5, Persona 4: RF-17 Registrar auditoría."""
import inspect
import re
from datetime import datetime
from pathlib import Path

import src.model.auditoria.servicio as servicio_auditoria
from src.controller.controller import ControladorAplicacion
from src.model.auditoria.servicio import consultar_auditoria
from src.model.estudiantes.servicio import modificar_estudiante, registrar_estudiante
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
    crear_reservacion,
    crear_reservaciones_recurrentes,
    modificar_reservacion,
)
from src.model.salas.servicio import modificar_sala, registrar_sala

from apoyo_p4 import eventos_auditoria, fecha_rel, insertar_reserva


def _campos_completos(ev):
    try:
        datetime.strptime(ev["fecha_hora"], "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return False
    return all(str(ev[c] or "").strip() for c in ("accion", "entidad", "entidad_id"))


def test_CP_RF17_01_creacion_registra_evento_completo(bd_p4, chk):
    """Crear una reservación registra fecha y hora, acción, entidad e identificador."""
    inicio = datetime.now().replace(microsecond=0)
    r = crear_reservacion("A001234567", "S01", fecha_rel(2), "10:00", 1, 2)
    ev = eventos_auditoria()
    chk.obs(f"reserva={r.get('id')}; eventos={ev}")
    chk.ok(r["exito"] and len(ev) == 1, "no se registró exactamente un evento por la creación")
    if ev:
        e = ev[0]
        chk.ok(_campos_completos(e), "el evento no tiene fecha y hora válidas, acción, entidad e identificador")
        chk.ok(e["entidad_id"] == r.get("id") and e["entidad"] == "reservacion", "el identificador o la entidad no coinciden")
        chk.ok(datetime.strptime(e["fecha_hora"], "%Y-%m-%d %H:%M:%S") >= inicio, "la fecha y hora no corresponde a la operación")


def test_CP_RF17_02_modificacion_y_cancelacion_registran(bd_p4, chk):
    """Modificar y cancelar una reservación registran su propio evento."""
    rid = crear_reservacion("A001234567", "S01", fecha_rel(2), "10:00", 1, 2)["id"]
    modificar_reservacion(rid, hora_inicio="12:00")
    cancelar_reservacion(rid)
    acciones = [(e["accion"], e["entidad"], e["entidad_id"]) for e in eventos_auditoria()]
    chk.obs(f"eventos={acciones}")
    chk.ok([a[0] for a in acciones] == ["creacion", "modificacion", "cancelacion"],
           "no se registraron creación, modificación y cancelación en orden")
    chk.ok(all(a[2] == rid for a in acciones), "algún evento no identifica la reservación afectada")


def test_CP_RF17_03_estudiantes_y_salas_registran(bd_p4, chk):
    """Las operaciones de estudiantes y salas también quedan auditadas."""
    registrar_estudiante("D001112223", "Elena Vargas", "elena@universidad.ac.cr")
    modificar_estudiante("D001112223", "Elena Vargas", "elena@universidad.ac.cr", "inactivo")
    registrar_sala("S06", "Sala nueva", 4)
    modificar_sala("S06", "Sala nueva", 5, "fuera_de_servicio")
    ev = [(e["accion"], e["entidad"], e["entidad_id"]) for e in eventos_auditoria()]
    chk.obs(f"eventos={ev}")
    esperado = [("creacion", "estudiante", "D001112223"), ("modificacion", "estudiante", "D001112223"),
                ("creacion", "sala", "S06"), ("modificacion", "sala", "S06")]
    chk.ok(ev == esperado, "faltan eventos o no identifican la entidad afectada")
    chk.ok(all(_campos_completos(e) for e in eventos_auditoria()), "hay eventos con campos incompletos")


def test_CP_RF17_04_errores_de_validacion_no_se_registran(bd_p4, chk):
    """Un error de validación no se registra como cambio exitoso."""
    rid = insertar_reserva("A001234567", "S03", fecha_rel(4), "10:00", personas=6)
    cancelada = insertar_reserva("B009876543", "S02", fecha_rel(4), "10:00", estado="cancelada")
    intentos = {
        "reserva estudiante inactivo": crear_reservacion("C004567890", "S01", fecha_rel(2), "10:00", 1, 1),
        "reserva sala fuera de servicio": crear_reservacion("A001234567", "S04", fecha_rel(2), "10:00", 1, 1),
        "reserva fecha pasada": crear_reservacion("A001234567", "S01", fecha_rel(-1), "10:00", 1, 1),
        "modificar excediendo capacidad": modificar_reservacion(rid, cantidad_personas=20),
        "cancelar inexistente": cancelar_reservacion("R9999"),
        "cancelar ya cancelada": cancelar_reservacion(cancelada),
        "sala duplicada": registrar_sala("S01", "Duplicada", 3),
        "reducir capacidad": modificar_sala("S03", "Laboratorio de estudio", 2, "disponible"),
        "estudiante inválido": registrar_estudiante("X1", "Al", "sin-arroba"),
    }
    for nombre, r in intentos.items():
        exito = r[0] if isinstance(r, tuple) else r["exito"]
        chk.ok(exito is False, f"la operación inválida '{nombre}' fue aceptada")
    ev = eventos_auditoria()
    chk.obs(f"{len(intentos)} intentos inválidos; eventos registrados={ev}")
    chk.ok(ev == [], "se registraron eventos por operaciones rechazadas")


def test_CP_RF17_05_consulta_ordenada_y_estado_vacio(bd_p4, chk):
    """La consulta devuelve primero lo más reciente e informa cuando no hay eventos."""
    vacio = consultar_auditoria()
    chk.ok(vacio["exito"] and vacio["eventos"] == [] and "no hay" in vacio["mensaje"].lower(),
           "la auditoría vacía no muestra un mensaje informativo")
    a = crear_reservacion("A001234567", "S01", fecha_rel(2), "10:00", 1, 2)["id"]
    b = crear_reservacion("B009876543", "S02", fecha_rel(2), "10:00", 1, 2)["id"]
    cancelar_reservacion(a)
    lleno = ControladorAplicacion().obtener_auditoria()
    orden = [(e["accion"], e["entidad_id"]) for e in lleno["eventos"]]
    chk.obs(f"vacía={vacio['mensaje']!r}; orden={orden}")
    chk.ok(orden == [("cancelacion", a), ("creacion", b), ("creacion", a)], "los eventos no van del más reciente al más antiguo")


def test_CP_RF17_06_historial_no_editable_desde_interfaz(bd_p4, chk):
    """La interfaz y el controlador solo exponen consulta; no hay forma de editar el historial."""
    publicas_servicio = sorted(n for n, o in inspect.getmembers(servicio_auditoria, inspect.isfunction)
                               if o.__module__ == servicio_auditoria.__name__ and not n.startswith("_"))
    metodos_ctl = [n for n in dir(ControladorAplicacion) if "auditoria" in n.lower()]
    # Se lee el archivo como texto para no depender de abrir una ventana Tk.
    ruta_dialogo = Path(servicio_auditoria.__file__).resolve().parents[2] / "view" / "dialogo_auditoria.py"
    fuente_dialogo = ruta_dialogo.read_text(encoding="utf-8")
    editores = [w for w in ("ttk.Entry", "tk.Entry", "Text(", "UPDATE", "DELETE", "eliminar", "editar")
                if w in fuente_dialogo]
    chk.obs(f"funciones públicas servicio={publicas_servicio}; controlador={metodos_ctl}; "
            f"controles de edición en el diálogo={editores}")
    chk.ok(set(publicas_servicio) <= {"registrar_evento", "consultar_auditoria"},
           "el servicio expone operaciones de edición o borrado")
    chk.ok(metodos_ctl == ["obtener_auditoria"], "el controlador expone más que la consulta de auditoría")
    chk.ok(editores == [], "el diálogo de auditoría contiene controles o sentencias de edición")


def test_CP_RF17_07_series_registran_ids_afectados(bd_p4, chk):
    """En una serie recurrente, el evento debe permitir identificar cada reservación afectada."""
    serie = crear_reservaciones_recurrentes("A001234567", "S01", fecha_rel(2), "10:00", 1, 2, 3)
    chk.ok(serie["exito"], f"no se pudo crear la serie: {serie.get('mensaje')}")
    ids = serie.get("ids", [])
    cancelar_ocurrencias_futuras(ids[1]) if len(ids) > 1 else None
    ev = eventos_auditoria()
    texto = " ".join(f"{e['entidad_id']} {e['detalle'] or ''}" for e in ev)
    citados = set(re.findall(r"\bR\d{4}\b", texto))  # evita confundir R0001 con SR0001
    faltan = [i for i in ids if i not in citados]
    chk.obs(f"ids creados={ids}; eventos={[(e['accion'], e['entidad'], e['entidad_id'], e['detalle']) for e in ev]}")
    chk.ok(not faltan, f"la auditoría no identifica las reservaciones {faltan} creadas o canceladas en la serie")
