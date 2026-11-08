"""Fase 7 - Persona 4: verificación de correcciones, rechazo e integración.

Bloque: salas, panel, reportes y auditoría. Se ejecuta sobre la versión
corregida del Grupo 6 (commit 92e1fd8), con una base SQLite temporal por
caso y sin modificar código productivo.

Casos:
- CP-F7P4-01: corrección BUG-P1-SAL-01 (s01 con S01 existente).
- CP-F7P4-02: corrección BUG-P5-REP-01 (sin temporal residual si falla el CSV).
- CP-F7P4-03: rechazo BUG-PAN-01, capa de servicio (ocupación tras cancelar serie).
- CP-F7P4-04: rechazo BUG-PAN-01, ventana real del panel (Tkinter).
- CP-F7P4-05: OBS-F5-P4-01 (pantalla de gestión de salas en la interfaz).
- CP-F7P4-06: integración sala -> reservación -> CSV -> panel -> auditoría
  -> reinicio y persistencia.
- CP-F7P4-07: DEF-F5-P4-01, consistencia de un código en minúscula (s06)
  entre registro, reservación, disponibilidad y panel.
"""
import csv
import os
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

import src.model.panel.servicio as panel_servicio
import src.model.reportes.servicio as reportes_servicio
from src.controller.controller import ControladorAplicacion
from src.db.conexion import cerrar_conexion, obtener_ruta_base_datos
from src.db.inicializador import inicializar_base_datos
from src.model.auditoria.servicio import consultar_auditoria
from src.model.panel.servicio import consultar_panel
from src.model.reportes.servicio import generar_reporte_csv
from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    crear_reservacion,
    crear_reservaciones_recurrentes,
)
from src.model.salas.servicio import consultar_disponibilidad, consultar_salas, registrar_sala

from apoyo_p4 import eventos_auditoria, foto

D = date.today() + timedelta(days=30)
AHORA_D = datetime.combine(D, time(7, 0))


def _ocupacion(panel, codigo):
    return next((o for o in panel["ocupacion_salas"] if o["codigo"] == codigo), None)


def _residuos(carpeta):
    """Archivos temporales que deja _escribir_archivo_temporal (.<nombre>.*.tmp)."""
    return sorted(p.name for p in Path(carpeta).iterdir() if p.name.endswith(".tmp"))


# ---------------------------------------------------------------- correcciones
def test_CP_F7P4_01_codigo_en_minuscula_rechazado(bd_p4, chk):
    """BUG-P1-SAL-01: con S01 registrada, registrar s01 se rechaza sin insertar ni auditar."""
    salas_antes, aud_antes = foto("salas"), eventos_auditoria()
    r = registrar_sala("s01", "Sala duplicada en minúscula", 3)
    chk.obs(f"respuesta={r}; códigos={[s['codigo'] for s in consultar_salas()]}")
    chk.ok(r["exito"] is False, "se registró s01 aunque S01 ya existe")
    chk.ok(bool(str(r.get("mensaje", "")).strip()), "el rechazo no tiene mensaje")
    chk.ok(foto("salas") == salas_antes, "la tabla de salas cambió tras el rechazo")
    chk.ok(eventos_auditoria() == aud_antes, "se registró un evento de auditoría por el rechazo")


