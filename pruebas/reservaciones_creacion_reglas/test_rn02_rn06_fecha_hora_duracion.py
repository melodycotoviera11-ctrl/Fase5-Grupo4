from datetime import datetime as DateTimeReal, timedelta
import src.model.reservaciones.servicio as servicio_res

from conftest import crear_valida, fecha_futura, foto_reservaciones


def test_CP_RN02_01_rechaza_fecha_pasada(bd_p2, chk):
    fecha = (DateTimeReal.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    r = crear_valida(fecha=fecha)
    chk.obs(f"fecha={fecha}; respuesta={r}")
    chk.ok(r.get("exito") is False and "anterior" in r.get("mensaje", "").lower(), f"no rechazó fecha pasada correctamente: {r}")


def test_CP_RN02_02_rechaza_fecha_formato_o_valor_invalido(bd_p2, chk):
    antes = foto_reservaciones()
    resultados = [crear_valida(fecha="10-12-2030"), crear_valida(fecha="2030-02-30")]
    chk.obs(f"resultados={resultados}")
    chk.ok(all(r.get("exito") is False for r in resultados), "alguna fecha inválida fue aceptada")
    chk.ok(all("formato" in r.get("mensaje", "").lower() for r in resultados), "algún mensaje no identifica formato/fecha inválida")
    chk.ok(foto_reservaciones() == antes, "se guardó información con fecha inválida")


def test_CP_RN03_01_hoy_debe_iniciar_despues_hora_actual(bd_p2, chk, monkeypatch):
    class FechaControlada(DateTimeReal):
        @classmethod
        def now(cls, tz=None):
            return cls(2030, 1, 15, 10, 30)
    monkeypatch.setattr(servicio_res, "datetime", FechaControlada)
    r = crear_valida(fecha="2030-01-15", hora_inicio="10:00")
    chk.obs(f"ahora simulado=2030-01-15 10:30; respuesta={r}")
    chk.ok(r.get("exito") is False, "se aceptó una reservación para una hora ya transcurrida hoy")
    chk.ok("transcurrió" in r.get("mensaje", "").lower(), f"mensaje inesperado: {r}")


def test_CP_RN04_01_rechaza_hora_no_completa(bd_p2, chk):
    r = crear_valida(hora_inicio="09:30")
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "hora completa" in r.get("mensaje", "").lower(), f"no rechazó 09:30 correctamente: {r}")


def test_CP_RN05_01_rechaza_antes_0800(bd_p2, chk):
    r = crear_valida(hora_inicio="07:00")
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "08:00" in r.get("mensaje", ""), f"no rechazó horario anterior a 08:00: {r}")


def test_CP_RN05_02_rechaza_fin_despues_2000(bd_p2, chk):
    r = crear_valida(hora_inicio="19:00", duracion=2)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is False and "20:00" in r.get("mensaje", ""), f"no rechazó fin posterior a 20:00: {r}")


def test_CP_RN05_03_acepta_fin_exactamente_2000(bd_p2, chk):
    r = crear_valida(hora_inicio="19:00", duracion=1)
    chk.obs(f"respuesta={r}")
    chk.ok(r.get("exito") is True, f"rechazó una reservación que termina exactamente a las 20:00: {r}")


def test_CP_RN06_01_acepta_duracion_1_y_2(bd_p2, chk):
    r1 = crear_valida(codigo_sala="S01", hora_inicio="10:00", duracion=1)
    r2 = crear_valida(codigo_sala="S02", hora_inicio="12:00", duracion=2)
    chk.obs(f"1h={r1}; 2h={r2}")
    chk.ok(r1.get("exito") is True and r2.get("exito") is True, "se rechazó alguna duración permitida")


def test_CP_RN06_02_rechaza_duracion_fuera_1_o_2(bd_p2, chk):
    resultados = [crear_valida(duracion=v) for v in (0, 3, 1.5)]
    chk.obs(f"resultados={resultados}")
    chk.ok(all(r.get("exito") is False for r in resultados), "alguna duración inválida fue aceptada")
    chk.ok(all("duración" in r.get("mensaje", "").lower() for r in resultados), "algún mensaje no identifica la duración")
