import os
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_db():
    db_url = "postgresql://postgres.agtztalpzszaseczsnzf:construccion123@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
    print(f"Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check tables in schema
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND (table_name LIKE '%componente%' OR table_name LIKE '%evaluacion%');
        """)
        tables = cur.fetchall()
        print("\n=== Found matching tables ===")
        for t in tables:
            print(f"- {t[0]}")
            
        for t_name in ["cat_tipo_componente", "cat_tipo_evaluacion", "tipo_componente", "tipo_evaluacion"]:
            try:
                cur.execute(f"SELECT * FROM {t_name} LIMIT 1;")
                cols = [desc[0] for desc in cur.description]
                print(f"\nTable '{t_name}' exists. Columns: {cols}")
            except Exception as e:
                print(f"\nTable '{t_name}' check failed: {e}")
                conn.rollback()
                
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    test_db()
