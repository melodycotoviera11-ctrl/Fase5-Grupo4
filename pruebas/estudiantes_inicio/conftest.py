"""Infraestructura de la Fase 5 - Persona 1 (Grupo 4 evalúa al Grupo 6).

Las pruebas NO modifican el código productivo: importan el paquete `src`
del repositorio evaluado (ruta en la variable de entorno REPO_G6) y
trabajan siempre sobre bases de datos temporales (tmp_path).
"""
import csv
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import signal
from datetime import datetime
from datetime import timedelta, timezone
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover
    ZoneInfo = None
from pathlib import Path

import pytest

REPO = Path(os.environ.get("REPO_G6", "/home/claude/repo")).resolve()
EVID = Path(os.environ.get("EVID_DIR", Path(__file__).resolve().parent.parent / "evidencias"))
sys.path.insert(0, str(REPO))

from src.db.conexion import cerrar_conexion, configurar_ruta_base_datos, obtener_conexion  # noqa: E402
from src.db.inicializador import inicializar_base_datos  # noqa: E402
from src.model.estudiantes.servicio import (  # noqa: E402
    consultar_estudiantes,
    modificar_estudiante,
    registrar_estudiante,
)

ESTUDIANTES_INICIALES = [
    ("A001234567", "Andrea Solano", "andrea@universidad.ac.cr", "activo"),
    ("B009876543", "Carlos Méndez", "carlos@universidad.ac.cr", "activo"),
    ("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", "inactivo"),
]
_OBSERVADO = {}


def _fecha_d():
    """Fecha D en hora de Costa Rica (UTC-6, sin horario de verano)."""
    try:
        return datetime.now(ZoneInfo("America/Costa_Rica")).date().isoformat()
    except Exception:  # Windows sin el paquete tzdata
        return datetime.now(timezone(timedelta(hours=-6))).date().isoformat()


class Chequeos:
    """Acumula verificaciones para reportar TODOS los incumplimientos de un caso."""

    def __init__(self, cid):
        self.cid, self.fallas, self.notas = cid, [], []

    def ok(self, condicion, mensaje):
        if not condicion:
            self.fallas.append(mensaje)

    def obs(self, texto):
        self.notas.append(str(texto))

    def registrar(self):
        _OBSERVADO[self.cid] = " | ".join(self.notas + (["INCUMPLE: " + "; ".join(self.fallas)] if self.fallas else []))

    def cerrar(self):
        self.registrar()
        if self.fallas:
            raise AssertionError("; ".join(self.fallas))


@pytest.fixture
def chk(request):
    m = re.search(r"test_(CP_[A-Z0-9]+_\d+)", request.node.name)
    c = Chequeos(m.group(1).replace("CP_", "CP-").replace("_", "-") if m else request.node.name)
    yield c


@pytest.hookimpl(wrapper=True)
def pytest_runtest_call(item):
    """Evalúa los chequeos acumulados dentro de la fase de ejecución del caso."""
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


def _nueva_bd(tmp_path):
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / "prueba.db")
    r = inicializar_base_datos()
    assert r.exito, r.mensaje
    return r


@pytest.fixture
def bd_inicial(tmp_path):
    """Base temporal nueva, inicializada solo con la carga inicial de la aplicación."""
    _nueva_bd(tmp_path)
    yield
    cerrar_conexion()


@pytest.fixture
def ds01(tmp_path):
    """DS-01 (plan sección 7.2): salas iniciales + 3 estudiantes de la sección 10."""
    _nueva_bd(tmp_path)
    con = obtener_conexion()
    for carne, nombre, correo, _ in ESTUDIANTES_INICIALES:
        ok, msg = registrar_estudiante(carne, nombre, correo)
        if not ok:  # el plan permite inserción directa y anotarlo en la evidencia
            con.execute("INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?,?,?,?)",
                        (carne, nombre, correo, "activo"))
            con.commit()
    ok, msg = modificar_estudiante("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", "inactivo")
    assert ok, msg
    assert con.execute("SELECT COUNT(*) FROM salas").fetchone()[0] == 5
    assert con.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0] == 3
    assert con.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0] == 0
    yield
    cerrar_conexion()


def lista():
    ok, msg, datos = consultar_estudiantes()
    assert ok, msg
    return datos


def buscar(carne):
    return next((e for e in lista() if e["carne"] == carne), None)


def foto_tabla():
    return [tuple(r) for r in obtener_conexion().execute(
        "SELECT * FROM estudiantes ORDER BY id").fetchall()]


# ---------- modo arranque ----------
def clon_limpio(destino: Path) -> Path:
    """Copia del repositorio sin .git ni base de datos (equivale a DS-00)."""
    shutil.copytree(REPO, destino, ignore=shutil.ignore_patterns(".git", "*.db", "__pycache__", ".pytest_cache"))
    return destino


def ejecutar_app(carpeta: Path, segundos=6):
    """Ejecuta `python -m src.main`. Si sigue vivo tras `segundos`, la interfaz abrió
    (se cierra sola). En Linux usa Xvfb; en Windows abre la ventana real unos segundos.
    Devuelve (código, stdout, stderr, seguia_vivo)."""
    windows = platform.system() == "Windows"
    cmd = [sys.executable, "-m", "src.main"]
    if not windows:
        cmd = ["xvfb-run", "-a"] + cmd
    extra = {} if windows else {"start_new_session": True}
    p = subprocess.Popen(cmd, cwd=carpeta, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         encoding="utf-8", errors="replace", env={**os.environ, "PYTHONIOENCODING": "utf-8"}, **extra)
    try:
        out, err = p.communicate(timeout=segundos)
        return p.returncode, out, err, False
    except subprocess.TimeoutExpired:
        if windows:
            p.terminate()
        else:
            os.killpg(p.pid, signal.SIGTERM)
        out, err = p.communicate(timeout=10)
        return None, out, err, True


def contar_tablas(ruta_db: Path):
    con = sqlite3.connect(ruta_db)
    try:
        tablas = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
        return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tablas}
    finally:
        con.close()


def pytest_sessionstart(session):
    """Cada corrida empieza con un CSV nuevo (evita filas duplicadas)."""
    (EVID / "resultados_fase5_persona1.csv").unlink(missing_ok=True)


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
        fila = {"ID": cid, "Estado": estado, "Resultado obtenido": _OBSERVADO.get(cid, "").replace("\n", " ").replace("\r", " "),
                "Fecha D": _fecha_d()}
        EVID.mkdir(parents=True, exist_ok=True)
        ruta = EVID / "resultados_fase5_persona1.csv"
        nuevo = not ruta.exists()
        with open(ruta, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(fila), delimiter=";")
            if nuevo:
                w.writeheader()
            w.writerow(fila)
