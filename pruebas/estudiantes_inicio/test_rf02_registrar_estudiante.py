"""RF-02 Registrar estudiante (CP-RF02-01 a CP-RF02-11). Modo lógica."""
from conftest import buscar, foto_tabla, lista, registrar_estudiante

OK_NOMBRE, OK_CORREO = "Ana Mora", "ana.mora@universidad.ac.cr"


def rechaza(chk, etiqueta, carne, nombre, correo, palabras):
    antes = foto_tabla()
    ok, msg = registrar_estudiante(carne, nombre, correo)
    chk.obs(f"{etiqueta}: ok={ok}, mensaje={msg!r}")
    chk.ok(ok is False, f"{etiqueta}: se aceptó un registro inválido")
    chk.ok(any(p in msg.lower() for p in palabras), f"{etiqueta}: el mensaje no identifica el dato inválido ({msg!r})")
    chk.ok(foto_tabla() == antes, f"{etiqueta}: cambió la tabla de estudiantes")


def test_CP_RF02_01_carne_duplicado_otra_capitalizacion(ds01, chk):
    rechaza(chk, "(a) a001234567", "a001234567", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    rechaza(chk, "(b) b009876543", "b009876543", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    chk.ok(len(lista()) == 3, "la lista ya no tiene los 3 estudiantes iniciales")


def test_CP_RF02_02_carne_9_caracteres(ds01, chk):
    rechaza(chk, "carné 9", "D00111222", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    chk.ok(buscar("D00111222") is None, "el estudiante aparece en la lista")


def test_CP_RF02_03_carne_10_caracteres(ds01, chk):
    ok, msg = registrar_estudiante("D001112223", OK_NOMBRE, OK_CORREO)
    e = buscar("D001112223")
    chk.obs(f"ok={ok}, mensaje={msg!r}, guardado={e}")
    chk.ok(ok is True, f"no se aceptó un carné válido: {msg!r}")
    chk.ok(e is not None, "no aparece en la lista")
    if e:
        chk.ok(e["estado"] == "activo" and e["nombre_completo"] == OK_NOMBRE and e["correo"] == OK_CORREO,
               "los datos guardados o el estado inicial son incorrectos")


def test_CP_RF02_04_carne_11_caracteres(ds01, chk):
    rechaza(chk, "carné 11", "D0011122233", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    chk.ok(buscar("D0011122233") is None, "el estudiante aparece en la lista")


def test_CP_RF02_05_carne_con_espacios_o_simbolos(ds01, chk):
    rechaza(chk, "(a) espacio", "D00111 222", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    rechaza(chk, "(b) símbolo", "D00111222!", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    chk.ok(len(lista()) == 3, "alguno de los carnés inválidos quedó registrado")


def test_CP_RF02_06_nombre_minimo_3_caracteres(ds01, chk):
    rechaza(chk, "(a) 'Al'", "D000000001", "Al", OK_CORREO, ["nombre"])
    ok, msg = registrar_estudiante("D000000002", "Ana", OK_CORREO)
    chk.obs(f"(b) 'Ana': ok={ok}, mensaje={msg!r}")
    chk.ok(ok is True, f"(b) se rechazó un nombre de 3 caracteres: {msg!r}")
    rechaza(chk, "(c) 'A l'", "D000000003", "A l", OK_CORREO, ["nombre"])
    nuevos = sorted(e["carne"] for e in lista() if e["carne"].startswith("D00000000"))
    chk.ok(nuevos == ["D000000002"], f"en la lista debía aparecer solo (b); aparecen {nuevos}")


def test_CP_RF02_07_correo_sin_arroba(ds01, chk):
    rechaza(chk, "sin @", "D001112223", OK_NOMBRE, "ana.morauniversidad.ac.cr", ["correo", "@"])


def test_CP_RF02_08_correo_dos_arrobas(ds01, chk):
    rechaza(chk, "dos @", "D001112223", OK_NOMBRE, "ana@mora@universidad.ac.cr", ["correo", "@"])


def test_CP_RF02_09_correo_sin_punto_despues_arroba(ds01, chk):
    rechaza(chk, "(a) sin punto", "D001112223", OK_NOMBRE, "ana.mora@universidad", ["correo"])
    rechaza(chk, "(b) sin punto", "D001112223", OK_NOMBRE, "ana.mora@universidadacr", ["correo"])
    chk.ok(buscar("D001112223") is None, "el estudiante aparece en la lista")


def test_CP_RF02_10_campos_vacios(ds01, chk):
    rechaza(chk, "(a) carné vacío", "", OK_NOMBRE, OK_CORREO, ["carné", "carne"])
    rechaza(chk, "(b) nombre vacío", "D001112223", "", OK_CORREO, ["nombre"])
    rechaza(chk, "(c) correo vacío", "D001112223", OK_NOMBRE, "", ["correo", "@"])
    rechaza(chk, "(d) tres vacíos", "", "", "", ["carné", "carne", "nombre", "correo"])
    rechaza(chk, "(e) tres con espacios", "   ", "   ", "   ", ["carné", "carne", "nombre", "correo"])


def test_CP_RF02_11_recorta_espacios_extremos(ds01, chk):
    ok, msg = registrar_estudiante("       D001112223     ", "     Ana Mora      ", " ana.mora@universidad.ac.cr ")
    e = buscar("D001112223")
    chk.obs(f"ok={ok}, mensaje={msg!r}, guardado={e}")
    chk.ok(ok is True, f"se rechazó un registro válido con espacios periféricos: {msg!r}")
    chk.ok(e is not None and (e["carne"], e["nombre_completo"], e["correo"]) == ("D001112223", "Ana Mora", OK_CORREO),
           "los valores guardados conservan espacios en los extremos")