def test_CP_F7P4_02_fallo_de_escritura_sin_temporal_residual(bd_p4, chk, tmp_path, monkeypatch):
    """BUG-P5-REP-01: si falla la escritura del CSV no queda un .tmp y el CSV previo se conserva."""
    from apoyo_p4 import insertar_reserva

    insertar_reserva("A001234567", "S01", "2030-01-10", "10:00", personas=2)
    destino = tmp_path / "reporte.csv"
    previo = generar_reporte_csv("2030-01-01", "2030-01-31", destino)
    chk.ok(previo["exito"], f"no se pudo generar el CSV inicial: {previo}")
    bytes_previos = destino.read_bytes()

    def falla(*_a, **_k):
        raise OSError("fallo simulado de escritura")

    variantes = {
        "encabezados": (csv.DictWriter, "writeheader"),
        "filas": (csv.DictWriter, "writerows"),
        "reemplazo del destino": (reportes_servicio.os, "replace"),
    }
    for nombre, (objeto, atributo) in variantes.items():
        with monkeypatch.context() as m:
            m.setattr(objeto, atributo, falla)
            r = generar_reporte_csv("2030-01-01", "2030-01-31", destino)
        residuos = _residuos(tmp_path)
        chk.obs(f"falla en {nombre}: exito={r['exito']}, mensaje={r['mensaje']!r}, temporales={residuos}")
        chk.ok(r["exito"] is False and r["mensaje"], f"no se informó el error en {nombre}")
        chk.ok(residuos == [], f"quedó un archivo temporal tras fallar {nombre}")
        chk.ok(destino.read_bytes() == bytes_previos, f"el CSV anterior cambió tras fallar {nombre}")

    # Variante real, sin simulación: el destino es una carpeta.
    carpeta_destino = tmp_path / "destino_carpeta"
    carpeta_destino.mkdir()
    r = generar_reporte_csv("2030-01-01", "2030-01-31", carpeta_destino)
    chk.obs(f"destino carpeta: exito={r['exito']}; temporales={_residuos(tmp_path)}")
    chk.ok(r["exito"] is False and _residuos(tmp_path) == [], "quedó un temporal al escribir sobre una carpeta")


# ---------------------------------------------------------------- rechazo BUG-PAN-01
def _serie_en_d():
    serie = crear_reservaciones_recurrentes("A001234567", "S01", D.isoformat(), "10:00", 1, 2, 3)
    assert serie["exito"], serie
    return serie["ids"]


def test_CP_F7P4_03_panel_sin_ocupacion_tras_cancelar_serie(bd_p4, chk):
    """BUG-PAN-01 (servicio): tras cancelar la serie, S01 queda sin ocupación ni próximas."""
    ids = _serie_en_d()
    antes = consultar_panel(ahora=AHORA_D)
    occ_antes = _ocupacion(antes, "S01")
    chk.obs(f"serie={ids}; antes: ocupación S01={occ_antes}; próximas={[p['id'] for p in antes['proximas_reservaciones']]}")
    chk.ok(occ_antes and occ_antes["reservaciones_activas"] == 1, "antes de cancelar S01 no mostraba la ocurrencia del día")

    r = cancelar_ocurrencias_futuras(ids[0])
    chk.ok(r["exito"], f"no se pudo cancelar la serie: {r}")
    for consulta, panel in (("servicio", consultar_panel(ahora=AHORA_D)),
                            ("controlador", None)):
        if panel is None:
            # El controlador usa la hora real: se compara la serie en la tabla de resultados.
            panel = ControladorAplicacion().obtener_panel(codigo_sala="S01")
            estados = {x["id"]: x["estado"] for x in panel["resultados"]}
            chk.obs(f"controlador: estados={estados}; próximas={len(panel['proximas_reservaciones'])}")
            chk.ok(all(estados.get(i) == "cancelada" for i in ids), "el controlador no muestra la serie cancelada")
            chk.ok(panel["proximas_reservaciones"] == [], "el controlador sigue mostrando próximas")
            continue
        occ = _ocupacion(panel, "S01")
        chk.obs(f"{consulta}: ocupación S01={occ}; próximas={len(panel['proximas_reservaciones'])}")
        chk.ok(occ is not None, "S01 desapareció del catálogo de ocupación")
        chk.ok(occ and occ["reservaciones_activas"] == 0 and occ["personas_reservadas"] == 0,
               "S01 sigue mostrando ocupación tras cancelar la serie")
        chk.ok(panel["proximas_reservaciones"] == [], "siguen apareciendo próximas reservaciones")


