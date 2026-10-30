"""Fase 5, Persona 4: RF-12 Gestionar salas (incluye RNF-06 sobre escrituras rechazadas)."""
from src.model.panel.servicio import consultar_panel
from src.model.reservaciones.servicio import crear_reservacion
from src.model.salas.servicio import consultar_disponibilidad, consultar_salas, modificar_sala, registrar_sala

from apoyo_p4 import fecha_rel, foto, insertar_reserva


def _sala(codigo):
    return next((s for s in consultar_salas() if s["codigo"] == codigo), None)


def test_CP_RF12_01_registrar_sala_valida(bd_p4, chk):
    """Una sala válida se guarda con estado disponible por defecto."""
    r = registrar_sala("S06", "Sala de reuniones", 5)
    chk.obs(f"respuesta={r}; sala={_sala('S06')}")
    chk.ok(r["exito"] is True, "no se registró una sala válida")
    chk.ok(_sala("S06") == {"codigo": "S06", "nombre": "Sala de reuniones", "capacidad": 5, "estado": "disponible"},
           "la sala no quedó guardada con los datos y el estado inicial esperados")


def test_CP_RF12_02_codigo_duplicado_rechazado(bd_p4, chk):
    """El código debe ser único: un duplicado exacto se rechaza sin cambios."""
    antes = foto("salas")
    r = registrar_sala("S01", "Duplicada", 3)
    chk.obs(f"respuesta={r}")
    chk.ok(r["exito"] is False, "se aceptó un código de sala duplicado")
    chk.ok(foto("salas") == antes, "la tabla de salas cambió tras el rechazo")


def test_CP_RF12_03_codigo_equivalente_no_crea_duplicado(bd_p4, chk):
    """Un código equivalente (minúsculas o espacios periféricos) no debe crear otra sala.

    Se toma como referencia la normalización que el propio sistema aplica en el
    panel (strip + mayúsculas, RF-15) y la regla de espacios periféricos del
    modelo de información.
    """
    for codigo in ("s01", " S01 ", "S01 "):
        r = registrar_sala(codigo, "Sala equivalente", 3)
        chk.obs(f"código enviado={codigo!r} -> {r}")
        chk.ok(r["exito"] is False, f"se registró {codigo!r}, equivalente a S01, como una sala distinta")
    codigos = [s["codigo"] for s in consultar_salas()]
    chk.obs(f"códigos guardados={codigos}")
    chk.ok(len(codigos) == 5, "la consulta de salas quedó con códigos equivalentes duplicados")


def test_CP_RF12_04_capacidad_invalida_rechazada(bd_p4, chk):
    """La capacidad debe ser un entero mayor que cero (partición y límites)."""
    antes = foto("salas")
    for valor in (0, -1, 2.5, "4", None):
        r = registrar_sala("S07", "Sala capacidad", valor)
        chk.obs(f"capacidad={valor!r} -> {r['exito']}")
        chk.ok(r["exito"] is False, f"se aceptó la capacidad {valor!r}")
    r = registrar_sala("S07", "Sala capacidad", 1)
    chk.obs(f"capacidad=1 (límite) -> {r['exito']}")
    chk.ok(r["exito"] is True, "se rechazó la capacidad mínima válida (1)")
    chk.ok(len(foto("salas")) == len(antes) + 1, "los intentos rechazados dejaron registros")


def test_CP_RF12_05_nombre_vacio_rechazado(bd_p4, chk):
    """Una sala no debe quedar sin nombre al registrarla ni al modificarla (RNF-05)."""
    for i, nombre in enumerate(("", "   ")):
        r1 = registrar_sala(f"S0{7 + i}", nombre, 3)
        r2 = modificar_sala("S01", nombre, 4, "disponible")
        chk.obs(f"nombre={nombre!r}: registrar={r1}; modificar={r2}")
        chk.ok(r1["exito"] is False, f"se registró una sala con nombre {nombre!r}")
        chk.ok(r2["exito"] is False, f"se modificó S01 dejándola con nombre {nombre!r}")
    chk.obs(f"S01 final={_sala('S01')}")


def test_CP_RF12_06_modificar_nombre_y_capacidad_conserva_codigo(bd_p4, chk):
    """La modificación cambia nombre y capacidad; el código no se altera."""
    r = modificar_sala("S02", "Sala Biblioteca 2 renovada", 7, "disponible")
    chk.obs(f"respuesta={r}; S02={_sala('S02')}")
    chk.ok(r["exito"] is True, "no se pudo modificar una sala con datos válidos")
    chk.ok(_sala("S02") == {"codigo": "S02", "nombre": "Sala Biblioteca 2 renovada", "capacidad": 7,
                            "estado": "disponible"}, "los cambios no se persistieron como se esperaba")
    chk.ok(len(consultar_salas()) == 5, "la modificación creó o eliminó salas")


