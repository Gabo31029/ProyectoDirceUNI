from typing import List, Dict, Any, Union
from decimal import Decimal, ROUND_HALF_UP

class CierreDomainError(Exception):
    pass

def redondear_nota(val: Decimal) -> Decimal:
    """
    Rounds a grade to two decimal places (e.g., 14.567 -> 14.57).
    """
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def calcular_nota_final(calificaciones: List[Dict[str, Any]]) -> Decimal:
    """
    Calculates the final grade of an enrollment by weighting component grades.
    calificaciones: list of dicts, each with keys 'valor_nota' (Decimal) and 'peso_relativo' (Decimal).
    The sum of pesos must equal 100.
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
    Calculates weighted average grade based on list of course enrollments.
    Each inscription dict has:
      - 'codigo_curso' (str)
      - 'creditos' (int or Decimal)
      - 'nota_final' (Decimal)
      - 'estado' (str: APROBADA, DESAPROBADA, etc.)
      - 'fecha_orden' (Any comparable, e.g. datetime or int to sort attempts)
    """
    # Filter out inscriptions without a final grade (e.g., RETIRADA, ANULADA, or active/ungraded)
    validas = [
        ins for ins in inscripciones 
        if ins.get("nota_final") is not None and ins["estado"] in ("APROBADA", "DESAPROBADA")
    ]
    
    if not validas:
        return Decimal("0.00")
        
    # Apply inclusion rules
    if regla_inclusion == "SOLO_APROBADOS":
        filtradas = [ins for ins in validas if ins["estado"] == "APROBADA"]
    elif regla_inclusion == "ULTIMO":
        # Group by course, keep only the latest attempt
        por_curso = {}
        for ins in validas:
            curso = ins["codigo_curso"]
            if curso not in por_curso:
                por_curso[curso] = ins
            else:
                # Keep the one with latest fecha_orden
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
    Evaluates if a follower account value triggers a policy threshold.
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
    NORMAL = "NORMAL"
    RIESGO_ACADEMICO = "RIESGO_ACADEMICO"
    SUSPENDIDO = "SUSPENDIDO"
    RETIRADO_DEFINITIVO = "RETIRADO_DEFINITIVO"
