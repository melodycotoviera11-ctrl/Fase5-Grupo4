"""RF-03 Consultar estudiantes (CP-RF03-01 a CP-RF03-03). Modo lógica."""
from conftest import consultar_estudiantes, foto_tabla, obtener_conexion, registrar_estudiante


def test_CP_RF03_01_lista_ordenada_con_activos_e_inactivos(ds01, chk):
    registrar_estudiante("D001112223", "Ana Mora", "ana.mora@universidad.ac.cr")
    ok, msg, datos = consultar_estudiantes()
    nombres = [e["nombre_completo"] for e in datos]
    chk.obs(f"ok={ok}, mensaje={msg!r}, orden={nombres}")
    chk.ok(nombres == ["Ana Mora", "Andrea Solano", "Carlos Méndez", "Daniela Rojas"], f"orden/cantidad incorrectos: {nombres}")
    chk.ok(all(set(e) >= {"carne", "nombre_completo", "correo", "estado"} for e in datos), "falta alguno de los 4 campos")
    chk.ok(next((e["estado"] for e in datos if e["nombre_completo"] == "Daniela Rojas"), None) == "inactivo",
           "Daniela Rojas debería aparecer como inactivo")


def test_CP_RF03_02_consultar_no_modifica(ds01, chk):
    registrar_estudiante("D001112223", "Ana Mora", "ana.mora@universidad.ac.cr")
    antes = foto_tabla()
    for _ in range(3):
        consultar_estudiantes()
    chk.obs(f"filas antes={len(antes)}, después={len(foto_tabla())}")
    chk.ok(foto_tabla() == antes, "el contenido de la tabla cambió tras consultar")


def test_CP_RF03_03_mensaje_si_no_hay_estudiantes(bd_inicial, chk):
    con = obtener_conexion()
    con.execute("DELETE FROM estudiantes")
    con.commit()
    ok, msg, datos = consultar_estudiantes()
    chk.obs(f"ok={ok}, mensaje={msg!r}, datos={datos}")
    chk.ok(datos == [], "la lista no está vacía")
    chk.ok(isinstance(msg, str) and "no hay" in msg.lower(), f"no hay mensaje informativo ({msg!r})")
