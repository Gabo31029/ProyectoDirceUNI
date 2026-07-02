import json
from decimal import Decimal
from typing import Any, Optional
from sqlalchemy.orm import Session
from app.models.seguimiento import RegistroAuditoria, EventoAcademico, CuentaSeguimientoAlumno
from app.models.core_schemas import TipoEvento

def log_audit(
    db: Session,
    id_tenant: str,
    id_usuario: str,
    tipo_operacion: str,
    entidad_afectada_tipo: str,
    entidad_afectada_id: str,
    resultado: str,  # EXITOSA or RECHAZADA
    valor_anterior: Optional[Any] = None,
    valor_nuevo: Optional[Any] = None,
    motivo_rechazo: Optional[str] = None
) -> RegistroAuditoria:
    """
    Logs an operation in the system audit log (registro_auditoria).
    """
    import uuid
    from app.models.core_schemas import Tenant, Usuario

    # Sanitize id_tenant
    try:
        uuid.UUID(str(id_tenant))
    except ValueError:
        first_t = db.query(Tenant).first()
        id_tenant = str(first_t.id_tenant) if first_t else str(uuid.uuid4())

    # Sanitize id_usuario
    try:
        uuid.UUID(str(id_usuario))
    except ValueError:
        first_u = db.query(Usuario).first()
        id_usuario = str(first_u.id_usuario) if first_u else str(uuid.uuid4())

    val_ant = json.dumps(valor_anterior) if valor_anterior is not None else None
    val_nue = json.dumps(valor_nuevo) if valor_nuevo is not None else None
    
    audit_log = RegistroAuditoria(
        id_tenant=id_tenant,
        id_usuario=id_usuario,
        tipo_operacion=tipo_operacion,
        entidad_afectada_tipo=entidad_afectada_tipo,
        entidad_afectada_id=entidad_afectada_id,
        resultado=resultado,
        valor_anterior=val_ant,
        valor_nuevo=val_nue,
        motivo_rechazo=motivo_rechazo
    )
    db.add(audit_log)
    db.flush()
    return audit_log

