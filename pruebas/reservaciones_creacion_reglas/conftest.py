"""Infraestructura Fase 5 - Persona 2 (Grupo 4 evalúa al Grupo 6).

Bloque: reservaciones, creación y reglas (RF-05, RF-08, RN-01 a RN-11,
RNF-07 y RNF-10). Las pruebas no modifican código productivo y usan una
base SQLite temporal por caso.
"""
import csv
import os
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None
from pathlib import Path

import pytest

REPO = Path(os.environ.get("REPO_G6", "/home/claude/repo")).resolve()
EVID = Path(os.environ.get("EVID_DIR", Path(__file__).resolve().parent.parent / "evidencias"))
sys.path.insert(0, str(REPO))

from src.db.conexion import (  # noqa: E402
    cerrar_conexion,
    configurar_ruta_base_datos,
    obtener_conexion,
    obtener_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos  # noqa: E402
from src.model.reservaciones.servicio import (  # noqa: E402
    consultar_reservaciones,
    crear_reservacion,
    crear_reservaciones_recurrentes,
)
from src.model.salas.servicio import consultar_disponibilidad  # noqa: E402

CARNE_ACTIVO = "A001234567"
CARNE_ACTIVO_2 = "B009876543"
CARNE_INACTIVO = "C004567890"
_OBSERVADO = {}


def _fecha_d():
    try:
        return datetime.now(ZoneInfo("America/Costa_Rica")).date().isoformat()
    except Exception:
        return datetime.now(timezone(timedelta(hours=-6))).date().isoformat()


class Chequeos:
    def __init__(self, cid):
        self.cid, self.fallas, self.notas = cid, [], []

    def ok(self, condicion, mensaje):
        if not condicion:
            self.fallas.append(mensaje)

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
    c = Chequeos(cid)
    yield c


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


def fecha_futura(dias=30):
    return (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")


def _insertar_estudiantes_base(con):
    datos = [
        (CARNE_ACTIVO, "Andrea Solano", "andrea@universidad.ac.cr", "activo"),
        (CARNE_ACTIVO_2, "Carlos Méndez", "carlos@universidad.ac.cr", "activo"),
        (CARNE_INACTIVO, "Daniela Rojas", "daniela@universidad.ac.cr", "inactivo"),
    ]
    con.executemany(
        "INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?,?,?,?)",
        datos,
    )
    con.commit()


@pytest.fixture
def bd_p2(tmp_path):
    ruta_original = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "p2.db")
    resultado = inicializar_base_datos()
    assert resultado.exito, resultado.mensaje
    con = obtener_conexion()
    _insertar_estudiantes_base(con)
    yield con
    cerrar_conexion()
    configurar_ruta_base_datos(ruta_original)


def foto_reservaciones():
    con = obtener_conexion()
    return [tuple(r) for r in con.execute(
        "SELECT id, estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, cantidad_personas, estado, serie_id "
        "FROM reservaciones ORDER BY id"
    ).fetchall()]


def sala_id(codigo):
    fila = obtener_conexion().execute("SELECT id FROM salas WHERE codigo = ?", (codigo,)).fetchone()
    return fila["id"] if fila else None


def estudiante_id(carne):
    fila = obtener_conexion().execute("SELECT id FROM estudiantes WHERE UPPER(carne)=?", (carne.upper(),)).fetchone()
    return fila["id"] if fila else None


def insertar_reserva_directa(carne, sala, fecha, hora, duracion=1, personas=1, estado="activa", serie_id=None):
    con = obtener_conexion()
    cur = con.execute(
        """
        INSERT INTO reservaciones
        (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, cantidad_personas, estado, serie_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (estudiante_id(carne), sala_id(sala), fecha, hora, duracion, personas, estado, serie_id),
    )
    con.commit()
    return f"R{cur.lastrowid:04d}"


def crear_valida(**cambios):
    datos = {
        "carne": CARNE_ACTIVO,
        "codigo_sala": "S01",
        "fecha": fecha_futura(),
        "hora_inicio": "10:00",
        "duracion": 1,
        "cantidad_personas": 2,
    }
    datos.update(cambios)
    return crear_reservacion(**datos)


def pytest_sessionstart(session):
    (EVID / "resultados_fase5_persona2.csv").unlink(missing_ok=True)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    out = yield
    rep = out.get_result()
    if rep.when == "call" or (rep.when == "setup" and rep.failed):
        m = re.search(r"test_(CP_[A-Z0-9]+_\d+)", item.name)
        if not m:
            return
        cid = m.group(1).replace("CP_", "CP-").replace("_", "-")
        estado = "Aprobado" if rep.passed else ("Bloqueado" if rep.when == "setup" else "Fallido")
        fila = {
            "ID": cid,
            "Estado": estado,
            "Resultado obtenido": _OBSERVADO.get(cid, "").replace("\n", " ").replace("\r", " "),
            "Fecha D": _fecha_d(),
        }
        EVID.mkdir(parents=True, exist_ok=True)
        ruta = EVID / "resultados_fase5_persona2.csv"
        nuevo = not ruta.exists()
        with open(ruta, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(fila), delimiter=";")
            if nuevo:
                w.writeheader()
            w.writerow(fila)
