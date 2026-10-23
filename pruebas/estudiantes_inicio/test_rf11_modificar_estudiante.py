"""RF-11 Modificar estudiante (CP-RF11-01 a CP-RF11-04). Modo lógica.
CP-RF11-05 (confirmación visual) es manual: Auto. F5 = No."""
from conftest import buscar, foto_tabla, modificar_estudiante, registrar_estudiante

CORREO = "ana.mora@universidad.ac.cr"


def _ana():
    ok, msg = registrar_estudiante("D001112223", "Ana Mora", CORREO)
    assert ok, msg


def test_CP_RF11_01_edita_nombre_y_correo(ds01, chk):
    _ana()
    ok, msg = modificar_estudiante("D001112223", "Ana Mora Solís", "ana.solis@universidad.ac.cr", "activo")
    e = buscar("D001112223")
    chk.obs(f"ok={ok}, mensaje={msg!r}, resultado={e}")
    chk.ok(ok is True, f"se rechazó una edición válida: {msg!r}")
    chk.ok(e and (e["nombre_completo"], e["correo"]) == ("Ana Mora Solís", "ana.solis@universidad.ac.cr"), "no se actualizaron nombre y correo")
    chk.ok(e and (e["carne"], e["estado"]) == ("D001112223", "activo"), "cambió el carné o el estado")


def test_CP_RF11_02_edicion_invalida_conserva_originales(ds01, chk):
    _ana()
    casos = [("(a) nombre 'Al'", "Al", CORREO, ["nombre"]),
             ("(b) correo 'ana@@...'", "Ana Mora", "ana@@universidad.ac.cr", ["correo", "@"]),
             ("(c) nombre válido + correo inválido", "Ana Solís", "sin-arroba", ["correo", "@"]),
             ("(d) nombre vacío", "", CORREO, ["nombre"])]
    for etiqueta, nombre, correo, palabras in casos:
        antes = foto_tabla()
        ok, msg = modificar_estudiante("D001112223", nombre, correo, "activo")
        chk.obs(f"{etiqueta}: ok={ok}, mensaje={msg!r}")
        chk.ok(ok is False, f"{etiqueta}: se aceptó una edición inválida")
        chk.ok(any(p in msg.lower() for p in palabras), f"{etiqueta}: el mensaje no identifica el dato inválido ({msg!r})")
        chk.ok(foto_tabla() == antes, f"{etiqueta}: se alteraron los datos originales")


def test_CP_RF11_03_inactivar_estudiante(ds01, chk):
    _ana()
    ok, msg = modificar_estudiante("D001112223", "Ana Mora", CORREO, "inactivo")
    e = buscar("D001112223")
    chk.obs(f"ok={ok}, mensaje={msg!r}, resultado={e}")
    chk.ok(ok is True, f"no permitió inactivar: {msg!r}")
    chk.ok(e is not None, "el estudiante inactivo dejó de aparecer en la consulta")
    chk.ok(e and e["estado"] == "inactivo" and e["nombre_completo"] == "Ana Mora" and e["correo"] == CORREO,
           "el estado no es inactivo o cambiaron otros datos")


def test_CP_RF11_04_activar_estudiante(ds01, chk):
    assert buscar("C004567890")["estado"] == "inactivo"
    ok, msg = modificar_estudiante("C004567890", "Daniela Rojas", "daniela@universidad.ac.cr", "activo")
    e = buscar("C004567890")
    chk.obs(f"ok={ok}, mensaje={msg!r}, resultado={e}")
    chk.ok(ok is True, f"no permitió activar: {msg!r}")
    chk.ok(e and e["estado"] == "activo" and e["nombre_completo"] == "Daniela Rojas" and e["correo"] == "daniela@universidad.ac.cr",
           "no quedó activa o cambiaron otros datos")
