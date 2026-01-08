-- ============================================
-- MIGRACIÓN: Mejorar Triggers de Auditoría para Capturar Contexto
-- ============================================
-- Fecha: 2025-12-27
-- Motivo: Los triggers guardaban usuario_id = NULL porque no tenían contexto
--
-- PROBLEMA:
-- Los triggers de auditoría no sabían qué usuario estaba haciendo los cambios,
-- por lo que siempre guardaban usuario_id = NULL en la tabla auditoria.
--
-- SOLUCIÓN:
-- 1. La aplicación Python configura variables de sesión (SET LOCAL)
-- 2. Los triggers leen esas variables para obtener el usuario_id
-- 3. Resultado: Auditoría completa con trazabilidad de usuarios
-- ============================================


-- ============================================
-- PASO 1: Verificar que la tabla auditoria existe
-- ============================================

DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'auditoria') THEN
        RAISE EXCEPTION 'La tabla auditoria no existe. Ejecuta primero el schema completo.';
    END IF;
END $$;


-- ============================================
-- PASO 2: Recrear la función de auditoría mejorada
-- ============================================

CREATE OR REPLACE FUNCTION registrar_auditoria()
RETURNS TRIGGER AS $$
DECLARE
    v_usuario_id BIGINT;
    v_ip_address VARCHAR(50);
    v_accion VARCHAR(100);
    v_datos_anteriores JSONB;
    v_datos_nuevos JSONB;
BEGIN
    -- ============================================
    -- 1. OBTENER CONTEXTO DEL USUARIO
    -- ============================================

    -- Intentar leer usuario_id de la variable de sesión
    -- (configurada por la aplicación Python)
    BEGIN
        v_usuario_id := current_setting('app.current_user_id', TRUE)::BIGINT;
    EXCEPTION
        WHEN OTHERS THEN
            -- Si no está configurada, usar NULL
            v_usuario_id := NULL;
    END;

    -- Intentar leer IP del usuario
    BEGIN
        v_ip_address := current_setting('app.current_user_ip', TRUE);
    EXCEPTION
        WHEN OTHERS THEN
            v_ip_address := NULL;
    END;

    -- ============================================
    -- 2. DETERMINAR ACCIÓN Y DATOS
    -- ============================================

    IF (TG_OP = 'INSERT') THEN
        v_accion := 'INSERT';
        v_datos_anteriores := NULL;
        v_datos_nuevos := to_jsonb(NEW);

    ELSIF (TG_OP = 'UPDATE') THEN
        v_accion := 'UPDATE';
        v_datos_anteriores := to_jsonb(OLD);
        v_datos_nuevos := to_jsonb(NEW);

    ELSIF (TG_OP = 'DELETE') THEN
        v_accion := 'DELETE';
        v_datos_anteriores := to_jsonb(OLD);
        v_datos_nuevos := NULL;
    END IF;

    -- ============================================
    -- 3. INSERTAR REGISTRO DE AUDITORÍA
    -- ============================================

    INSERT INTO auditoria (
        usuario_id,           -- ✅ Ahora captura el usuario correctamente
        accion,
        tabla_afectada,
        registro_id,
        datos_anteriores,
        datos_nuevos,
        ip_address,          -- ✅ Captura la IP del usuario
        user_agent,          -- Se puede agregar en futuras versiones
        fecha_evento
    ) VALUES (
        v_usuario_id,         -- ID del usuario autenticado (o NULL si público)
        v_accion,             -- INSERT, UPDATE, DELETE
        TG_TABLE_NAME,        -- Nombre de la tabla
        CASE
            WHEN TG_OP = 'DELETE' THEN (OLD.id)
            ELSE (NEW.id)
        END,                  -- ID del registro afectado
        v_datos_anteriores,   -- Estado anterior (JSON)
        v_datos_nuevos,       -- Estado nuevo (JSON)
        v_ip_address,         -- IP del cliente
        NULL,                 -- user_agent (para futuras versiones)
        NOW()                 -- Timestamp del evento
    );

    -- ============================================
    -- 4. RETORNAR SEGÚN OPERACIÓN
    -- ============================================

    IF (TG_OP = 'DELETE') THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Agregar comentario a la función
