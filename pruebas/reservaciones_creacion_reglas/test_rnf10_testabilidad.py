import sys
from pathlib import Path

from conftest import REPO, crear_valida, consultar_disponibilidad, fecha_futura, foto_reservaciones


def test_CP_RNF10_01_logica_sin_gui(bd_p2, chk):
    antes_gui = "src.view.app" in sys.modules
    r1 = crear_valida()
    r2 = consultar_disponibilidad("S02", fecha_futura(), "12:00", 1)
    despues_gui = "src.view.app" in sys.modules
    chk.obs(f"crear={r1}; disponibilidad={r2}; GUI antes={antes_gui}; GUI después={despues_gui}")
    chk.ok(r1.get("exito") is True and r2.get("disponible") is True, "la lógica no pudo ejercerse directamente")
    chk.ok(not despues_gui, "la ejecución de lógica cargó la interfaz gráfica")


def test_CP_RNF10_02_bd_aislada(bd_p2, chk):
    ruta_productiva = REPO / "src" / "db" / "reservas.db"
    existia = ruta_productiva.exists()
    bytes_antes = ruta_productiva.read_bytes() if existia else None
    r = crear_valida()
    temporal = foto_reservaciones()
    existia_despues = ruta_productiva.exists()
    bytes_despues = ruta_productiva.read_bytes() if existia_despues else None
    chk.obs(f"crear={r}; reservas_temporales={len(temporal)}; productiva_existía={existia}; después={existia_despues}")
    chk.ok(r.get("exito") is True and len(temporal) == 1, "la operación no se realizó sobre la base temporal")
    chk.ok(existia == existia_despues and bytes_antes == bytes_despues, "la prueba alteró la base de datos de uso normal")
