# Módulo de Periodos Académicos y Oferta Académica

**Responsable:** Dair Ramos Jacay (20232156D)
**Alcance:** Configuración y gestión de Periodos Académicos | Políticas y Fórmulas de Promedio | Planes de Estudio | Cursos, Prerrequisitos, Secciones | Asignación de Docentes | Componentes de Evaluación (Pesos)

---

## 1. Contexto del repositorio

Este módulo implementa el backend correspondiente a la gestión de periodos académicos, políticas de créditos/retiros/condiciones, y la estructuración de la oferta académica (planes de estudio, cursos, prerrequisitos, secciones, docentes asignados y componentes de evaluación) bajo el esquema multi-tenant del Sistema de Gestión Académica (SGA). 

Se conecta con los módulos de:
- **Autenticación y Tenants:** Para validar accesos (`ADMIN`, `DOCENTE`, `ALUMNO`) y resolver el `tenant_id` contextual del token JWT.
- **Matrícula:** Que consume los periodos en estado `MATRICULA`, las secciones disponibles con vacantes, los prerrequisitos de cursos y las políticas de crédito establecidas.
- **Calificaciones y Cierre:** Que consume las secciones, la asignación de docentes, las fórmulas de promedio y los componentes evaluativos configurados.

---

## 2. Alcance de implementación

### 2.1 Componentes obligatorios

| Componente | Estado | Descripción |
|------------|--------|-------------|
| Gestión de Periodos | Sí | Creación, listado y transiciones de estado de Periodos Académicos. |
| Políticas de Periodo | Sí | Configuración de políticas de crédito, condiciones, retiro, reserva y dispersión. |
| Fórmulas de Promedio | Sí | Fórmulas de cálculo de promedio por período académico. |
| Planes de Estudio | Sí | Creación de planes de estudio por tenant y activación de los mismos. |
| Cursos | Sí | Registro de cursos y asociación a planes de estudio. |
| Prerrequisitos | Sí | Configuración de restricciones de aprobación de cursos y mínimos de créditos. |
| Secciones | Sí | Creación de secciones académicas por período. |
| Asignación Docente | Sí | Asignación de profesores a secciones específicas. |
| Componentes de Evaluación | Sí | Creación y listado de criterios evaluativos con pesos asociados por sección. |

### 2.2 Elementos complementarios

| Elemento | Estado |
|----------|--------|
| Reglas de Validación de Negocio | Implementado en `domain/` |
| Pruebas Unitarias | Implementado en `tests/test_periodos_oferta.py` |
| Swagger Autodocumentado | Disponible a través de FastAPI |

---

## 3. Estructura de archivos del módulo

La implementación está distribuida en los siguientes archivos clave dentro del monorepo backend:

```
backend/app/
├── api/v1/
│   ├── periodos.py          # Endpoints de Periodo y sus Políticas/Fórmulas
│   └── oferta.py            # Endpoints de Planes, Cursos, Secciones y Evaluaciones
├── domain/
│   ├── periodo.py           # Reglas de negocio y validaciones de Periodos
│   └── oferta.py            # Reglas de negocio y validaciones de Oferta Académica
├── services/
│   ├── periodo_service.py   # Orquestación y lógica transaccional de Periodos
│   └── oferta_service.py    # Orquestación y lógica transaccional de Oferta
└── repositories/
    ├── periodo_repository.py# Consultas y escrituras SQL para Periodos y Políticas
    └── oferta_repository.py # Consultas y escrituras SQL para Oferta Académica
```

---

## 4. Endpoints REST

### 4.1 Periodos Académicos y Políticas (`api/v1/periodos.py`)

| Método | Ruta | Rol Requerido | Descripción |
|--------|------|---------------|-------------|
| POST | `/api/v1/periodos` | `ADMIN` | Crea un nuevo período académico |
| GET | `/api/v1/periodos` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista todos los períodos académicos |
| GET | `/api/v1/periodos/activo` | `ADMIN`, `DOCENTE`, `ALUMNO` | Obtiene el período académico activo actual |
| GET | `/api/v1/periodos/{periodo_id}` | `ADMIN`, `DOCENTE`, `ALUMNO` | Obtiene un período por ID |
| POST | `/api/v1/periodos/{periodo_id}/transicion` | `ADMIN` | Cambia el estado del período académico |
| POST | `/api/v1/periodos/{periodo_id}/politicas-credito` | `ADMIN` | Crea política de créditos |
| GET | `/api/v1/periodos/{periodo_id}/politicas-credito` | `ADMIN`, `ALUMNO` | Lista políticas de créditos |
| POST | `/api/v1/periodos/{periodo_id}/politicas-condicion` | `ADMIN` | Crea política de condiciones de matrícula |
| GET | `/api/v1/periodos/{periodo_id}/politicas-condicion` | `ADMIN`, `ALUMNO` | Lista políticas de condiciones |
| POST | `/api/v1/periodos/{periodo_id}/politicas-retiro` | `ADMIN` | Crea política de retiro de asignaturas |
| GET | `/api/v1/periodos/{periodo_id}/politicas-retiro` | `ADMIN`, `ALUMNO` | Lista políticas de retiro |
| POST | `/api/v1/periodos/{periodo_id}/politicas-reserva` | `ADMIN` | Crea política de reserva de matrícula |
| GET | `/api/v1/periodos/{periodo_id}/politicas-reserva` | `ADMIN`, `ALUMNO` | Obtiene política de reserva |
| POST | `/api/v1/periodos/{periodo_id}/formulas-promedio` | `ADMIN` | Agrega fórmula de promedio |
| GET | `/api/v1/periodos/{periodo_id}/formulas-promedio` | `ADMIN` | Lista las fórmulas de promedio |
| POST | `/api/v1/periodos/{periodo_id}/politicas-dispersion` | `ADMIN` | Crea política de dispersión |
| GET | `/api/v1/periodos/{periodo_id}/politicas-dispersion` | `ADMIN`, `ALUMNO` | Obtiene política de dispersión |

