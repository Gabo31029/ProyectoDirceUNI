# Módulo de Matrícula, Inscripciones y Cuentas de Seguimiento

**Responsable:** Luis Gabriel Eustaquio Avila (20240206G)  
**Alcance:** Proceso de matrícula del período | Inscripción y retiro de asignaturas | Gestión de cuentas de seguimiento de créditos

---

## 1. Contexto del módulo

Este módulo maneja la inscripción de asignaturas y la cuenta de seguimiento del estudiante bajo un esquema multi-tenant y transaccional en la Fase 1 del proyecto. A través de este módulo se garantiza que ningún estudiante se matricule en un período cerrado, exceda su límite de créditos permitido, curse asignaturas sin cumplir prerrequisitos o se inscriba en secciones sin vacantes.

---

## 2. Alcance de implementación

| Componente | Archivo / Ubicación | Estado |
|------------|---------------------|--------|
| Migraciones y Tablas SQL | `db/migrations/004_matricula_inscripciones_gabriel.sql` | Completado |
| Definición de API (Router) | `app/api/v1/matricula.py` | Completado |
| Lógica de Negocio (Servicio) | `app/services/matricula_service.py` | Completado |
| Consultas y Persistencia | `app/repositories/matricula_repository.py` | Completado |
| Reglas de Dominio puras | `app/domain/matricula.py` | Completado |
| Pruebas Unitarias (Pytest) | `tests/test_matricula.py` | Completado |
| Pruebas de Integración | `tests/integration/test_matricula_integration.py` | Completado |

---

## 3. Estructura de Base de Datos (Esquema del Módulo)

Las tablas principales asociadas al módulo son:

### 3.1 `cuenta_seguimiento_alumno`
Permite auditar y monitorear el avance del alumno acumulado en la institución.
*   `id`: UUID (Llave primaria).
*   `id_tenant`: UUID (Filtro multi-tenant).
*   `id_alumno`: UUID (Relación a `usuarios`).
*   `creditos_inscritos_periodo`: Créditos en los que está matriculado actualmente.
*   `creditos_aprobados_acumulados`: Créditos acumulados aprobados a lo largo de su carrera.

### 3.2 `matricula`
Registro general del estudiante en un período académico específico.
*   `id`: UUID (Llave primaria).
*   `id_tenant`: UUID.
*   `id_alumno`: UUID (Estudiante matriculado).
*   `id_periodo`: UUID (Periodo académico activo).
*   `estado`: `ACTIVA` | `RETIRADA` | `FINALIZADA`.
*   `creditos_matriculados`: Suma total de créditos del alumno en el período.

### 3.3 `inscripcion`
Asignaturas específicas (secciones) cursadas por el alumno en su matrícula.
*   `id`: UUID (Llave primaria).
*   `id_seccion`: UUID (Sección ofertada).
*   `id_curso`: UUID (Curso asociado).
*   `estado`: `ACTIVA` | `RETIRADA` | `APROBADA` | `DESAPROBADA` | `ANULADA`.
*   `creditos`: Créditos que aporta el curso.

---

## 4. Endpoints REST del Módulo

### Módulo: Matrícula (`/api/v1/matriculas`)

| Método | Ruta | Rol Autorizado | Descripción |
|--------|------|----------------|-------------|
| **POST** | `/api/v1/matriculas` | `ALUMNO`, `ADMIN` | Crea la matrícula inicial del alumno para el período activo. |
| **GET** | `/api/v1/matriculas` | `ALUMNO`, `ADMIN`, `DOCENTE` | Retorna el historial de matrículas del alumno. |
| **POST** | `/api/v1/matriculas/{matricula_id}/inscripciones` | `ALUMNO`, `ADMIN` | Inscribe una asignatura específica (sección) en la matrícula indicada. |
| **GET** | `/api/v1/matriculas/{matricula_id}/inscripciones` | `ALUMNO`, `ADMIN`, `DOCENTE` | Lista todas las inscripciones actuales de la matrícula. |

### Módulo: Inscripción / Retiro (`/api/v1/inscripciones`)

| Método | Ruta | Rol Autorizado | Descripción |
|--------|------|----------------|-------------|
| **POST** | `/api/v1/inscripciones/{inscripcion_id}/retiro` | `ALUMNO`, `ADMIN` | Realiza el retiro formal de una asignatura inscrita. |

---

## 5. Reglas de Negocio y Flujos Críticos

### 5.1 Flujo de Inscripción de Asignaturas
El servicio `MatriculaService.inscribir_curso` valida de forma estricta las siguientes condiciones:
1.  **Estado de Matrícula:** La matrícula del alumno debe estar en estado `ACTIVA`.
2.  **Estado del Período:** El período de la sección debe coincidir con el de la matrícula y debe encontrarse en estado `MATRICULA`.
3.  **Estado y Vacantes de la Sección:** La sección seleccionada debe estar en estado `ABIERTA` y poseer al menos 1 vacante disponible.
4.  **No Duplicidad:** El alumno no puede inscribirse en un curso en el que ya tiene una inscripción activa.
5.  **Validación de Prerrequisitos:** Se consulta la lista de prerrequisitos de la asignatura y se contrasta contra el historial de cursos aprobados del estudiante.
6.  **Límite de Créditos:** La suma de los créditos actuales matriculados más los créditos de la nueva asignatura no debe superar el tope de créditos configurado en las políticas del período académico.
7.  **Reserva Transaccional de Vacante:** La reducción de vacantes en la sección (`vacantes_disponibles = vacantes_disponibles - 1`) y la creación de la inscripción se ejecutan dentro de una transacción SQL única para prevenir sobre-inscripción por condiciones de carrera.

### 5.2 Flujo de Retiro de Asignatura
El servicio `MatriculaService.retirar_curso` ejecuta:
1.  Transición de estado de la inscripción de `ACTIVA` a `RETIRADA`.
2.  Liberación de la vacante reservada en la sección (`vacantes_disponibles = vacantes_disponibles + 1`).
3.  Descuento de créditos matriculados de la cabecera de la matrícula y de la cuenta de seguimiento.
4.  Registro en la tabla de auditoría con la justificación del retiro.

---

## 6. Pruebas y Cobertura

Las pruebas del módulo están divididas en dos niveles:

### 6.1 Pruebas Unitarias de Dominio (`tests/test_matricula.py`)
Valida de forma aislada e independiente de base de datos las reglas puras:
*   Fallo si el período no está en matrícula.
*   Fallo si la sección no cuenta con vacantes disponibles o está cerrada.
*   Fallo si existen prerrequisitos obligatorios no aprobados.
*   Fallo por exceso de créditos permitidos.

### 6.2 Pruebas de Integración (`tests/integration/test_matricula_integration.py`)
Simula llamadas reales de extremo a extremo utilizando base de datos en memoria o aislada de testing:
*   Creación exitosa de matrículas de desarrollo.
*   Concurrencia y persistencia transaccional al reservar y liberar vacantes.
*   Generación de trazas de auditoría por cada evento del flujo.

Para ejecutar las pruebas del módulo localmente:
```bash
cd sga/backend
.venv/bin/pytest tests/test_matricula.py tests/integration/test_matricula_integration.py -v
```
