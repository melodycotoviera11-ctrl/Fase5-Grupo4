"""Infraestructura Fase 5 - Persona 4 (Grupo 4 evalúa al Grupo 6).

Bloque: salas, panel, reportes y auditoría (RF-04, RF-12, RF-15, RF-16,
RF-17, RNF-08 y RNF-09). Las pruebas no modifican el código productivo:
importan el paquete `src` del repositorio evaluado (variable REPO_G6) y
trabajan siempre sobre una base SQLite temporal por caso.
"""
import csv
import os
import re
import sys
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None
from pathlib import Path

import pytest

REPO = Path(os.environ.get("REPO_G6") or Path(__file__).resolve().parents[2] / "repo").resolve()
EVID = Path(os.environ.get("EVID_DIR", Path(__file__).resolve().parent.parent / "evidencias"))
if not (REPO / "src").is_dir():
    raise pytest.UsageError("Defina REPO_G6 con la ruta del repositorio del Grupo 6 (que contiene src/).")
sys.path.insert(0, str(REPO))

from src.db.conexion import (  # noqa: E402
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos  # noqa: E402

CSV_RESULTADOS = "resultados_fase5_persona4.csv"
ESTUDIANTES_INICIALES = [
    ("A001234567", "Andrea Solano", "andrea@universidad.ac.cr", "activo"),
    ("B009876543", "Carlos Méndez", "carlos@universidad.ac.cr", "activo"),
    ("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", "inactivo"),
]
_OBSERVADO = {}


def _fecha_d():
    """Fecha de ejecución en hora de Costa Rica (UTC-6)."""
    try:
        return datetime.now(ZoneInfo("America/Costa_Rica")).date().isoformat()
    except Exception:  # Windows sin tzdata
        return datetime.now(timezone(timedelta(hours=-6))).date().isoformat()


class Chequeos:
    """Acumula verificaciones para reportar TODOS los incumplimientos de un caso."""

    def __init__(self, cid):
        self.cid, self.fallas, self.notas = cid, [], []

    def ok(self, condicion, mensaje):
        if not condicion:
            self.fallas.append(mensaje)
        return condicion

    def obs(self, texto):
        self.notas.append(str(texto))

    def registrar(self):
        partes = self.notas + (["INCUMPLE: " + "; ".join(self.fallas)] if self.fallas else [])
        _OBSERVADO[self.cid] = " | ".join(partes)

    def cerrar(self):
        self.registrar()
        if self.fallas:
            raise AssertionError("; ".join(self.fallas))


@pytest.fixture
def chk(request):
    m = re.search(r"test_(CP_[A-Z0-9]+_\d+)", request.node.name)
    cid = m.group(1).replace("CP_", "CP-").replace("_", "-") if m else request.node.name
    yield Chequeos(cid)


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    c = item.funcargs.get("chk")
    try:
        resultado = yield
    except BaseException:
        if c:
            c.registrar()
        raise
    if c:
        c.cerrar()
    return resultado


# ---------------------------------------------------------------- datos
def _asegurar_estudiantes_base(con):
    """Deja en la base los 3 estudiantes de referencia, sin duplicarlos.

    Fase 7: desde el commit 92e1fd8 la inicialización del Grupo 6 ya carga
    estos mismos estudiantes (corrección de BUG-INI-01). Solo se insertan
    los que falten y luego se verifica que los tres existan con los datos
    y estados esperados. En la versión de Fase 5 (ee922b6) se insertan
    los tres, como antes.
    """
    existentes = {fila[0].upper() for fila in con.execute("SELECT carne FROM estudiantes")}
    faltantes = [e for e in ESTUDIANTES_INICIALES if e[0].upper() not in existentes]
    if faltantes:
        con.executemany(
            "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?,?,?,?)",
            faltantes,
        )
        con.commit()
    for carne, nombre, correo, estado in ESTUDIANTES_INICIALES:
        fila = con.execute(
            "SELECT nombre_completo, correo, estado FROM estudiantes WHERE UPPER(carne) = ?",
            (carne.upper(),),
        ).fetchone()
        assert fila is not None, f"Falta el estudiante base {carne}"
        assert tuple(fila) == (nombre, correo, estado), f"Datos distintos para {carne}: {tuple(fila)}"


@pytest.fixture
def bd_p4(tmp_path):
    """DS-01: salas iniciales del sistema + 3 estudiantes de la sección 10."""
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "p4.db")
    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje
    con = obtener_conexion()
    _asegurar_estudiantes_base(con)
    yield con
    cerrar_conexion()
    configurar_ruta_base_datos(ruta_original)


# ---------------------------------------------------------------- evidencias
def pytest_sessionstart(session):
    """Cada corrida empieza con un CSV nuevo (evita filas duplicadas)."""
    (EVID / CSV_RESULTADOS).unlink(missing_ok=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    out = yield
    rep = out.get_result()
    if rep.when == "call" or (rep.when == "setup" and (rep.failed or rep.skipped)):
        m = re.search(r"test_(CP_[A-Z0-9]+_\d+)", item.name)
        if not m:
            return
        cid = m.group(1).replace("CP_", "CP-").replace("_", "-")
        if rep.passed:
            estado = "Aprobado"
        elif rep.skipped:
            estado = "Omitido"  # p. ej., sin pantalla para la prueba de interfaz
        else:
            estado = "Bloqueado" if rep.when == "setup" else "Fallido"
        fila = {
            "ID": cid,
            "Estado": estado,
            "Resultado obtenido": _OBSERVADO.get(cid, "").replace("\n", " ").replace("\r", " "),
            "Fecha D": _fecha_d(),
        }
        EVID.mkdir(parents=True, exist_ok=True)
        ruta = EVID / CSV_RESULTADOS
        nuevo = not ruta.exists()
        with open(ruta, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(fila), delimiter=";")
            if nuevo:
                w.writeheader()
            w.writerow(fila)