### 4.2 Oferta Académica (`api/v1/oferta.py`)

| Método | Ruta | Rol Requerido | Descripción |
|--------|------|---------------|-------------|
| POST | `/api/v1/oferta/planes-estudio` | `ADMIN` | Crea un nuevo plan de estudios |
| GET | `/api/v1/oferta/planes-estudio` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista los planes de estudio del tenant |
| PUT | `/api/v1/oferta/planes-estudio/{plan_id}/activar` | `ADMIN` | Activa un plan de estudios |
| POST | `/api/v1/oferta/cursos` | `ADMIN` | Crea un nuevo curso global en la institución |
| GET | `/api/v1/oferta/cursos` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista todos los cursos de la institución |
| POST | `/api/v1/oferta/planes-estudio/{plan_id}/cursos` | `ADMIN` | Asocia un curso a un plan de estudios |
| GET | `/api/v1/oferta/planes-estudio/{plan_id}/cursos` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista los cursos de un plan de estudios |
| POST | `/api/v1/oferta/cursos/{curso_id}/prerrequisitos` | `ADMIN` | Configura prerrequisito para un curso |
| POST | `/api/v1/oferta/secciones` | `ADMIN` | Crea una sección para un curso en un periodo |
| GET | `/api/v1/oferta/periodos/{periodo_id}/secciones` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista todas las secciones por periodo |
| POST | `/api/v1/oferta/secciones/{seccion_id}/docentes` | `ADMIN` | Asigna un docente a una sección académica |
| POST | `/api/v1/oferta/secciones/{seccion_id}/componentes` | `ADMIN` | Crea componente de evaluación para una sección |
| GET | `/api/v1/oferta/secciones/{seccion_id}/componentes` | `ADMIN`, `DOCENTE`, `ALUMNO` | Lista componentes de evaluación de una sección |

---

## 5. Reglas de Negocio Principales

Las validaciones de negocio críticas se encuentran aisladas en la capa de dominio:

1. **Fechas del Periodo Académico (`validar_fechas_periodo`):**
   - La fecha de inicio del periodo debe ser estrictamente anterior a la fecha de fin.
2. **Transiciones de Estado del Periodo (`validar_transicion_estado_periodo`):**
   - Los periodos académicos siguen una transición lineal estricta de estados que no puede ser alterada ni saltada:
     `CONFIGURACION` $\rightarrow$ `MATRICULA` $\rightarrow$ `REGISTRO_NOTAS` $\rightarrow$ `CERRADO`.
3. **Prerrequisitos de Asignatura (`validar_prerrequisitos`):**
   - Si el prerrequisito es de tipo `APROBACION_CURSO`, es obligatorio especificar el curso requerido.
   - Si es de tipo `MINIMO_CREDITOS`, es obligatorio que el valor de créditos mínimos sea mayor a cero.
4. **Edición de Secciones (`validar_edicion_seccion`):**
   - La creación o modificación de secciones está restringida únicamente a cuando el periodo académico se encuentra en estado `CONFIGURACION`. No se permiten cambios en periodos activos o cerrados.
5. **Componentes Evaluativos (`validar_suma_pesos_componentes`):**
   - La suma acumulada de los pesos de los componentes de evaluación configurados en una sección no puede exceder el `100.00%`.

---

## 6. Pruebas Unitarias y de Integración

Las pruebas unitarias del dominio para este módulo están codificadas en [test_periodos_oferta.py](file:///c:/Users/dair1/Downloads/Proy_SW505_2026_1_Grupo_4/sga/backend/tests/test_periodos_oferta.py) y verifican la correcta ejecución de todas las reglas de negocio descritas anteriormente.

Para correr las pruebas de este módulo, ejecuta:

```powershell
cd sga/backend
pytest tests/test_periodos_oferta.py -v
```