COMMENT ON FUNCTION registrar_auditoria() IS
'Trigger function mejorada que captura el contexto del usuario autenticado.
Lee las variables de sesión configuradas por la aplicación Python:
- app.current_user_id: ID del usuario autenticado
- app.current_user_ip: IP del cliente
Versión: 2.0 - Actualizada: 2025-12-27';


-- ============================================
-- PASO 3: Recrear triggers en tablas importantes
-- ============================================

-- Las tablas que necesitan auditoría completa son:
-- usuario, estudiante, docente, padre, contenido_lectura, evaluacion_lectura, etc.

-- Función auxiliar para crear/recrear trigger
DO $$
DECLARE
    tabla_name TEXT;
    tablas_auditar TEXT[] := ARRAY[
        'usuario',
        'estudiante',
        'docente',
        'padre',
        'contenido_lectura',
        'evaluacion_lectura',
        'detalle_evaluacion',
        'actividad_lectura',
        'respuesta_actividad',
        'ejercicio_pronunciacion',
        'historial_puntos',
        'nivel_estudiante',
        'recompensa_estudiante',
        'mision_diaria'
    ];
BEGIN
    FOREACH tabla_name IN ARRAY tablas_auditar
    LOOP
        -- Verificar si la tabla existe
        IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = tabla_name) THEN

            -- Eliminar trigger existente si ya está
            EXECUTE format('DROP TRIGGER IF EXISTS trigger_auditoria ON %I', tabla_name);

            -- Crear trigger mejorado
            EXECUTE format('
                CREATE TRIGGER trigger_auditoria
                AFTER INSERT OR UPDATE OR DELETE ON %I
                FOR EACH ROW
                EXECUTE FUNCTION registrar_auditoria()
            ', tabla_name);

            RAISE NOTICE '✅ Trigger de auditoría creado/actualizado en tabla: %', tabla_name;
        ELSE
            RAISE NOTICE '⚠️  Tabla % no existe, saltando...', tabla_name;
        END IF;
    END LOOP;
END $$;


-- ============================================
-- PASO 4: Verificación post-migración
-- ============================================

-- Verificar que la función existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc
        WHERE proname = 'registrar_auditoria'
    ) THEN
        RAISE EXCEPTION '❌ La función registrar_auditoria() no existe';
    ELSE
        RAISE NOTICE '✅ Función registrar_auditoria() verificada';
    END IF;
END $$;

-- Listar todas las tablas con trigger de auditoría
SELECT
    trigger_schema,
    event_object_table AS tabla,
    trigger_name,
    event_manipulation AS evento
FROM information_schema.triggers
WHERE trigger_name = 'trigger_auditoria'
ORDER BY event_object_table;


-- ============================================
-- PASO 5: Ejemplo de Prueba
-- ============================================

/*
-- Para probar que funciona, ejecuta esto desde Python:

from sqlalchemy import text
from app.config import SessionLocal

db = SessionLocal()

# Configurar contexto de usuario
db.execute(text("SET LOCAL app.current_user_id = :user_id"), {"user_id": 1})
db.execute(text("SET LOCAL app.current_user_ip = :ip"), {"ip": "192.168.1.100"})

# Hacer una operación (ej: actualizar estudiante)
estudiante = db.query(Estudiante).filter(Estudiante.id == 1).first()
if estudiante:
    estudiante.nombre = "Nombre Actualizado - Prueba"
    db.commit()

# Verificar la auditoría
auditoria = db.query(Auditoria).order_by(Auditoria.id.desc()).first()
print(f"Usuario ID: {auditoria.usuario_id}")  # Debería ser 1
print(f"IP: {auditoria.ip_address}")          # Debería ser 192.168.1.100
print(f"Acción: {auditoria.accion}")          # Debería ser UPDATE
print(f"Tabla: {auditoria.tabla_afectada}")   # Debería ser estudiante

db.close()
*/


-- ============================================
-- PASO 6: Consultas Útiles para Verificación
-- ============================================

-- Ver auditorías con usuario (deberían tener usuario_id no NULL)
-- SELECT
--     a.id,
--     a.usuario_id,
--     u.email AS usuario_email,
--     a.accion,
--     a.tabla_afectada,
--     a.ip_address,
--     a.fecha_evento
-- FROM auditoria a
-- LEFT JOIN usuario u ON a.usuario_id = u.id
-- ORDER BY a.fecha_evento DESC
-- LIMIT 20;

