from sqlalchemy import create_engine, text

from app.core.security import hash_password

url = "postgresql+psycopg2://postgres.agtztalpzszaseczsnzf:construccion123@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
engine = create_engine(url, connect_args={"sslmode": "require"})
tid = "f1111111-1111-1111-1111-111111111111"
aid = "f2222222-2222-2222-2222-222222222222"
pid = "f3333333-3333-3333-3333-333333333333"
plan = "f4444444-4444-4444-4444-444444444444"
pwd = hash_password("x")

with engine.begin() as conn:
    for sql in [
        "DELETE FROM inscripcion WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM matricula WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM cuenta_seguimiento_alumno WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM perfil_alumno WHERE id_usuario = CAST(:aid AS uuid)",
        "DELETE FROM plan_estudios WHERE id_tenant = CAST(:tid AS uuid)",
        "DELETE FROM usuario WHERE id_usuario = CAST(:aid AS uuid)",
        "DELETE FROM usuarios WHERE id = CAST(:aid AS uuid)",
        "DELETE FROM tenants WHERE id = CAST(:tid AS uuid)",
    ]:
        conn.execute(text(sql), {"tid": tid, "aid": aid})

    conn.execute(
        text(
            """
            INSERT INTO tenants (id, id_tenant, nombre, dominio, zona_horaria, estado)
            VALUES (CAST(:tid AS uuid), CAST(:tid AS uuid), 'Tenant', 'uni-int', 'America/Lima', 'ACTIVO')
            """
        ),
        {"tid": tid},
    )
    print("tenant:", conn.execute(text("SELECT id, id_tenant FROM tenants WHERE id = CAST(:tid AS uuid)"), {"tid": tid}).fetchone())

    conn.execute(
        text(
            """
            INSERT INTO usuarios (id, id_tenant, email, password_hash, nombre, apellido, rol, activo)
            VALUES (CAST(:aid AS uuid), CAST(:tid AS uuid), 'a@t.l', :pwd, 'A', 'B', 'ALUMNO', TRUE)
            """
        ),
        {"aid": aid, "tid": tid, "pwd": pwd},
    )
    conn.execute(
        text(
            """
            INSERT INTO usuario (id_usuario, id_tenant, nombre_completo, email, password_hash, rol)
            VALUES (CAST(:aid AS uuid), CAST(:tid AS uuid), 'AB', 'a@t.l', :pwd, 'ALUMNO')
            """
        ),
        {"aid": aid, "tid": tid, "pwd": pwd},
    )
    conn.execute(
        text(
            """
            INSERT INTO plan_estudios (id, id_tenant, carrera, version_plan, creditos_totales, estado)
            VALUES (CAST(:plan AS uuid), CAST(:tid AS uuid), 'Ing', 'v1', 120, 'ACTIVO')
            """
        ),
        {"plan": plan, "tid": tid},
    )
    conn.execute(
        text(
            """
            INSERT INTO perfil_alumno (
                id_perfil_alumno, id_usuario, id_plan_estudios, codigo_alumno, carrera, periodo_ingreso
            ) VALUES (
                CAST(:aid AS uuid), CAST(:aid AS uuid), CAST(:plan AS uuid), '001', 'Ing', '2026-1'
            )
            """
        ),
        {"aid": aid, "plan": plan},
    )
    conn.execute(
        text(
            "INSERT INTO matricula (id_tenant, id_alumno, id_periodo) VALUES (CAST(:tid AS uuid), CAST(:aid AS uuid), CAST(:pid AS uuid))"
        ),
        {"tid": tid, "aid": aid, "pid": pid},
    )
    print("matricula OK")
    conn.execute(
        text(
            "INSERT INTO cuenta_seguimiento_alumno (id_tenant, id_alumno, creditos_inscritos_periodo) VALUES (CAST(:tid AS uuid), CAST(:aid AS uuid), 0)"
        ),
        {"tid": tid, "aid": aid},
    )
    print("cuenta OK")
