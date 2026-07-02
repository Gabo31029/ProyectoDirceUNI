"""
Pruebas del módulo de Ciclo de Vida Académico.

Cubre:
  - Validaciones de dominio (calificaciones y cálculo de promedios)
  - Creación de tablas y entidades básicas en SQLite in-memory
"""
import pytest
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import declarative Base
from app.models.base import Base

# Import all models to register them with Base.metadata
import app.models.core_schemas   # noqa: F401
import app.models.calificacion    # noqa: F401
import app.models.cierre          # noqa: F401
import app.models.seguimiento     # noqa: F401

from app.models.core_schemas import Tenant, EscalaEvaluacion, PeriodoAcademico
from app.domain.calificacion import validate_grade_value, GradeDomainError
from app.domain.cierre import (
    calcular_nota_final,
    calcular_promedio_ponderado,
    evaluar_politica_condicion,
    CierreDomainError
)


# ─────────────────────────────────────────────────────────────────────────────
# DOMAIN UNIT TESTS
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateGradeValue:
    def test_valid_boundary_values(self):
        validate_grade_value(0, 0, 20)       # minimum
        validate_grade_value(20, 0, 20)      # maximum
        validate_grade_value(14.5, 0, 20)    # mid-range

    def test_valid_0_to_100_scale(self):
        validate_grade_value(0, 0, 100)
        validate_grade_value(100, 0, 100)
        validate_grade_value(72.5, 0, 100)

    def test_above_max_raises(self):
        with pytest.raises(GradeDomainError):
            validate_grade_value(21, 0, 20)

    def test_below_min_raises(self):
        with pytest.raises(GradeDomainError):
            validate_grade_value(-0.01, 0, 20)

    def test_exact_max_is_valid(self):
        validate_grade_value(20, 0, 20)   # should not raise


class TestCalcNotaFinal:
    def test_equal_weights(self):
        calificaciones = [
            {"valor_nota": Decimal("15.00"), "peso_relativo": Decimal("50.00")},
            {"valor_nota": Decimal("13.00"), "peso_relativo": Decimal("50.00")},
        ]
        assert calcular_nota_final(calificaciones) == Decimal("14.00")

    def test_three_component_weights(self):
        calificaciones = [
            {"valor_nota": Decimal("12.00"), "peso_relativo": Decimal("30.00")},
            {"valor_nota": Decimal("16.00"), "peso_relativo": Decimal("30.00")},
            {"valor_nota": Decimal("14.00"), "peso_relativo": Decimal("40.00")},
        ]
        # (12*0.30) + (16*0.30) + (14*0.40) = 3.60 + 4.80 + 5.60 = 14.00
        assert calcular_nota_final(calificaciones) == Decimal("14.00")

    def test_weights_not_100_raises(self):
        calificaciones = [
            {"valor_nota": Decimal("15.00"), "peso_relativo": Decimal("40.00")},
            {"valor_nota": Decimal("15.00"), "peso_relativo": Decimal("40.00")},
        ]
        with pytest.raises(CierreDomainError):
            calcular_nota_final(calificaciones)

    def test_empty_list_returns_zero(self):
        assert calcular_nota_final([]) == Decimal("0.00")


class TestCalcPromediosPonderados:
    def _make_inscriptions(self):
        return [
            {"codigo_curso": "INF01", "creditos": 4, "nota_final": Decimal("15.00"),
             "estado": "APROBADA", "fecha_orden": 1},
            {"codigo_curso": "MAT01", "creditos": 5, "nota_final": Decimal("10.00"),
             "estado": "DESAPROBADA", "fecha_orden": 1},
        ]

    def test_todos_includes_failed(self):
        ins = self._make_inscriptions()
        # (15*4 + 10*5) / 9 = 110/9 ≈ 12.22
        result = calcular_promedio_ponderado(ins, "TODOS")
        assert result == Decimal("12.22")

    def test_solo_aprobados(self):
        ins = self._make_inscriptions()
        # Only INF01 (15, 4 creditos): 15.00
        assert calcular_promedio_ponderado(ins, "SOLO_APROBADOS") == Decimal("15.00")

    def test_ultimo_keeps_latest_attempt(self):
        ins = [
            {"codigo_curso": "INF01", "creditos": 4, "nota_final": Decimal("15.00"),
             "estado": "APROBADA", "fecha_orden": 1},
            {"codigo_curso": "MAT01", "creditos": 5, "nota_final": Decimal("10.00"),
             "estado": "DESAPROBADA", "fecha_orden": 1},
            # Retake of MAT01 — higher date_order, should replace the failed one
            {"codigo_curso": "MAT01", "creditos": 5, "nota_final": Decimal("16.00"),
             "estado": "APROBADA", "fecha_orden": 2},
        ]
        # INF01(15,4) + MAT01(16,5) → (60+80)/9 = 140/9 ≈ 15.56
        result = calcular_promedio_ponderado(ins, "ULTIMO")
        assert result == Decimal("15.56")

    def test_empty_list_returns_zero(self):
        assert calcular_promedio_ponderado([], "TODOS") == Decimal("0.00")

    def test_only_active_entries_excluded(self):
        ins = [
            {"codigo_curso": "INF01", "creditos": 4, "nota_final": None,
             "estado": "ACTIVA", "fecha_orden": 1},
        ]
        assert calcular_promedio_ponderado(ins, "TODOS") == Decimal("0.00")


