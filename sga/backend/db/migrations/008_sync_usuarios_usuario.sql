-- Sync existing users from usuarios to usuario
INSERT INTO public.usuario (
    id_usuario,
    id_tenant,
    nombre_completo,
    email,
    password_hash,
    rol,
    estado,
    fecha_registro
)
SELECT 
    u.id,
    COALESCE(t.id_tenant, 'b387616c-4731-489c-bc4d-84092face20b'),
    u.nombre || ' ' || u.apellido,
    u.email,
    u.password_hash,
    CASE 
        WHEN u.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
        WHEN u.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
        ELSE u.rol::text
    END,
    CASE WHEN u.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
    u.created_at
FROM public.usuarios u
LEFT JOIN public.tenants t ON u.id_tenant = t.id
ON CONFLICT (id_usuario) DO UPDATE SET
    id_tenant = EXCLUDED.id_tenant,
    nombre_completo = EXCLUDED.nombre_completo,
    email = EXCLUDED.email,
    password_hash = EXCLUDED.password_hash,
    rol = EXCLUDED.rol,
    estado = EXCLUDED.estado,
    updated_at = NOW();

-- Create trigger function to sync changes from usuarios to usuario
CREATE OR REPLACE FUNCTION public.sync_usuarios_to_usuario_func()
RETURNS TRIGGER AS $$
DECLARE
    v_id_tenant UUID;
BEGIN
    SELECT t.id_tenant INTO v_id_tenant
    FROM public.tenants t
    WHERE t.id = NEW.id_tenant;

    IF v_id_tenant IS NULL THEN
        v_id_tenant := 'b387616c-4731-489c-bc4d-84092face20b';
    END IF;

    IF TG_OP = 'INSERT' THEN
        INSERT INTO public.usuario (
            id_usuario,
            id_tenant,
            nombre_completo,
            email,
            password_hash,
            rol,
            estado,
            fecha_registro
        ) VALUES (
            NEW.id,
            v_id_tenant,
            NEW.nombre || ' ' || NEW.apellido,
            NEW.email,
            NEW.password_hash,
            CASE 
                WHEN NEW.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
                WHEN NEW.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
                ELSE NEW.rol::text
            END,
            CASE WHEN NEW.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
            NEW.created_at
        ) ON CONFLICT (id_usuario) DO NOTHING;
    ELSIF TG_OP = 'UPDATE' THEN
        UPDATE public.usuario SET
            id_tenant = v_id_tenant,
            nombre_completo = NEW.nombre || ' ' || NEW.apellido,
            email = NEW.email,
            password_hash = NEW.password_hash,
            rol = CASE 
                WHEN NEW.rol::text = 'ADMIN_CENTRAL' THEN 'ADMINISTRADOR_CENTRAL'
                WHEN NEW.rol::text = 'ADMIN' THEN 'ADMINISTRADOR'
                ELSE NEW.rol::text
            END,
            estado = CASE WHEN NEW.activo THEN 'ACTIVO' ELSE 'INACTIVO' END,
            updated_at = NOW()
        WHERE id_usuario = OLD.id;
    ELSIF TG_OP = 'DELETE' THEN
        DELETE FROM public.usuario WHERE id_usuario = OLD.id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_usuarios_to_usuario ON public.usuarios;
CREATE TRIGGER trg_sync_usuarios_to_usuario
AFTER INSERT OR UPDATE OR DELETE ON public.usuarios
FOR EACH ROW EXECUTE FUNCTION public.sync_usuarios_to_usuario_func();