def create_academic_event(
    db: Session,
    id_tenant: str,
    codigo_evento: str,
    id_actor: str,
    entidad_afectada_tipo: str,
    entidad_afectada_id: str,
    id_perfil_alumno: Optional[str] = None,  # Required to update student accounts
    valor_anterior: Optional[Any] = None,
    valor_nuevo: Optional[Any] = None,
    id_evento_ref: Optional[str] = None,
    id_periodo_ref: Optional[str] = None,
    id_curso_ref: Optional[str] = None
) -> EventoAcademico:
    """
    Generates an academic event (evento_academico) and automatically updates 
    the student's corresponding CuentaSeguimientoAlumno if the event type requires it.
    """
    import uuid
    from app.models.core_schemas import Tenant, Usuario

    # Sanitize id_tenant
    try:
        uuid.UUID(str(id_tenant))
    except ValueError:
        first_t = db.query(Tenant).first()
        id_tenant = str(first_t.id_tenant) if first_t else str(uuid.uuid4())

    # Sanitize id_actor
    try:
        uuid.UUID(str(id_actor))
    except ValueError:
        first_u = db.query(Usuario).first()
        id_actor = str(first_u.id_usuario) if first_u else str(uuid.uuid4())

    # 1. Look up the TipoEvento in the current Tenant catalog.
    tipo_ev = db.query(TipoEvento).filter(
        TipoEvento.id_tenant == id_tenant,
        TipoEvento.codigo == codigo_evento
    ).first()
    
    # Defensive setup: create TipoEvento on the fly if not exists (for tests/development)
    if not tipo_ev:
        # Infer target follow-up account from event code
        cuenta_obj = "CTA-CREDITOS-INSCRITOS"
        operacion = "ASIGNACION"
        
        if "NOTA-FINAL" in codigo_evento or "NOTA-CORREGIDA" in codigo_evento:
            cuenta_obj = "CTA-CREDITOS-APROBADOS"
            operacion = "INCREMENTO"
        elif "DESAPROBADA" in codigo_evento or "REPROBO" in codigo_evento:
            cuenta_obj = "CTA-DESAPROBACIONES"
            operacion = "INCREMENTO"
        elif "MATRICULA" in codigo_evento:
            cuenta_obj = "CTA-CREDITOS-INSCRITOS"
            operacion = "INCREMENTO"
            
        tipo_ev = TipoEvento(
            id_tenant=id_tenant,
            codigo=codigo_evento,
            nombre=f"Evento {codigo_evento}",
            cuenta_objetivo=cuenta_obj,
            operacion=operacion
        )
        db.add(tipo_ev)
        db.flush()

    val_ant = json.dumps(valor_anterior) if valor_anterior is not None else None
    val_nue = json.dumps(valor_nuevo) if valor_nuevo is not None else None

    # 2. Insert the academic event
    event = EventoAcademico(
        id_tenant=id_tenant,
        id_tipo_evento=tipo_ev.id_tipo_evento,
        id_actor=id_actor,
        entidad_afectada_tipo=entidad_afectada_tipo,
        entidad_afectada_id=entidad_afectada_id,
        valor_anterior=val_ant,
        valor_nuevo=val_nue,
        id_evento_ref=id_evento_ref
    )
    db.add(event)
    db.flush()

    # 3. Update the corresponding student follow-up account, if profile ID is supplied
    if id_perfil_alumno and tipo_ev.cuenta_objetivo:
        # Find the specific account
        # UniqueConstraint: (id_perfil_alumno, tipo_cuenta, id_periodo_ref, id_curso_ref)
        # Note that some accounts have period or course reference, others are global.
        p_ref = id_periodo_ref if tipo_ev.cuenta_objetivo in ("CTA-CREDITOS-INSCRITOS", "CTA-PROMEDIO-SNAPSHOT") else None
        c_ref = id_curso_ref if tipo_ev.cuenta_objetivo == "CTA-DESAPROBACIONES" else None
        
        cuenta = db.query(CuentaSeguimientoAlumno).filter(
            CuentaSeguimientoAlumno.id_perfil_alumno == id_perfil_alumno,
            CuentaSeguimientoAlumno.tipo_cuenta == tipo_ev.cuenta_objetivo,
            CuentaSeguimientoAlumno.id_periodo_ref == p_ref,
            CuentaSeguimientoAlumno.id_curso_ref == c_ref
        ).first()
        
        if not cuenta:
            cuenta = CuentaSeguimientoAlumno(
                id_perfil_alumno=id_perfil_alumno,
                id_tenant=id_tenant,
                tipo_cuenta=tipo_ev.cuenta_objetivo,
                id_periodo_ref=p_ref,
                id_curso_ref=c_ref,
                valor_actual=Decimal("0.00")
            )
            db.add(cuenta)
            db.flush()
            
        # Perform operation
        if tipo_ev.operacion == "INCREMENTO":
            # For grades or credits, we increment by the value provided in valor_nuevo (e.g. credits amount)
            inc_val = Decimal("1.00")
            if isinstance(valor_nuevo, (int, float, Decimal)):
                inc_val = Decimal(str(valor_nuevo))
            elif isinstance(valor_nuevo, dict) and "creditos" in valor_nuevo:
                inc_val = Decimal(str(valor_nuevo["creditos"]))
            cuenta.valor_actual += inc_val
        elif tipo_ev.operacion == "DECREMENTO":
            dec_val = Decimal("1.00")
            if isinstance(valor_nuevo, (int, float, Decimal)):
                dec_val = Decimal(str(valor_nuevo))
            cuenta.valor_actual = max(Decimal("0.00"), cuenta.valor_actual - dec_val)
        elif tipo_ev.operacion == "ASIGNACION":
            set_val = Decimal("0.00")
            if isinstance(valor_nuevo, (int, float, Decimal)):
                set_val = Decimal(str(valor_nuevo))
            cuenta.valor_actual = set_val
            
        db.add(cuenta)
        db.flush()
        
    return event
