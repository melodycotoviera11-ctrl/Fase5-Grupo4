"""Fase 5, Persona 4: RNF-08 Codificación (tildes y ñ en la base de datos y en el CSV)."""
import csv
import sqlite3

from src.db.conexion import cerrar_conexion, obtener_ruta_base_datos
from src.model.estudiantes.servicio import consultar_estudiantes, registrar_estudiante
from src.model.reportes.servicio import generar_reporte_csv
from src.model.salas.servicio import consultar_salas, registrar_sala

from apoyo_p4 import insertar_reserva

NOMBRE = "José Ñúñez Peña"
SALA = "Sala Óptica Ñandú"


def test_CP_RNF08_01_base_de_datos_conserva_tildes_y_enie(bd_p4, chk):
    """Los textos con tildes y ñ se recuperan idénticos, incluso tras reabrir la base."""
    ok, msg = registrar_estudiante("D001234567", NOMBRE, "jose.nunez@universidad.ac.cr")
    r = registrar_sala("S06", SALA, 4)
    chk.ok(ok and r["exito"], f"no se pudieron registrar los datos: {msg} / {r}")
    ruta = obtener_ruta_base_datos()
    cerrar_conexion()  # se reabre la base como en un reinicio
    nombre_app = next((e["nombre_completo"] for e in consultar_estudiantes()[2] if e["carne"] == "D001234567"), None)
    sala_app = next((s["nombre"] for s in consultar_salas() if s["codigo"] == "S06"), None)
    con = sqlite3.connect(ruta)
    crudo = con.execute("SELECT nombre_completo FROM estudiantes WHERE carne='D001234567'").fetchone()
    con.close()
    chk.obs(f"estudiante={nombre_app!r}; sala={sala_app!r}; lectura directa SQLite={crudo}")
    chk.ok(nombre_app == NOMBRE and crudo == (NOMBRE,), "el nombre del estudiante no se conservó")
    chk.ok(sala_app == SALA, "el nombre de la sala no se conservó")
    chk.ok(any(s["nombre"] == "Cubículo individual" for s in consultar_salas()), "la tilde del dato inicial se perdió")


def test_CP_RNF08_02_csv_utf8_conserva_tildes_y_enie(bd_p4, chk, tmp_path):
    """El CSV exportado está en UTF-8 válido y conserva tildes y ñ."""
    registrar_estudiante("D001234567", NOMBRE, "jose.nunez@universidad.ac.cr")
    insertar_reserva("D001234567", "S05", "2030-03-01", "09:00")
    insertar_reserva("B009876543", "S01", "2030-03-02", "09:00")
    destino = tmp_path / "reporte_tildes.csv"
    r = generar_reporte_csv("2030-03-01", "2030-03-31", destino)
    crudo = destino.read_bytes() if destino.exists() else b""
    try:
        texto = crudo.decode("utf-8")
        decodifica = True
    except UnicodeDecodeError:
        texto, decodifica = "", False
    filas = list(csv.reader(texto.splitlines()))
    chk.obs(f"respuesta={r['mensaje']!r}; bytes={len(crudo)}; filas={filas}")
    chk.ok(r["exito"] and decodifica, "el archivo no es UTF-8 válido")
    chk.ok(NOMBRE.encode("utf-8") in crudo and "Carlos Méndez".encode("utf-8") in crudo,
           "los nombres con tildes y ñ no se exportaron en UTF-8")
    chk.ok(any(f and f[0] == NOMBRE for f in filas), "el nombre con ñ no aparece intacto en el CSV")
