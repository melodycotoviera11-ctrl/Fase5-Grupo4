"""RF-01 Cargar datos (CP-RF01-01 a CP-RF01-04)."""
from conftest import ESTUDIANTES_INICIALES, clon_limpio, contar_tablas, ejecutar_app, lista, obtener_conexion

TABLAS = {"estudiantes", "salas", "reservaciones", "auditoria"}
SALAS = [("S01", "Sala Biblioteca 1", 4, "disponible"), ("S02", "Sala Biblioteca 2", 6, "disponible"),
         ("S03", "Laboratorio de estudio", 10, "disponible"), ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
         ("S05", "Cubículo individual", 1, "disponible")]


def test_CP_RF01_01_crea_bd_primera_ejecucion(tmp_path, chk):
    carpeta = clon_limpio(tmp_path / "clon")
    codigo, out, err, vivo = ejecutar_app(carpeta)
    dbs = list(carpeta.rglob("*.db"))
    chk.obs(f"proceso {'sigue en ejecución (interfaz abierta)' if vivo else 'terminó con código ' + str(codigo)}; "
            f"archivos .db: {[str(d.relative_to(carpeta)) for d in dbs]}; stdout={out.strip()!r}; stderr={err.strip()[:200]!r}")
    chk.ok("Traceback" not in err, "la aplicación mostró una traza técnica")
    chk.ok(vivo, f"la aplicación no se mantuvo abierta (código de salida {codigo})")
    chk.ok(len(dbs) == 1, "no se creó exactamente un archivo de base de datos")
    if dbs:
        c = contar_tablas(dbs[0])
        chk.obs(f"tablas y registros: {c}")
        chk.ok(TABLAS <= set(c), f"faltan tablas: {TABLAS - set(c)}")
        chk.ok(c.get("salas") == 5, "las salas iniciales no quedaron cargadas")


def test_CP_RF01_02_no_duplica_registros(tmp_path, chk):
    carpeta = clon_limpio(tmp_path / "clon")
    ejecutar_app(carpeta)
    db = next(carpeta.rglob("*.db"))
    antes = contar_tablas(db)
    for _ in range(2):
        codigo, out, err, vivo = ejecutar_app(carpeta)
        chk.ok("Traceback" not in err, "traza técnica en una ejecución posterior")
    despues = contar_tablas(db)
    chk.obs(f"antes={antes}; después={despues}")
    chk.ok(antes == despues, "las cantidades de registros cambiaron tras ejecutar de nuevo")


def test_CP_RF01_03_carga_3_estudiantes_iniciales(bd_inicial, chk):
    datos = lista()
    obtenido = [(e["carne"], e["nombre_completo"], e["correo"], e["estado"]) for e in datos]
    chk.obs(f"estudiantes cargados por la inicialización: {len(obtenido)} -> {obtenido}")
    chk.ok(sorted(obtenido) == sorted(ESTUDIANTES_INICIALES),
           "la carga inicial no contiene los 3 estudiantes de la sección 10 del enunciado (H-02)")


def test_CP_RF01_04_carga_5_salas_iniciales(bd_inicial, chk):
    filas = [tuple(r) for r in obtener_conexion().execute(
        "SELECT codigo, nombre, capacidad, estado FROM salas ORDER BY codigo")]
    chk.obs(f"salas: {filas}")
    chk.ok(filas == SALAS, "las salas iniciales no coinciden con la sección 5.2")
