
"""Fase 7: verificación de BUG-INI-02."""

from src.db.conexion import (
    cerrar_conexion,
    configurar_ruta_base_datos,
)
from src.db.inicializador import inicializar_base_datos


def test_bug_ini02_ruta_invalida(tmp_path):
    # Crear un archivo que simula una carpeta.
    archivo = tmp_path / "archivo.txt"
    archivo.write_text("No soy una carpeta", encoding="utf-8")

    # Intentar crear la base de datos dentro de ese archivo.
    ruta_invalida = archivo / "prueba.db"

    cerrar_conexion()

    try:
        configurar_ruta_base_datos(ruta_invalida)

        # La aplicación debe controlar el error.
        resultado = inicializar_base_datos()

        assert resultado.exito is False
        assert resultado.mensaje
        assert "No fue posible inicializar" in resultado.mensaje

        # No debe crearse una base de datos.
        assert not ruta_invalida.exists()

    finally:
        cerrar_conexion()