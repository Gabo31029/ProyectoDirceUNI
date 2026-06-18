# Modulo Auth, Tenant y Usuarios

**Responsable:** Leonardo Gabriel Chavez Miranda (20240110J)  
**Alcance:** Autenticacion y gestion de sesion | Gestion institucional (Tenant) | Gestion de usuarios (Fase 1)

---

## 1. Contexto del repositorio

En la rama `main` del repositorio remoto se encuentran actualmente:

- Documentos en `Entregables/`
- `README.md`

A la fecha de este documento, no hay codigo backend ni frontend versionado, ni ramas `develop` o `feature/*` creadas. La implementacion del directorio `backend/` corresponde a la Fase 1 del plan de implementacion (Semana 9).

Este modulo incluye, ademas de los tres componentes funcionales asignados, la base compartida requerida por el plan:

- Estructura del monorepo en `backend/`
- Docker Compose y PostgreSQL local
- `db/schema.sql`
- Capa `core/` (configuracion, JWT, middleware de tenant)
- Endpoint de health check
- `.gitignore` y `.env.example`

---

## 2. Alcance de implementacion

### 2.1 Componentes obligatorios (Plan de Implementacion)

| Componente | Incluido en `backend/` |
|------------|------------------------|
| Estructura monorepo `backend/` | Si |
| Docker Compose + PostgreSQL local | Si |
| `schema.sql` (Auth, Tenant, Usuarios) | Si |
| `core/` (config, JWT, middleware tenant) | Si |
| API, servicios y repositorios del modulo | Si (base funcional) |
| `.gitignore` + `.env.example` | Si |

### 2.2 Elementos complementarios

| Elemento | Estado |
|----------|--------|
| Endpoints REST del modulo | Base implementada; requiere pruebas y ajustes |
| Seed de usuarios de desarrollo | Implementado |
| Pruebas con pytest | Parcial |
| GitHub Actions (CI) | Configurado en `.github/workflows/backend-tests.yml` |
| Este documento | Guia de referencia del modulo |

### 2.3 Pendientes de cierre

- Cobertura de pruebas al 80% en validaciones criticas (RNF-MAN-03)
- Conexion a Supabase en entorno cloud (`DATABASE_URL`)
- Integracion real con Oferta Academica para RF-USR-04
- Seed de catalogos base al registrar un tenant
- Validacion end-to-end con Docker o Python 3.12

---

## 3. Requisitos del entorno local

- **Python 3.12** (version definida en el plan; versiones superiores pueden fallar al instalar dependencias)
- **Docker Desktop** (recomendado) o PostgreSQL 15 / Supabase

```powershell
cd backend
copy .env.example .env
docker compose up --build
```

| Recurso | URL |
|---------|-----|
| API | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| Health check | http://localhost:8000/health |

### Credenciales de desarrollo (seed)

| Rol | Email | Password | Dominio tenant |
|-----|-------|----------|----------------|
| Admin Central | admin.central@sga.local | AdminCentral123! | — |
| Admin Demo | admin@uni-demo.local | AdminDemo123! | uni-demo |

---

## 4. Estructura de archivos del modulo

```
backend/app/
├── api/v1/
│   ├── auth.py          # RF-USR-01, RNF-SEG-02
│   ├── tenants.py       # RF-TNT-01, RF-TNT-02
│   └── users.py         # RF-USR-03, RF-USR-04
├── domain/
│   ├── auth.py
│   ├── tenant.py
│   └── users.py         # Reglas de negocio (RNF-MAN-01)
├── services/
│   ├── auth_service.py
│   ├── tenant_service.py
│   └── user_service.py
├── repositories/
│   ├── auth_repository.py
│   ├── tenant_repository.py
│   ├── user_repository.py
│   └── audit_repository.py
└── core/
    ├── dependencies.py  # JWT, RBAC, contexto de tenant (RF-TNT-03)
    └── security.py
```

---

## 5. Modulos fuera de alcance e integraciones

| Integrante | Modulo | Punto de integracion |
|------------|--------|----------------------|
| Ramos Jacay | Periodos, Oferta Academica | `app/interfaces/oferta_academica.py` |
| Eustaquio Avila | Matricula, Cuentas de Seguimiento | Capa `core/` (JWT, tenant) |
| Paucar Ventura | Calificaciones, Cierre, Historial | Capa `core/` (JWT, tenant) |
| Chupa Ballesteros | Frontend, Auditoria, Reportes | Endpoints `/api/v1/auth/*` |

El archivo `app/interfaces/oferta_academica.py` expone un stub (`OfertaAcademicaStub`) para RF-USR-04 hasta la entrega del modulo de Oferta Academica.

---

## 6. Endpoints REST

### Autenticacion

| Metodo | Ruta |
|--------|------|
| POST | `/api/v1/auth/login` |
| POST | `/api/v1/auth/logout` |
| GET | `/api/v1/auth/me` |

### Tenants (rol Admin Central)

| Metodo | Ruta |
|--------|------|
| GET, POST | `/api/v1/tenants` |
| PUT | `/api/v1/tenants/{id}` |
| POST, GET | `/api/v1/tenants/{id}/catalogos/*` |

### Usuarios (rol Admin / Admin Central)

| Metodo | Ruta | Notas |
|--------|------|-------|
| GET, POST | `/api/v1/usuarios` | Query `tenant_id` requerido para Admin Central |
| PUT | `/api/v1/usuarios/{id}` | |
| PATCH | `/api/v1/usuarios/{id}/desactivar` | |

---

## 7. Reglas arquitectonicas

1. El `id_tenant` no se recibe en el body del request; se obtiene del JWT (RF-TNT-03).
2. Las reglas de negocio residen en `domain/`, no en routers ni en SQL directo.
3. El frontend no accede a Supabase; toda operacion pasa por esta API.
4. Los mensajes de error se devuelven en espanol, sin trazas internas (RNF-USA-02).

---

## 8. Pruebas

```powershell
cd backend
pip install -r requirements.txt
pytest tests/test_domain.py -v

# Pruebas de integracion (requiere base de datos activa):
$env:RUN_INTEGRATION_TESTS="1"
pytest -v
```

---

## 9. Control de versiones

Modelo de ramas segun el Plan de Implementacion: `main` → `develop` → `feature/*`.

Si la rama `develop` aun no existe en el remoto, se recomienda crearla a partir de `main` antes de abrir pull requests del modulo:

```bash
git checkout main
git pull
git checkout -b develop
git push -u origin develop

git checkout -b feature/auth-tenant-usuarios
git push -u origin feature/auth-tenant-usuarios
# Pull request: feature/auth-tenant-usuarios -> develop
```

### Archivos que no deben versionarse

- `backend/.env` (variables y secretos locales)

### Archivos que si deben versionarse

- `.env.example`
- Codigo fuente del modulo
- `db/schema.sql`

### Convencion de commits (Conventional Commits)

```
feat(auth): implementar login JWT con contexto de tenant
feat(tenant): CRUD de tenants RF-TNT-01
test(auth): pruebas de bloqueo por intentos fallidos
```
