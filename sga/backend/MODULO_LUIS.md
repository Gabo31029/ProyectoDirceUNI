# Módulo Ciclo de Vida Académico (Gestión de Calificaciones, Cierre y Historial)

**Responsable:** Luis Paucar Ventura (Grupo 4)  
**Alcance:** Gestión de Calificaciones | Cierre Académico (Actas y Períodos) | Historial Académico (Consolidación y PDF)

---

## 1. Contexto del módulo

Este módulo implementa el núcleo académico del sistema SGA Multitenant, encargándose de la gestión y publicación de calificaciones, el cálculo automático de notas finales, PPS y PPA, la auditoría e inmutabilidad de los eventos académicos, el procesamiento batch de cierre de períodos y la generación del récord oficial de notas en PDF.

La implementación se encuentra en el directorio `sga/backend/` en la rama `feature/academic-lifecycle` y está completamente integrada con la base compartida y autenticación de la plataforma.

---

## 2. Alcance de implementación

### 2.1 Componentes obligatorios (Plan de Implementación)

| Componente | Incluido en `backend/` |
|------------|------------------------|
| Gestión de Calificaciones (Registros y Publicación) | Sí |
| Aprobación de Correcciones Administrativas | Sí |
| Cierre de Acta de Sección (Cálculo Ponderado Final) | Sí |
| Cierre de Período Académico (Procesamiento por lote) | Sí |
| Historial Académico Consolidado (JSON) | Sí |
| Generación de Récord Oficial en PDF (fpdf2) | Sí |
| Sistema Transversal de Auditoría y Eventos | Sí |

### 2.2 Elementos complementarios

| Elemento | Estado |
|----------|--------|
| Endpoints REST del módulo | 100% Funcionales e Integrados |
| Pruebas unitarias y de integración (pytest) | Suite de 23 pruebas aprobadas |
| Base de datos local | SQLite local autogenerada y seed de prueba para testing |
| Este documento | Guía de referencia del módulo del Ciclo de Vida Académico |

---

## 3. Requisitos del entorno local

El módulo está diseñado para correr en el entorno de desarrollo utilizando SQLite local de manera transparente o la base de datos PostgreSQL/Supabase en producción.

### Ejecución de Pruebas y Servidor
Puedes utilizar el script interactivo del backend para inicializar las tablas de base de datos, poblar datos de prueba (seed) y levantar el servidor:

```powershell
cd sga\backend
.\install_and_run.ps1
```
*Selecciona la opción `3` para ejecutar los tests de pytest y luego levantar el servidor FastAPI.*

Alternativamente, el servidor de tu módulo se levanta directamente con:
```powershell
py -m uvicorn app.api.main:app --reload --port 8000
```

| Recurso | URL |
|---------|-----|
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |

---

## 4. Estructura de archivos del módulo

La organización del código sigue una arquitectura limpia (Clean Architecture) orientada al dominio (DDD):

```
sga/backend/app/
├── core/
│   ├── db.py                 # Engine y SessionLocal de SQLAlchemy
│   ├── security.py           # Extracción de CurrentUser y RBAC (Roles)
│   └── audit.py              # Log de auditoría e inmutabilidad de eventos
├── models/
│   ├── base.py               # Declaración Base de SQLAlchemy
│   ├── core_schemas.py       # Dependencias y tablas transversales compartidas
│   ├── calificacion.py       # Tablas de Calificaciones y Correcciones
│   ├── cierre.py             # Tablas de Snapshots de promedios y Condiciones Académicas
│   └── seguimiento.py        # Cuentas de seguimiento y log de eventos
├── domain/
│   ├── calificacion.py       # Validación de escalas de notas y máquina de estados del acta
│   └── cierre.py             # Fórmulas de promedio PPS/PPA y lógica de condiciones de riesgo
│                             # Nota: domain/historial.py no se requiere debido a que el
│                             # historial es una vista de solo lectura sin lógica transaccional.
├── repositories/
│   ├── base.py               # CRUD genérico BaseRepository
│   ├── calificacion.py       # Consultas SQL para ingreso y correcciones de notas
│   ├── cierre.py             # Consultas de cierre, snapshots y políticas
│   └── historial.py          # Consultas optimizadas con JOINS para récord académico
├── services/
│   ├── calificacion.py       # Casos de uso de registro de notas, publicación y corrección
│   ├── cierre.py             # Casos de uso de cierre de actas y cierres de períodos en lote
│   └── historial.py          # Casos de uso de compilación del historial y exportación a PDF
└── api/
    ├── main.py               # Inicializador de la aplicación FastAPI del módulo
    ├── calificaciones.py     # Rutas de calificaciones y correcciones
    ├── cierre.py             # Rutas de cierre de sección y período
    └── historial.py          # Rutas de descarga de PDF e historial JSON
```

