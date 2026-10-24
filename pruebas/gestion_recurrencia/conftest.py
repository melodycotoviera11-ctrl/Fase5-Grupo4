"""Fixtures aisladas para Persona 3 — Grupo 4, Fase 5."""
import os
import sys
from pathlib import Path
from datetime import date, timedelta

import pytest

REPO = Path(os.environ.get('REPO_G6', '')).resolve() if os.environ.get('REPO_G6') else None
if REPO is None or not (REPO / 'src').is_dir():
    raise pytest.UsageError('Defina REPO_G6 con la ruta del repositorio del Grupo 6 (que contiene src/).')
sys.path.insert(0, str(REPO))

from src.db.conexion import configurar_ruta_base_datos, cerrar_conexion, obtener_conexion, obtener_ruta_base_datos
from src.db.inicializador import inicializar_base_datos

@pytest.fixture
def bd_p3(tmp_path):
    anterior = obtener_ruta_base_datos()
    cerrar_conexion()
    configurar_ruta_base_datos(tmp_path / 'persona3.db')
    try:
        resultado = inicializar_base_datos()
        assert resultado.exito, resultado.mensaje
        con = obtener_conexion()
        con.executemany(
            'INSERT INTO estudiantes (carne, nombre_completo, correo, estado) VALUES (?,?,?,?)',
            [('A001234567', 'Andrea Solano', 'andrea@universidad.ac.cr', 'activo'),
             ('B009876543', 'Carlos Méndez', 'carlos@universidad.ac.cr', 'activo'),
             ('C004567890', 'Daniela Rojas', 'daniela@universidad.ac.cr', 'inactivo')]
        )
        con.commit()
        yield con
    finally:
        cerrar_conexion()
        configurar_ruta_base_datos(anterior)

@pytest.fixture
def insertar_reserva(bd_p3):
    def insertar(carne, sala, dias, hora, duracion=1, personas=1, estado='activa'):
        fecha = (date.today() + timedelta(days=dias)).isoformat()
        cur = bd_p3.execute('''INSERT INTO reservaciones
            (estudiante_id, sala_id, fecha, hora_inicio, duracion_horas, cantidad_personas, estado)
            VALUES ((SELECT id FROM estudiantes WHERE carne=?),
                    (SELECT id FROM salas WHERE codigo=?), ?, ?, ?, ?, ?)''',
            (carne, sala, fecha, hora, duracion, personas, estado))
        bd_p3.commit()
        return f'R{cur.lastrowid:04d}'
    return insertar
