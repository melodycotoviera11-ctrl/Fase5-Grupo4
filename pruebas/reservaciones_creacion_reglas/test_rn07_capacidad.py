from conftest import crear_valida


def test_CP_RN07_01_acepta_capacidad_exacta(bd_p2, chk):
    r = crear_valida(codigo_sala="S01", cantidad_personas=4)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is True, f"rechazó cantidad igual a la capacidad: {r}")


def test_CP_RN07_02_rechaza_superior_capacidad(bd_p2, chk):
    r = crear_valida(codigo_sala="S01", cantidad_personas=5)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "capacidad" in r.get("mensaje", "").lower(), f"no rechazó capacidad excedida: {r}")


def test_CP_RN07_03_rechaza_cero_personas(bd_p2, chk):
    r = crear_valida(cantidad_personas=0)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "mayor que cero" in r.get("mensaje", "").lower(), f"no rechazó cero personas: {r}")


def test_CP_RN07_04_rechaza_cantidad_decimal(bd_p2, chk):
    r = crear_valida(cantidad_personas=1.5)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "entero" in r.get("mensaje", "").lower(), f"no rechazó cantidad decimal: {r}")