---

## 5. Módulos fuera de alcance e integraciones

* **Autenticación y Usuarios:** Consume los tokens JWT emitidos por el módulo de autenticación para obtener el rol, ID del tenant e ID del usuario logueado.
* **Periodos y Ofertas Académicas:** Se consume de manera de solo lectura la información de secciones, cursos, créditos y asignaciones para validar que solo docentes con asignación activa puedan calificar y cerrar actas de su respectiva sección.

---

## 6. Endpoints REST Implementados

### Gestión de Calificaciones

| Método | Ruta | Descripción | Rol Mínimo |
|--------|------|-------------|------------|
| POST | `/calificaciones/secciones/{id_seccion}/componentes/{id_componente}` | Registra notas en borrador | DOCENTE / ADMIN |
| PUT | `/calificaciones/secciones/{id_seccion}/componentes/{id_componente}/publicar` | Publica las notas de un componente | DOCENTE (coord) / ADMIN |
| POST | `/calificaciones/{id_calificacion}/corregir` | Registra y aprueba una corrección administrativa | ADMIN |

### Cierre Académico

| Método | Ruta | Descripción | Rol Mínimo |
|--------|------|-------------|------------|
| POST | `/cierre/secciones/{id_seccion}/cerrar-acta` | Cierra el acta e inmutable las notas finales | DOCENTE (coord) / ADMIN |
| POST | `/cierre/periodos/{id_periodo}/cerrar` | Cierre batch total del período académico | ADMIN |

### Historial Académico

| Método | Ruta | Descripción | Rol Mínimo |
|--------|------|-------------|------------|
| GET | `/historial/alumnos/{id_perfil_alumno}` | Obtiene el historial consolidado en JSON | ALUMNO / DOCENTE / ADMIN |
| GET | `/historial/alumnos/{id_perfil_alumno}/pdf` | Descarga el récord oficial de notas en PDF | ALUMNO / ADMIN |

---

## 7. Reglas Arquitectónicas y del Dominio (DDD)

1. **Aislamiento Multitenant:** En ningún endpoint de registro se solicita el `id_tenant` en el cuerpo de la petición. Este parámetro se extrae de forma automática y segura desde el token JWT para garantizar la segregación de datos.
2. **Máquina de Estados de Acta:** Las calificaciones pasan por los estados `BORRADOR` -> `PUBLICADO` -> `CERRADO`. No se permite registrar calificaciones si el componente ya fue publicado o el acta cerrada.
3. **Consistencia en Transacciones:** Los cierres de actas y períodos se ejecutan dentro de transacciones de base de datos (`db.commit()`), garantizando consistencia fuerte y registrando eventos históricos de manera atómica.
4. **Tratamiento del Historial Académico:** Al ser una vista puramente de lectura (Query / Reporte), no tiene entidad ni lógica de modificación propia en `domain/`. Su código está encapsulado óptimamente en `repositories/` y `services/`.

---

## 8. Pruebas

Para validar el correcto funcionamiento del dominio, base de datos y flujos, ejecuta la suite de pytest desde el directorio backend:

```powershell
cd sga\backend
py -m pytest tests/test_academic_lifecycle.py -v
```

### Cobertura de Pruebas
Las pruebas cubren:
* **`TestValidateGradeValue`**: Validación de límites y escalas vigesimales o porcentuales.
* **`TestCalcNotaFinal`**: Cálculo matemático ponderado exacto y validación de suma de pesos (100%).
* **`TestCalcPromediosPonderados`**: Fórmulas de promedios PPS/PPA aplicando reglas de inclusión (TODOS, ULTIMO, SOLO_APROBADOS).
* **`TestEvaluarPolitica`**: Evaluación de comparaciones lógicas para condiciones de riesgo.
* **`TestDatabaseModels`**: Inicialización correcta de esquemas y tablas de base de datos SQLite.