class TestEvaluarPolitica:
    def test_mayor_que(self):
        assert evaluar_politica_condicion(3, 2, "MAYOR_QUE") is True
        assert evaluar_politica_condicion(2, 2, "MAYOR_QUE") is False

    def test_mayor_igual(self):
        assert evaluar_politica_condicion(2, 2, "MAYOR_IGUAL") is True
        assert evaluar_politica_condicion(1, 2, "MAYOR_IGUAL") is False

    def test_igual(self):
        assert evaluar_politica_condicion(5, 5, "IGUAL") is True
        assert evaluar_politica_condicion(4, 5, "IGUAL") is False

    def test_menor_igual(self):
        assert evaluar_politica_condicion(2, 3, "MENOR_IGUAL") is True
        assert evaluar_politica_condicion(4, 3, "MENOR_IGUAL") is False

    def test_menor_que(self):
        assert evaluar_politica_condicion(1, 2, "MENOR_QUE") is True
        assert evaluar_politica_condicion(2, 2, "MENOR_QUE") is False

    def test_invalid_operator_raises(self):
        with pytest.raises(CierreDomainError):
            evaluar_politica_condicion(1, 2, "DISTINTO_DE")


# ─────────────────────────────────────────────────────────────────────────────
# DATABASE INTEGRATION TESTS (SQLite in-memory)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def db_session():
    """Creates an in-memory SQLite database and provides a session for testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False}
    )
    # SQLite does not enforce RESTRICT FK, but we still test the ORM mapping
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        yield db
        db.rollback()
    finally:
        db.close()


class TestDatabaseModels:
    def test_create_tenant(self, db_session):
        tenant = Tenant(
            id_tenant="t-1",
            nombre="Universidad Nacional",
            dominio="uni.edu.pe",
            zona_horaria="America/Lima"
        )
        db_session.add(tenant)
        db_session.flush()
        fetched = db_session.query(Tenant).filter_by(id_tenant="t-1").first()
        assert fetched is not None
        assert fetched.dominio == "uni.edu.pe"

    def test_create_escala_evaluacion(self, db_session):
        tenant = Tenant(id_tenant="t-2", nombre="UNIV 2",
                        dominio="univ2.edu.pe", zona_horaria="America/Lima")
        db_session.add(tenant)
        db_session.flush()

        escala = EscalaEvaluacion(
            id_escala="e-1",
            id_tenant="t-2",
            nombre_escala="Vigesimal",
            nota_minima=Decimal("0.00"),
            nota_maxima=Decimal("20.00"),
            nota_aprobatoria=Decimal("10.50")
        )
        db_session.add(escala)
        db_session.flush()

        fetched = db_session.query(EscalaEvaluacion).filter_by(id_escala="e-1").first()
        assert fetched is not None
        assert fetched.nota_aprobatoria == Decimal("10.50")
        assert fetched.nota_minima == Decimal("0.00")

    def test_base_metadata_includes_all_tables(self, db_session):
        """All expected tables should be registered in SQLAlchemy metadata."""
        expected_tables = {
            "tenants", "usuario", "perfil_alumno", "perfil_docente",
            "periodo_academico", "curso", "seccion", "inscripcion", "matricula",
            "evaluacion_academica", "calificacion", "correccion_nota",
            "snapshot_promedio", "condicion_academica_alumno",
            "politica_condicion_academica", "formula_promedio",
            "cuenta_seguimiento_alumno", "evento_academico", "registro_auditoria",
        }
        registered = set(Base.metadata.tables.keys())
        missing = expected_tables - registered
        assert not missing, f"Tablas faltantes en metadata: {missing}"
