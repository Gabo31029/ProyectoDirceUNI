import os
import sys
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import db

async def main():
    await db.connect()
    try:
        async with db.connection().acquire() as conn:
            print("--- EVALUACIONES ACADEMICAS (CON JOIN) ---")
            rows = await conn.fetch("""
                SELECT ea.id, ea.id_seccion, ea.id_tipo_evaluacion, ea.peso_relativo, ea.estado,
                       cte.nombre AS nombre_tipo_evaluacion
                FROM evaluacion_academica ea
                LEFT JOIN cat_tipo_evaluacion cte ON ea.id_tipo_evaluacion = cte.id
            """)
            for row in rows:
                print(dict(row))
                
            print("\n--- CAT_TIPO_EVALUACION ---")
            rows = await conn.fetch("SELECT id, codigo, nombre FROM cat_tipo_evaluacion")
            for row in rows:
                print(dict(row))
    finally:
        await db.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
