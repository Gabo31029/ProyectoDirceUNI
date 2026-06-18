from typing import List, Dict, Any, Union
from decimal import Decimal, ROUND_HALF_UP

class CierreDomainError(Exception):
    """
    Excepción lanzada para errores relacionados con los cálculos de promedios,
    ponderaciones y validación de políticas durante el cierre académico.
    """
    pass

def redondear_nota(val: Decimal) -> Decimal:
    """
    Realiza el redondeo estándar de calificaciones a dos decimales
    utilizando el método ROUND_HALF_UP (redondeo simétrico al más cercano,
    donde el 5 media hacia arriba, por ejemplo: 14.565 -> 14.57).
    """
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calcular_nota_final(calificaciones: List[Dict[str, Any]]) -> Decimal:
    """
    Calcula la nota final de una asignatura ponderando las notas obtenidas en cada componente.

    Parámetros:
    - calificaciones: Lista de diccionarios, donde cada uno debe contener:
        * 'valor_nota': Calificación obtenida en el componente (Decimal).
        * 'peso_relativo': Peso relativo o porcentaje del componente (Decimal).

    Reglas de negocio:
    - La suma de los pesos de todos los componentes debe ser exactamente igual a 100.00%.
    - Aplica la fórmula: Sumatoria(Nota_i * (Peso_i / 100)).
    - El resultado final se redondea a dos decimales.
    """
    if not calificaciones:
        return Decimal("0.00")
        
    total_peso = sum(Decimal(str(c["peso_relativo"])) for c in calificaciones)
    if total_peso != Decimal("100.00"):
        raise CierreDomainError(f"La suma de pesos de los componentes debe ser exactamente 100, pero es {total_peso}.")
        
    nota_acumulada = sum(
        Decimal(str(c["valor_nota"])) * (Decimal(str(c["peso_relativo"])) / Decimal("100.00"))
        for c in calificaciones
    )
    return redondear_nota(nota_acumulada)

def calcular_promedio_ponderado(
    inscripciones: List[Dict[str, Any]], 
    regla_inclusion: str = "TODOS"
) -> Decimal:
    """
    Calcula el promedio ponderado (PPS o PPA) en base a un listado de inscripciones de cursos.

    Parámetros:
    - inscripciones: Lista de diccionarios que representan cursos cursados, con las llaves:
        * 'codigo_curso': Identificador único de la asignatura (str).
        * 'creditos': Número de créditos académicos del curso (int o Decimal).
        * 'nota_final': Nota final obtenida en el curso (Decimal).
        * 'estado': Estado del curso ('APROBADA', 'DESAPROBADA', etc.).
        * 'fecha_orden': Criterio temporal para ordenar los intentos en el mismo curso.
    - regla_inclusion: Regla que define cuáles asignaturas entran en el promedio:
        * TODOS: Considera todos los cursos finalizados con nota (aprobados y desaprobados).
        * ULTIMO: Agrupa por asignatura y solo toma el intento más reciente del estudiante.
        * SOLO_APROBADOS: Solo incluye las materias aprobadas con nota aprobatoria.

    Reglas de negocio:
    - Excluye inscripciones sin calificación final registrada o en estados de retiro/anulación.
    - Aplica la fórmula estándar: Sumatoria(NotaFinal * Creditos) / Sumatoria(Creditos).
    - Si el total de créditos de las materias filtradas es cero, retorna 0.00.
    """
    # Filtrar solo inscripciones válidas con notas finales asentadas en estado APROBADA o DESAPROBADA
    validas = [
        ins for ins in inscripciones 
        if ins.get("nota_final") is not None and ins["estado"] in ("APROBADA", "DESAPROBADA")
    ]
    
    if not validas:
        return Decimal("0.00")
        
    # Aplicar la política de inclusión correspondiente
    if regla_inclusion == "SOLO_APROBADOS":
        filtradas = [ins for ins in validas if ins["estado"] == "APROBADA"]
    elif regla_inclusion == "ULTIMO":
        # Agrupar por curso y conservar únicamente el intento más reciente
        por_curso = {}
        for ins in validas:
            curso = ins["codigo_curso"]
            if curso not in por_curso:
                por_curso[curso] = ins
            else:
                # Reemplazar si el intento actual es posterior en fecha u orden
                if ins.get("fecha_orden", 0) > por_curso[curso].get("fecha_orden", 0):
                    por_curso[curso] = ins
        filtradas = list(por_curso.values())
    else:  # TODOS
        filtradas = validas
        
    if not filtradas:
        return Decimal("0.00")
        
    suma_ponderada = sum(Decimal(str(ins["nota_final"])) * Decimal(str(ins["creditos"])) for ins in filtradas)
    suma_creditos = sum(Decimal(str(ins["creditos"])) for ins in filtradas)
    
    if suma_creditos == 0:
        return Decimal("0.00")
        
    return redondear_nota(suma_ponderada / suma_creditos)

def evaluar_politica_condicion(
    valor_cuenta: Union[int, float, Decimal], 
    umbral: Union[int, float, Decimal], 
    operador: str
) -> bool:
    """
    Evalúa si el valor actual de una cuenta de seguimiento de un alumno supera un umbral
    definido en una política académica, utilizando un operador de comparación específico.

    Parámetros:
    - valor_cuenta: El valor actual de la métrica (e.g. 3 desaprobaciones).
    - umbral: El límite configurado para la política (e.g. 3.00).
    - operador: Comparación lógica ('MAYOR_QUE', 'MAYOR_IGUAL', 'IGUAL', 'MENOR_IGUAL', 'MENOR_QUE').

    Lanza:
    - CierreDomainError si el operador proporcionado no es válido.
    """
    val = Decimal(str(valor_cuenta))
    umb = Decimal(str(umbral))
    
    if operador == "MAYOR_QUE":
        return val > umb
    elif operador == "MAYOR_IGUAL":
        return val >= umb
    elif operador == "IGUAL":
        return val == umb
    elif operador == "MENOR_IGUAL":
        return val <= umb
    elif operador == "MENOR_QUE":
        return val < umb
    else:
        raise CierreDomainError(f"Operador de comparación inválido: {operador}")

class AcademicConditionStatus:
    """
    Estados estándar de la situación o condición académica del alumno.
    
    Categorías:
    - NORMAL: Alumno regular sin riesgo.
    - RIESGO_ACADEMICO: Alumno bajo supervisión por promedio bajo o cursos reprobados.
    - SUSPENDIDO: Suspensión temporal de matrícula por reincidencia en riesgo.
    - RETIRADO_DEFINITIVO: Separación definitiva de la institución académica.
    """
    NORMAL = "NORMAL"
    RIESGO_ACADEMICO = "RIESGO_ACADEMICO"
    SUSPENDIDO = "SUSPENDIDO"
    RETIRADO_DEFINITIVO = "RETIRADO_DEFINITIVO"
