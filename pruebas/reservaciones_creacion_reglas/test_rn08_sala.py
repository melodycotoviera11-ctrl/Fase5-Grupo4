from conftest import crear_valida


def test_CP_RN08_01_rechaza_sala_fuera_servicio(bd_p2, chk):
    r = crear_valida(codigo_sala="S04")
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "fuera de servicio" in r.get("mensaje", "").lower(), f"no rechazó S04: {r}")
