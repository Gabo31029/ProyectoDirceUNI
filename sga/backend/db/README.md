# Base de datos SGA — trabajo en equipo

Cada integrante puede **crear su propio proyecto Supabase**, aplicar el esquema y **editar solo el SQL de su módulo** sin pisar el de los demás.

## 1. Supabase propio (recomendado)

1. Crear proyecto gratis en [supabase.com](https://supabase.com).
2. En `backend/.env` (no subir a Git):

   ```env
   SUPABASE_PROJECT_REF=<tu Reference ID>
   DATABASE_PASSWORD=<tu database password>
   DATABASE_URL=
   ```

3. No hace falta compartir `anon` ni `service_role`: el backend solo usa Postgres.

Así cada uno tiene su BD aislada para desarrollo y pruebas Thunder/pytest.

## 2. Estructura de migraciones

| Archivo | Módulo | Dueño habitual |
|---------|--------|----------------|
| `migrations/001_auth_tenant_leonardo.sql` | Auth, tenant, usuarios | Leonardo |
| `migrations/002_periodos_politicas_ramos.sql` | Periodos y políticas | Dair Ramos |
| `migrations/003_oferta_academica_ramos.sql` | Oferta académica | Dair Ramos |
| `migrations/004_matricula_inscripciones_gabriel.sql` | Matrícula e inscripciones | Gabriel |

- **Nuevo módulo:** copiar `_TEMPLATE_nuevo_modulo.sql` → `005_calificaciones_fulano.sql` (siguiente número libre).
- **Cambio en tablas ya mergeadas:** preferir un archivo nuevo `006_alter_matricula_columna_x.sql` con `ALTER TABLE ...` en lugar de reescribir `004` en la BD compartida de staging.

`schema.sql` se **regenera** (no se edita a mano):

```bash
cd sga/backend/db
chmod +x build_schema.sh
./build_schema.sh
```

Incluir en el PR: tu archivo en `migrations/` + `schema.sql` regenerado si cambió el esquema global.

## 3. Primera vez en tu Supabase

**Opción A — SQL Editor (más simple)**

1. Supabase → **SQL** → **New query**.
2. Pegar el contenido de `db/schema.sql` (o cada `migrations/00X_*.sql` en orden 001 → 004).
3. **Run**.

**Opción B — Terminal** (si tienes `psql` y la connection string del dashboard):

```bash
cd sga/backend
psql "<URI del pooler o direct>" -f db/schema.sql
```

Al levantar el backend, `app/db/seed.py` crea usuarios demo (`uni-demo`) si `ENVIRONMENT=development`.

## 4. Solo actualizar tu módulo

Si ya tienes 001–003 aplicados y solo falta matrícula:

1. Abrir `migrations/004_matricula_inscripciones_gabriel.sql`.
2. Ejecutar **solo ese archivo** en el SQL Editor.

Si cambias tablas existentes en producción/staging compartido, usa un archivo `00N_alter_...sql` nuevo y avisa al equipo.

## 5. Reglas del equipo

1. **Un archivo por módulo** (o por cambio incremental numerado).
2. **No renombrar** migraciones ya en `main`/`dev`.
3. **FKs:** respetar orden 001 → 002 → 003 → 004 → tus 005+.
4. **`.env` personal:** cada quien con su `SUPABASE_PROJECT_REF` + `DATABASE_PASSWORD`.
5. **Supabase compartido (opcional staging):** solo ejecutar archivos nuevos que aún no estén en esa BD; coordinar en el grupo.

## 6. Dependencias entre módulos

```
001 tenants, usuarios
  └── 002 periodo_academico
        └── 003 curso, seccion
              └── 004 matricula, inscripcion
```

Antes de probar matrícula necesitas al menos 001 + 002 + 003 en tu Supabase.
