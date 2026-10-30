"""Fase 5, Persona 4: RF-16 Generar reporte CSV."""
import csv

from src.controller.controller import ControladorAplicacion
from src.model.reportes.servicio import generar_reporte_csv, validar_rango_reporte

from apoyo_p4 import insertar_reserva

ENCABEZADOS = ["estudiante", "sala", "fecha", "horario", "cantidad_personas", "estado"]


def _leer(ruta):
    with open(ruta, encoding="utf-8", newline="") as f:
        return list(csv.reader(f))


def _archivos(carpeta):
    return sorted(p.name for p in carpeta.iterdir())


def test_CP_RF16_01_rango_obligatorio(bd_p4, chk, tmp_path):
    """Sin fecha inicial o final no se genera el reporte ni se crea archivo."""
    destino = tmp_path / "reporte.csv"
    for ini, fin in (("", "2030-01-31"), ("2030-01-01", ""), (None, "2030-01-31"), ("2030-01-01", None),
                     ("   ", "2030-01-31")):
        r = generar_reporte_csv(ini, fin, destino)
        v = validar_rango_reporte(ini, fin)
        chk.obs(f"({ini!r}, {fin!r}) -> {r['mensaje']!r}")
        chk.ok(r["exito"] is False and v["exito"] is False, f"se aceptó el rango ({ini!r}, {fin!r})")
    chk.ok(not destino.exists(), "se creó un archivo con un rango incompleto")


def test_CP_RF16_02_fecha_final_anterior_y_limites(bd_p4, chk, tmp_path):
    """La fecha final no puede ser anterior; igual a la inicial es válida (valor límite)."""
    r_mal = generar_reporte_csv("2030-01-10", "2030-01-09", tmp_path / "mal.csv")
    r_igual = generar_reporte_csv("2030-01-10", "2030-01-10", tmp_path / "igual.csv")
    r_fmt = generar_reporte_csv("2030-02-30", "2030-03-01", tmp_path / "fmt.csv")
    chk.obs(f"fin<inicio -> {r_mal['mensaje']!r}; fin=inicio -> {r_igual['exito']}; 2030-02-30 -> {r_fmt['mensaje']!r}")
    chk.ok(r_mal["exito"] is False and not (tmp_path / "mal.csv").exists(), "se aceptó una fecha final anterior")
    chk.ok(r_igual["exito"] is True, "se rechazó un rango de un solo día")
    chk.ok(r_fmt["exito"] is False and not (tmp_path / "fmt.csv").exists(), "se aceptó una fecha inexistente")


def test_CP_RF16_03_contenido_y_rango_inclusivo(bd_p4, chk, tmp_path):
    """Incluye estudiante, sala, fecha, horario, cantidad y estado del rango (activas y canceladas)."""
    insertar_reserva("A001234567", "S01", "2030-01-09", "10:00", personas=2)  # fuera (antes)
    insertar_reserva("A001234567", "S02", "2030-01-10", "08:00", 2, 3)  # límite inicial
    insertar_reserva("B009876543", "S03", "2030-01-12", "15:00", 1, 5, estado="cancelada")
    insertar_reserva("B009876543", "S01", "2030-01-15", "18:00", 2, 4)  # límite final
    insertar_reserva("A001234567", "S05", "2030-01-16", "09:00", personas=1)  # fuera (después)
    destino = tmp_path / "reporte.csv"
    r = generar_reporte_csv("2030-01-10", "2030-01-15", destino)
    filas = _leer(destino) if destino.exists() else []
    chk.obs(f"respuesta={r}; filas={filas}")
    chk.ok(r["exito"] is True and r.get("cantidad") == 3, "el reporte no se generó con 3 reservaciones")
    chk.ok(filas[:1] == [ENCABEZADOS], "el archivo no inicia con los encabezados requeridos")
    esperado = [
        ["Andrea Solano", "S02", "2030-01-10", "08:00-10:00", "3", "activa"],
        ["Carlos Méndez", "S03", "2030-01-12", "15:00-16:00", "5", "cancelada"],
        ["Carlos Méndez", "S01", "2030-01-15", "18:00-20:00", "4", "activa"],
    ]
    chk.ok(filas[1:] == esperado, "las filas no corresponden al rango inclusivo o a los datos esperados")


def test_CP_RF16_04_cancelar_selector_no_crea_archivo(bd_p4, chk, tmp_path):
    """Si se cancela el selector de destino (None o vacío) no se crea ningún archivo."""
    insertar_reserva("A001234567", "S01", "2030-01-10", "10:00")
    antes = _archivos(tmp_path)
    ctl = ControladorAplicacion()
    respuestas = [generar_reporte_csv("2030-01-01", "2030-01-31", None),
                  generar_reporte_csv("2030-01-01", "2030-01-31", ""),
                  ctl.generar_reporte("2030-01-01", "2030-01-31", "")]
    chk.obs(f"respuestas={[(x['exito'], x.get('cancelado')) for x in respuestas]}; archivos={_archivos(tmp_path)}")
    chk.ok(all(x["exito"] is False and x.get("cancelado") is True for x in respuestas),
           "la cancelación no se informó como cancelada")
    chk.ok(_archivos(tmp_path) == antes, "la cancelación dejó archivos en la carpeta")


def test_CP_RF16_05_error_de_escritura_sin_archivo_parcial(bd_p4, chk, tmp_path):
    """Si el destino no es escribible, se informa el error y no quedan archivos incompletos."""
    insertar_reserva("A001234567", "S01", "2030-01-10", "10:00")
    destino = tmp_path / "no_existe" / "reporte.csv"
    r = generar_reporte_csv("2030-01-01", "2030-01-31", destino)
    chk.obs(f"respuesta={r}; archivos={_archivos(tmp_path)}")
    chk.ok(r["exito"] is False and r["mensaje"], "no se informó el error de escritura")
    chk.ok(_archivos(tmp_path) == ["p4.db"], "quedaron archivos temporales o incompletos")


def test_CP_RF16_06_rango_sin_reservaciones(bd_p4, chk, tmp_path):
    """Un rango sin datos genera un CSV válido solo con encabezados."""
    destino = tmp_path / "vacio.csv"
    r = generar_reporte_csv("2031-01-01", "2031-01-31", destino)
    filas = _leer(destino) if destino.exists() else None
    chk.obs(f"respuesta={r}; contenido={filas}")
    chk.ok(r["exito"] is True and filas == [ENCABEZADOS], "el reporte vacío no contiene únicamente los encabezados")