def test_CP_F7P4_04_ventana_del_panel_tras_cancelar_serie(bd_p4, chk, monkeypatch):
    """BUG-PAN-01 (interfaz): la ventana real se actualiza al cancelar desde el panel."""
    tk = pytest.importorskip("tkinter")
    from tkinter import messagebox

    class RelojFijo(datetime):
        @classmethod
        def now(cls, tz=None):
            return AHORA_D

    # Solo se fija el reloj de la consulta del panel; el código productivo no cambia.
    monkeypatch.setattr(panel_servicio, "datetime", RelojFijo)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **k: True)
    monkeypatch.setattr(messagebox, "showinfo", lambda *a, **k: None)
    monkeypatch.setattr(messagebox, "showerror", lambda *a, **k: chk.ok(False, f"error en la ventana: {a}"))
    monkeypatch.setattr(messagebox, "showwarning", lambda *a, **k: chk.ok(False, f"aviso en la ventana: {a}"))

    ids = _serie_en_d()
    try:
        from src.view.app import Aplicacion
        app = Aplicacion()
    except tk.TclError as error:
        pytest.skip(f"No hay pantalla disponible para Tkinter: {error}")
    try:
        app.withdraw()
        panel = app.panel

        def ocupacion_s01():
            for item in panel.tabla_ocupacion.get_children():
                valores = panel.tabla_ocupacion.item(item, "values")
                if valores[0] == "S01":
                    return valores
            return None

        antes = (ocupacion_s01(), panel.total_proximas_var.get())
        fila = next(i for i in panel.tabla_resultados.get_children()
                    if panel.tabla_resultados.item(i, "values")[0] == ids[0])
        panel.tabla_resultados.selection_set(fila)
        panel._cancelar_futuras()  # mismo método que ejecuta el botón de la ventana
        despues = (ocupacion_s01(), panel.total_proximas_var.get())
        estados = [panel.tabla_resultados.item(i, "values")[6] for i in panel.tabla_resultados.get_children()]
        chk.obs(f"antes: ocupación S01={antes[0]}, próximas={antes[1]}; "
                f"después: ocupación S01={despues[0]}, próximas={despues[1]}, estados={estados}")
        chk.ok(antes[0] is not None and str(antes[0][3]) == "1" and antes[1] == "3",
               "antes de cancelar la ventana no mostraba la serie")
        chk.ok(despues[0] is not None and str(despues[0][3]) == "0" and str(despues[0][5]) == "0",
               "la ventana sigue mostrando ocupación en S01")
        chk.ok(despues[1] == "0", "la ventana sigue mostrando próximas reservaciones")
        chk.ok(estados and all(e == "cancelada" for e in estados), "la tabla de resultados no muestra la serie cancelada")
    finally:
        app.destroy()


# ---------------------------------------------------------------- observación
def test_CP_F7P4_05_interfaz_sin_gestion_de_salas(bd_p4, chk):
    """OBS-F5-P4-01: la interfaz debe ofrecer una vista para consultar y gestionar salas."""
    vista = Path(panel_servicio.__file__).resolve().parents[2] / "view"
    controlador = Path(panel_servicio.__file__).resolve().parents[2] / "controller" / "controller.py"
    texto_vista = " ".join(p.read_text(encoding="utf-8") for p in vista.glob("*.py"))
    metodos_ctl = [n for n in dir(ControladorAplicacion) if not n.startswith("_")]
    llamadas = [f for f in ("registrar_sala", "modificar_sala", "consultar_salas") if f in texto_vista
                or f in controlador.read_text(encoding="utf-8")]
    chk.obs(f"métodos del controlador={metodos_ctl}; funciones de salas usadas por vista/controlador={llamadas}; "
            f"archivos de vista={sorted(p.name for p in vista.glob('*.py'))}")
    chk.ok("registrar_sala" in llamadas and "modificar_sala" in llamadas,
           "la interfaz no permite registrar ni modificar salas (la observación persiste)")


