import sys
import os

# Asegurar que el entorno reconozca la app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.reporte_service import ReporteService
import traceback

app = create_app()

with app.app_context():
    print("--- Test Inventario ---")
    try:
        data_inv = ReporteService.get_datos_inventario()
        print(f"Total Inventario: {len(data_inv)}")
        if data_inv:
            print(data_inv[0])
    except Exception as e:
        print("Error en Inventario:")
        traceback.print_exc()

    print("\n--- Test Rentabilidad ---")
    try:
        data_rent = ReporteService.get_datos_rentabilidad(None, None)
        print(f"Total Rentabilidad: {len(data_rent)}")
        if data_rent:
            print(data_rent[0])
    except Exception as e:
        print("Error en Rentabilidad:")
        traceback.print_exc()
