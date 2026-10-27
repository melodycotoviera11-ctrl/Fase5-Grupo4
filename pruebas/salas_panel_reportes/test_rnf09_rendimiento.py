"""Fase 5, Persona 4: RNF-09 Rendimiento (1 000 estudiantes y 5 000 reservaciones, < 2 s por consulta)."""
import random
import time
from datetime import date, timedelta

from src.db.conexion import obtener_conexion
from src.model.auditoria.servicio import consultar_auditoria
from src.model.estudiantes.servicio import buscar_reservaciones_estudiante, consultar_estudiantes
from src.model.panel.servicio import consultar_panel
from src.model.reportes.servicio import generar_reporte_csv
from src.model.reservaciones.servicio import consultar_reservaciones
from src.model.salas.servicio import consultar_disponibilidad, consultar_salas

LIMITE_S = 2.0


def _cargar_volumen(con):
    """DS-P4-VOL: 1 000 estudiantes, 5 000 reservaciones y 5 000 eventos de auditoría."""
    random.seed(2026)
    est = [(f"P{i:09d}", f"Estudiante Prueba {i:04d}", f"e{i}@universidad.ac.cr", "activo") for i in range(1000)]
    con.executemany("INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?,?,?,?)", est)
    ids_est = [r[0] for r in con.execute("SELECT id FROM estudiantes")]
    salas = {r[0]: r[1] for r in con.execute("SELECT id, capacidad FROM salas")}
    base = date.today() - timedelta(days=60)
    filas = []
    for _ in range(5000):
        sid = random.choice(list(salas))
        filas.append((random.choice(ids_est), sid, (base + timedelta(days=random.randint(0, 180))).isoformat(),
                      f"{random.randint(8, 18):02d}:00", random.choice((1, 2)), random.randint(1, salas[sid]),
                      random.choice(("activa", "activa", "activa", "cancelada"))))
    con.executemany("INSERT INTO reservaciones (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, "
                    "cantidad_personas, estado) VALUES (?,?,?,?,?,?,?)", filas)
    con.executemany("INSERT INTO auditoria (fecha_hora, accion, entidad, entidad_id, detalle) VALUES (?,?,?,?,?)",
                    [(f"2026-10-01 10:{i // 60 % 60:02d}:{i % 60:02d}", "creacion", "reservacion", f"R{i + 1:04d}", "")
                     for i in range(5000)])
    con.commit()


def test_CP_RNF09_01_consultas_bajo_dos_segundos(bd_p4, chk, tmp_path):
    """Cada consulta responde en menos de 2 s con el volumen mínimo del requisito."""
    con = bd_p4
    _cargar_volumen(con)
    n_est = con.execute("SELECT COUNT(*) FROM estudiantes").fetchone()[0]
    n_res = con.execute("SELECT COUNT(*) FROM reservaciones").fetchone()[0]
    chk.ok(n_est >= 1000 and n_res >= 5000, f"el volumen cargado no cumple el mínimo: {n_est}/{n_res}")
    hoy = date.today().isoformat()
    consultas = {
        "RF-03 consultar_estudiantes": lambda: consultar_estudiantes(),
        "RF-04 consultar_salas": lambda: consultar_salas(),
        "RF-06 consultar_reservaciones": lambda: consultar_reservaciones(),
        "RF-07 buscar_reservaciones_estudiante": lambda: buscar_reservaciones_estudiante("P000000500"),
        "RF-08 consultar_disponibilidad": lambda: consultar_disponibilidad(
            "S03", (date.today() + timedelta(days=20)).isoformat(), "10:00", 2),
        "RF-15 panel sin filtros": lambda: consultar_panel(),
        "RF-15 panel con filtros": lambda: consultar_panel(fecha=hoy, codigo_sala="S01", estado="activa"),
        "RF-16 reporte CSV 6 meses": lambda: generar_reporte_csv(
            (date.today() - timedelta(days=60)).isoformat(),
            (date.today() + timedelta(days=120)).isoformat(), tmp_path / "volumen.csv"),
        "RF-17 consultar_auditoria": lambda: consultar_auditoria(),
    }
    tiempos = {}
    for nombre, funcion in consultas.items():
        t0 = time.perf_counter()
        funcion()
        tiempos[nombre] = round(time.perf_counter() - t0, 4)
        chk.ok(tiempos[nombre] < LIMITE_S, f"{nombre} tardó {tiempos[nombre]} s")
    chk.obs(f"volumen: {n_est} estudiantes, {n_res} reservaciones; tiempos (s)={tiempos}")
    obtener_conexion()  # la conexión sigue disponible tras la carga