# ---------------------------------------------------------------- integración
def test_CP_F7P4_06_integracion_sala_reserva_csv_panel_auditoria(bd_p4, chk, tmp_path):
    """Registrar sala -> reservar -> exportar CSV -> panel y auditoría -> reiniciar -> persistencia."""
    fecha = D.isoformat()
    sala = registrar_sala("S06", "Sala de integración", 6)
    chk.ok(sala["exito"], f"no se registró la sala S06: {sala}")
    reserva = crear_reservacion("B009876543", "S06", fecha, "14:00", 2, 5)
    chk.ok(reserva["exito"], f"no se creó la reservación en S06: {reserva}")
    rid = reserva.get("id")

    destino = tmp_path / "integracion.csv"
    rep = generar_reporte_csv(fecha, fecha, destino)
    with open(destino, encoding="utf-8", newline="") as f:
        filas_csv = list(csv.reader(f))
    panel = consultar_panel(fecha=fecha, codigo_sala="S06")
    en_panel = [(x["id"], x["sala"], x["fecha"], x["hora_inicio"], x["hora_fin"], x["cantidad_personas"], x["estado"])
                for x in panel["resultados"]]
    eventos = [(e["accion"], e["entidad"], e["entidad_id"]) for e in eventos_auditoria()]
    chk.obs(f"reserva={rid}; CSV={filas_csv}; panel={en_panel}; auditoría={eventos}")
    chk.ok(rep["exito"] and filas_csv[1:] == [["Carlos Méndez", "S06", fecha, "14:00-16:00", "5", "activa"]],
           "el CSV no contiene exactamente la reservación de S06")
    chk.ok(en_panel == [(rid, "S06", fecha, "14:00", "16:00", 5, "activa")], "el panel no coincide con el CSV")
    chk.ok(("creacion", "sala", "S06") in eventos and ("creacion", "reservacion", rid) in eventos,
           "la auditoría no registra la sala y la reservación")

    # Reinicio: se cierra la conexión y se vuelve a inicializar sobre el mismo archivo,
    # como hace la aplicación al abrirse de nuevo.
    antes = {t: foto(t) for t in ("estudiantes", "salas", "reservaciones", "auditoria")}
    cerrar_conexion()
    reinicio = inicializar_base_datos()
    despues = {t: foto(t) for t in ("estudiantes", "salas", "reservaciones", "auditoria")}
    rep2 = generar_reporte_csv(fecha, fecha, tmp_path / "integracion_2.csv")
    chk.obs(f"reinicio={reinicio.exito}; filas antes/después={ {t: (len(antes[t]), len(despues[t])) for t in antes} }")
    chk.ok(reinicio.exito, f"la reinicialización falló: {reinicio.mensaje}")
    chk.ok(despues == antes, "los datos cambiaron o se duplicaron al reiniciar")
    chk.ok(rep2["exito"] and (tmp_path / "integracion_2.csv").read_bytes() == destino.read_bytes(),
           "el CSV generado después del reinicio es distinto")
    chk.ok(any(e["entidad_id"] == rid for e in consultar_auditoria()["eventos"]),
           "la auditoría consultada tras el reinicio no muestra la reservación")
    assert os.path.exists(obtener_ruta_base_datos())


# ---------------------------------------------------------------- DEF-F5-P4-01
def test_CP_F7P4_07_codigo_en_minuscula_consistente_entre_modulos(bd_p4, chk):
    """DEF-F5-P4-01: una sala registrada como s06 debe tratarse igual en todos los módulos."""
    fecha = D.isoformat()
    alta = registrar_sala("s06", "Sala registrada en minúscula", 4)
    duplicado = registrar_sala("S06", "Sala en mayúscula", 4)
    reserva_mayus = crear_reservacion("A001234567", "S06", fecha, "10:00", 1, 2)
    reserva_minus = crear_reservacion("A001234567", "s06", fecha, "12:00", 1, 2)
    disp_mayus = consultar_disponibilidad("S06", fecha, "14:00", 1)
    panel = consultar_panel(codigo_sala="s06")
    chk.obs(f"registrar s06={alta}; registrar S06={duplicado}; reservar en S06={reserva_mayus}; "
            f"reservar en s06={reserva_minus}; disponibilidad S06={disp_mayus}; "
            f"panel filtros={panel['filtros']} resultados={[x['id'] for x in panel['resultados']]}")
    chk.ok(alta["exito"] and duplicado["exito"] is False,
           "no se reprodujo el escenario: s06 debía registrarse y S06 rechazarse como duplicado")
    chk.ok(reserva_mayus["exito"] is True,
           "S06 se rechaza como duplicado al registrar, pero al reservar se informa que la sala no existe")
    chk.ok(disp_mayus.get("motivo") != "La sala especificada no existe.",
           "la disponibilidad de S06 informa que la sala no existe")
    chk.ok(reserva_minus["exito"] is True and any(x["id"] == reserva_minus.get("id") for x in panel["resultados"]),
           "la reservación de s06 no aparece al filtrar el panel por esa sala")