-- Ver auditorías sin usuario (operaciones públicas o antiguas)
-- SELECT
--     COUNT(*) as total,
--     accion,
--     tabla_afectada
-- FROM auditoria
-- WHERE usuario_id IS NULL
-- GROUP BY accion, tabla_afectada
-- ORDER BY total DESC;

-- Ver actividad reciente por usuario
-- SELECT
--     u.email,
--     u.nombre,
--     COUNT(*) as operaciones,
--     MAX(a.fecha_evento) as ultima_actividad
-- FROM auditoria a
-- JOIN usuario u ON a.usuario_id = u.id
-- GROUP BY u.id, u.email, u.nombre
-- ORDER BY operaciones DESC
-- LIMIT 10;


-- ============================================
-- ROLLBACK (en caso de problemas)
-- ============================================

-- Si necesitas revertir los cambios:
/*
-- 1. Eliminar triggers de todas las tablas
DO $$
DECLARE
    tabla_name TEXT;
BEGIN
    FOR tabla_name IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trigger_auditoria ON %I', tabla_name);
    END LOOP;
END $$;

-- 2. Restaurar función original (si tienes backup)
-- DROP FUNCTION registrar_auditoria();
-- Luego ejecuta la versión anterior desde el backup
*/


-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

-- 1. COMPATIBILIDAD:
--    - Esta migración es compatible con registros antiguos (usuario_id NULL)
--    - Los nuevos registros tendrán usuario_id correcto

-- 2. VARIABLES DE SESIÓN:
--    - SET LOCAL solo afecta la transacción actual
--    - Se limpian automáticamente al finalizar la transacción
--    - No hay riesgo de "contaminación" entre requests

-- 3. RENDIMIENTO:
--    - current_setting() es muy rápido (lectura de variable de sesión)
--    - El impacto en rendimiento es mínimo
--    - Los triggers solo se ejecutan cuando hay cambios

-- 4. SEGURIDAD:
--    - El usuario_id viene del token JWT validado
--    - No se puede falsificar desde el cliente
--    - La aplicación Python controla quién puede hacer qué

-- 5. ENDPOINTS PÚBLICOS:
--    - Para endpoints sin autenticación (register, login), usuario_id será NULL
--    - Esto es correcto y esperado
--    - La IP se captura de todas formas

-- 6. USO EN LA APLICACIÓN:
--    - Usar get_db_with_audit_context en lugar de get_db
--    - El middleware configura todo automáticamente
--    - Ver app/middlewares/audit_context.py para detalles


-- ============================================
-- INSTRUCCIONES DE EJECUCIÓN
-- ============================================

-- 1. Hacer backup de la base de datos:
--    pg_dump -h localhost -U postgres tutoria > backup_antes_triggers.sql

-- 2. Ejecutar esta migración:
--    psql -h localhost -U postgres -d tutoria -f migrations/mejorar_triggers_auditoria.sql

-- 3. Verificar que funcionó:
--    - Ejecutar las consultas de verificación (PASO 6)
--    - Probar desde la aplicación Python
--    - Revisar logs de la aplicación

-- 4. Actualizar código de la aplicación:
--    - Reemplazar Depends(get_db) con Depends(get_db_with_audit_context)
--    - En los routers que necesitan auditoría completa

-- 5. Monitorear en producción:
--    - Verificar que usuario_id se guarda correctamente
--    - Verificar que IP se captura
--    - Revisar performance (no debería haber impacto)


-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================

RAISE NOTICE '';
RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
RAISE NOTICE '║  ✅ MIGRACIÓN DE TRIGGERS DE AUDITORÍA COMPLETADA             ║';
RAISE NOTICE '║                                                                ║';
RAISE NOTICE '║  Próximos pasos:                                               ║';
RAISE NOTICE '║  1. Actualizar routers para usar get_db_with_audit_context     ║';
RAISE NOTICE '║  2. Probar con operaciones CRUD                                ║';
RAISE NOTICE '║  3. Verificar tabla auditoria tiene usuario_id no NULL         ║';
RAISE NOTICE '║                                                                ║';
RAISE NOTICE '║  Documentación: AUDITORIA_README.md                            ║';
RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
RAISE NOTICE '';
