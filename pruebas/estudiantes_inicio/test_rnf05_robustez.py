"""RNF-05 Robustez (CP-RNF05-01 a CP-RNF05-03)."""
import shutil
from conftest import (buscar, clon_limpio, ejecutar_app, foto_tabla, lista, modificar_estudiante,
                      obtener_conexion, registrar_estudiante)


def test_CP_RNF05_01_entrada_invalida_no_cierra_ni_deja_datos_parciales(ds01, chk):
    antes = foto_tabla()
    n = len(lista())
    try:
        r1 = registrar_estudiante("D000000004", "Ana Mora", "sin-arroba")
        r2 = modificar_estudiante("A001234567", "Al", "andrea@universidad.ac.cr", "activo")
    except Exception as exc:  # una excepción sin controlar equivale a cierre del programa
        chk.ok(False, f"excepción sin controlar: {exc!r}")
        return
    chk.obs(f"registro inválido={r1}; edición inválida={r2}")
    chk.ok(r1[0] is False and r2[0] is False, "alguna entrada inválida fue aceptada")
    chk.ok(len(lista()) == n and foto_tabla() == antes, "quedaron datos parciales")
    ok, msg = registrar_estudiante("D000000005", "Ana Mora", "ana.mora@universidad.ac.cr")
    chk.ok(ok is True and buscar("D000000005") is not None, f"un registro válido posterior falló: {msg!r}")


def test_CP_RNF05_02_caracteres_especiales_y_texto_largo(ds01, chk):
    antes = foto_tabla()
    variantes = [("D000000006", "Robert'); DROP TABLE estudiantes;--"), ("D000000007", "A" * 300)]
    for carne, nombre in variantes:
        try:
            ok, msg = registrar_estudiante(carne, nombre, "ana.mora@universidad.ac.cr")
        except Exception as exc:
            chk.ok(False, f"{nombre[:20]!r}: excepción sin controlar {exc!r}")
            continue
        e = buscar(carne)
        chk.obs(f"{nombre[:25]!r}(len={len(nombre)}): ok={ok}, mensaje={msg!r}, guardado_integro={bool(e) and e['nombre_completo'] == nombre}")
        chk.ok(isinstance(msg, str) and msg, "sin mensaje")
        if ok:
            chk.ok(e is not None and e["nombre_completo"] == nombre, "el texto aceptado no se guardó íntegro")
    tabla = obtener_conexion().execute("SELECT name FROM sqlite_master WHERE name='estudiantes'").fetchone()
    chk.ok(tabla is not None, "la tabla estudiantes fue eliminada")
    originales = [f for f in foto_tabla() if f in antes]
    chk.ok(originales == antes, "los datos existentes se alteraron")


def test_CP_RNF05_03_bd_danada_no_cierra_sin_aviso(tmp_path, chk):
    carpeta = clon_limpio(tmp_path / "clon")
    ruta = carpeta / "src" / "db" / "reservas.db"
    ruta.write_text("Esto no es una base de datos SQLite.\n", encoding="utf-8")
    codigo, out, err, vivo = ejecutar_app(carpeta)
    chk.obs(f"código de salida={codigo}; stdout={out.strip()!r}; stderr={err.strip()[:300]!r}")
    chk.ok("Traceback" not in err, "terminó con un error sin controlar (traza técnica)")
    chk.ok(bool((out + err).strip()), "no mostró ningún mensaje a la persona usuaria")
    chk.ok(not vivo or "No fue posible" in out, "continuó como si nada sin avisar")