def test_CP_RF12_07_no_reduce_capacidad_bajo_reserva_futura(bd_p4, chk):
    """No se reduce la capacidad por debajo de una reservación activa futura (valores límite)."""
    insertar_reserva("A001234567", "S03", fecha_rel(5), "10:00", personas=6)
    antes = foto("salas")
    r_menor = modificar_sala("S03", "Laboratorio de estudio", 5, "disponible")
    chk.obs(f"capacidad 5 con reserva de 6 -> {r_menor}")
    chk.ok(r_menor["exito"] is False, "se redujo la capacidad por debajo de una reserva futura")
    chk.ok(foto("salas") == antes, "el rechazo modificó la sala")
    r_igual = modificar_sala("S03", "Laboratorio de estudio", 6, "disponible")
    chk.obs(f"capacidad 6 con reserva de 6 -> {r_igual}")
    chk.ok(r_igual["exito"] is True, "se rechazó una capacidad igual a la reserva futura")


def test_CP_RF12_08_reservas_canceladas_o_pasadas_no_limitan_capacidad(bd_p4, chk):
    """Solo las reservaciones activas futuras limitan la reducción de capacidad."""
    insertar_reserva("A001234567", "S03", fecha_rel(5), "10:00", personas=9, estado="cancelada")
    insertar_reserva("B009876543", "S03", fecha_rel(-3), "10:00", personas=8)
    r = modificar_sala("S03", "Laboratorio de estudio", 2, "disponible")
    chk.obs(f"respuesta={r}")
    chk.ok(r["exito"] is True, "una reserva cancelada o pasada impidió reducir la capacidad")


def test_CP_RF12_09_fuera_de_servicio_conserva_historial_y_rechaza(bd_p4, chk):
    """Al pasar a fuera de servicio se conserva el historial y se rechazan nuevas reservas."""
    id_previa = insertar_reserva("A001234567", "S01", fecha_rel(4), "09:00", personas=2)
    r = modificar_sala("S01", "Sala Biblioteca 1", 4, "fuera_de_servicio")
    chk.ok(r["exito"] is True, f"no se pudo cambiar el estado: {r}")
    panel = consultar_panel(codigo_sala="S01")
    chk.ok(any(x["id"] == id_previa for x in panel["resultados"]), "la reservación previa desapareció del historial")
    nueva = crear_reservacion("B009876543", "S01", fecha_rel(6), "10:00", 1, 2)
    disp = consultar_disponibilidad("S01", fecha_rel(6), "10:00", 1)
    chk.obs(f"cambio={r}; crear={nueva}; disponibilidad={disp}")
    chk.ok(nueva["exito"] is False, "se permitió reservar una sala fuera de servicio")
    chk.ok(disp["disponible"] is False, "la disponibilidad indica libre una sala fuera de servicio")
    reactivar = modificar_sala("S01", "Sala Biblioteca 1", 4, "disponible")
    otra = crear_reservacion("B009876543", "S01", fecha_rel(6), "10:00", 1, 2)
    chk.obs(f"reactivar={reactivar}; crear tras reactivar={otra}")
    chk.ok(otra["exito"] is True, "tras reactivar la sala no se pudo reservar")


def test_CP_RF12_10_entradas_invalidas_sin_cambios(bd_p4, chk):
    """Sala inexistente o estado inválido: mensaje y sin cambios (RNF-06)."""
    antes = foto("salas")
    casos = {
        "sala inexistente": modificar_sala("S99", "No existe", 3, "disponible"),
        "estado inválido (modificar)": modificar_sala("S01", "Sala Biblioteca 1", 4, "mantenimiento"),
        "estado inválido (registrar)": registrar_sala("S07", "Sala nueva", 4, "cerrada"),
        "capacidad 0 (modificar)": modificar_sala("S01", "Sala Biblioteca 1", 0, "disponible"),
    }
    for nombre, r in casos.items():
        chk.obs(f"{nombre}: {r}")
        chk.ok(r["exito"] is False, f"se aceptó: {nombre}")
        chk.ok(bool(str(r.get("mensaje", "")).strip()), f"sin mensaje explicativo: {nombre}")
    chk.ok(foto("salas") == antes, "una operación rechazada modificó la tabla de salas")
