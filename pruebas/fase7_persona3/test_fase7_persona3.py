"""Fase 7, Persona 3: verificacion de BUG-RES-02, BUG-REC-01 e integracion.

Pruebas independientes sobre el servicio real del Grupo 6 (commit 92e1fd8).
Usan la BD temporal del fixture bd_p3. No modifican codigo productivo.
"""
from datetime import date, timedelta

from src.model.reservaciones.servicio import (
    cancelar_ocurrencias_futuras,
    cancelar_reservacion,
    consultar_reservaciones,
    crear_reservaciones_recurrentes,
    modificar_reservacion,
)
from src.model.salas.servicio import consultar_disponibilidad
from src.model.panel.servicio import consultar_panel


def _foto(con):
    """Copia completa de todas las tablas (reservaciones, auditoria, etc.)."""
    tablas = [
        f[0] for f in con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]
    return {
        t: [tuple(r) for r in con.execute(f"SELECT * FROM {t} ORDER BY 1")]
        for t in tablas
    }


def _reservas():
    respuesta = consultar_reservaciones()
    assert respuesta['exito'] is True, respuesta
    return {r['id']: r for r in respuesta['reservaciones']}


def _datos_serie(semanas=3):
    return {
        'carne': 'A001234567',
        'codigo_sala': 'S01',
        'fecha': (date.today() + timedelta(days=14)).isoformat(),
        'hora_inicio': '10:00',
        'duracion': 1,
        'cantidad_personas': 2,
        'semanas': semanas,
    }


def test_BUG_RES_02_cambio_a_sala_sin_capacidad(bd_p3, insertar_reserva):
    """4 personas de S02 a S05 (capacidad 1): rechazo y base sin cambios."""
    sala5 = bd_p3.execute("SELECT * FROM salas WHERE codigo='S05'").fetchone()
    identificador = insertar_reserva('B009876543', 'S02', 2, '10:00', 1, 4)
    foto_antes = _foto(bd_p3)
    antes = _reservas()[identificador].copy()

    respuesta = modificar_reservacion(identificador, codigo_sala='S05')

    foto_despues = _foto(bd_p3)
    print("\nBUG-RES-02")
    print("  Sala S05 (registro):", tuple(sala5) if sala5 else None)
    print("  Reservacion:", identificador, "- 4 personas en S02")
    print("  Respuesta del servicio:", respuesta)
    print("  Base sin cambios:", foto_antes == foto_despues)

    assert respuesta['exito'] is False, respuesta
    assert 'capacidad' in respuesta['mensaje'].lower(), respuesta
    assert foto_despues == foto_antes
    assert _reservas()[identificador] == antes


def test_BUG_REC_01_modificar_una_ocurrencia_conserva_serie(bd_p3):
    """Serie de 3: cambiar solo la hora de la segunda conserva serie_id."""
    creada = crear_reservaciones_recurrentes(**_datos_serie())
    assert creada['exito'] is True, creada
    primera, segunda, tercera = creada['ids']
    antes = {i: _reservas()[i].copy() for i in creada['ids']}

    respuesta = modificar_reservacion(segunda, hora_inicio='12:00')

    despues = {i: _reservas()[i].copy() for i in creada['ids']}
    print("\nBUG-REC-01")
    print("  Respuesta del servicio:", respuesta)
    for i in creada['ids']:
        print("  ", i, "serie_id", antes[i]['serie_id'], "->", despues[i]['serie_id'],
              "| hora", antes[i]['hora_inicio'], "->", despues[i]['hora_inicio'])

    assert respuesta['exito'] is True, respuesta
    assert len({despues[i]['serie_id'] for i in creada['ids']}) == 1
    assert all(despues[i]['serie_id'] == antes[i]['serie_id'] for i in creada['ids'])
    assert despues[primera] == antes[primera]
    assert despues[tercera] == antes[tercera]
    assert despues[segunda]['hora_inicio'] == '12:00'
    assert despues[segunda]['fecha'] == antes[segunda]['fecha']


def test_integracion_serie_cancelacion_panel_disponibilidad(bd_p3):
    """Serie de 3 -> cancelar una -> panel/disponibilidad -> cancelar serie."""
    creada = crear_reservaciones_recurrentes(**_datos_serie())
    assert creada['exito'] is True, creada
    ids = creada['ids']
    fechas = [_reservas()[i]['fecha'] for i in ids]

    def libre(indice):
        return consultar_disponibilidad('S01', fechas[indice], '10:00', 1)['disponible']

    def panel(indice):
        resp = consultar_panel(fecha=fechas[indice], codigo_sala='S01')
        assert 'exito' not in resp or resp['exito'] is True, resp
        return resp

    print("\nINTEGRACION")
    # Paso 1: serie creada, tres franjas ocupadas
    estado1 = [libre(i) for i in range(3)]
    print("  Paso 1 - disponibles tras crear serie (esperado False x3):", estado1)
    print("  Panel fecha 1:", panel(0))
    assert estado1 == [False, False, False]

    # Paso 2: cancelar una ocurrencia
    assert cancelar_reservacion(ids[1])['exito'] is True
    estado2 = [libre(i) for i in range(3)]
    estados = [_reservas()[i]['estado'] for i in ids]
    print("  Paso 2 - disponibles tras cancelar la 2da (esperado F,T,F):", estado2)
    print("  Estados:", estados)
    print("  Panel fecha 2:", panel(1))
    assert estado2 == [False, True, False]
    assert estados == ['activa', 'cancelada', 'activa']

    # Paso 3: cancelar la serie completa desde la primera ocurrencia
    resp = cancelar_ocurrencias_futuras(ids[0])
    assert resp['exito'] is True, resp
    estado3 = [libre(i) for i in range(3)]
    estados3 = [_reservas()[i]['estado'] for i in ids]
    print("  Paso 3 - disponibles tras cancelar la serie (esperado True x3):", estado3)
    print("  Estados:", estados3)
    print("  Panel fecha 1:", panel(0))
    assert estado3 == [True, True, True]
    assert estados3 == ['cancelada', 'cancelada', 'cancelada']