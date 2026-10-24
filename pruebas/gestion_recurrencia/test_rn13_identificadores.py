"""RN-13: los IDs de reservaciones canceladas no se reutilizan ni al reiniciar conexión."""
from datetime import date, timedelta
from src.db.conexion import cerrar_conexion, obtener_conexion
from src.model.reservaciones.servicio import cancelar_reservacion, crear_reservacion, consultar_reservaciones


def test_CP_RN13_01_no_reutiliza_ids_tras_reiniciar(bd_p3):
    fecha = (date.today() + timedelta(days=4)).isoformat()
    primera = crear_reservacion('A001234567', 'S01', fecha, '09:00', 1, 2)
    assert primera['exito'] is True, primera
    id_cancelado = primera['id']
    assert cancelar_reservacion(id_cancelado)['exito'] is True
    segunda = crear_reservacion('B009876543', 'S01', fecha, '09:00', 1, 2)
    assert segunda['exito'] is True, segunda
    assert int(segunda['id'][1:]) > int(id_cancelado[1:])

    # Simula el reinicio de la aplicación cerrando y reabriendo SQLite temporal.
    cerrar_conexion()
    obtener_conexion()
    tercera = crear_reservacion('A001234567', 'S02', fecha, '12:00', 1, 2)
    assert tercera['exito'] is True, tercera
    assert int(tercera['id'][1:]) > int(segunda['id'][1:])
    resultado = consultar_reservaciones()
    assert resultado['exito'] is True, resultado
    registros = {r['id']: r for r in resultado['reservaciones']}
    assert len(registros) == 3
    assert registros[id_cancelado]['estado'] == 'cancelada'
    assert len(registros) == len(set(registros))
