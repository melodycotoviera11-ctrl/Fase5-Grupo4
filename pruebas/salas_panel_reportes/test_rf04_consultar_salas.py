"""Fase 5, Persona 4: RF-04 Consultar salas."""
from src.db.conexion import obtener_conexion
from src.model.salas.servicio import consultar_salas, registrar_sala

SALAS_ENUNCIADO = [
    ("S01", "Sala Biblioteca 1", 4, "disponible"),
    ("S02", "Sala Biblioteca 2", 6, "disponible"),
    ("S03", "Laboratorio de estudio", 10, "disponible"),
    ("S04", "Sala multimedia", 8, "fuera_de_servicio"),
    ("S05", "Cubículo individual", 1, "disponible"),
]


def test_CP_RF04_01_muestra_campos_y_salas_iniciales(bd_p4, chk):
    """Debe mostrar código, nombre, capacidad y estado de las 5 salas iniciales."""
    salas = consultar_salas()
    chk.obs(f"salas={[(s.get('codigo'), s.get('nombre'), s.get('capacidad'), s.get('estado')) for s in salas]}")
    chk.ok(len(salas) == 5, f"se esperaban 5 salas y se obtuvieron {len(salas)}")
    chk.ok(all({"codigo", "nombre", "capacidad", "estado"} <= set(s) for s in salas),
           "alguna sala no incluye código, nombre, capacidad y estado")
    obtenidas = [(s["codigo"], s["nombre"], s["capacidad"], s["estado"]) for s in salas]
    chk.ok(obtenidas == SALAS_ENUNCIADO, "los datos no coinciden con la sección 5.2 del enunciado")


def test_CP_RF04_02_orden_por_codigo_e_incluye_fuera_de_servicio(bd_p4, chk):
    """Las salas se ordenan por código e incluyen las fuera de servicio."""
    # Se registran salas nuevas fuera de orden para verificar el ORDER BY.
    r1 = registrar_sala("S09", "Sala de prueba nueve", 3)
    r2 = registrar_sala("S06", "Sala de prueba seis", 2, "fuera_de_servicio")
    chk.ok(r1["exito"] and r2["exito"], f"no se pudieron preparar las salas: {r1} {r2}")
    codigos = [s["codigo"] for s in consultar_salas()]
    estados = {s["codigo"]: s["estado"] for s in consultar_salas()}
    chk.obs(f"orden={codigos}; estados={estados}")
    chk.ok(codigos == sorted(codigos), "las salas no están ordenadas por código")
    chk.ok(estados.get("S04") == "fuera_de_servicio" and estados.get("S06") == "fuera_de_servicio",
           "la consulta no incluye las salas fuera de servicio")
    chk.ok(set(estados.values()) <= {"disponible", "fuera_de_servicio"},
           "aparece un estado distinto de los definidos")


def test_CP_RF04_03_consulta_no_modifica_datos(bd_p4, chk):
    """La consulta es de solo lectura."""
    con = obtener_conexion()
    antes = con.total_changes
    consultar_salas()
    consultar_salas()
    chk.obs(f"cambios antes={antes}; después={con.total_changes}")
    chk.ok(con.total_changes == antes, "la consulta modificó la base de datos")
