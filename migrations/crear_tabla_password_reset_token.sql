-- ============================================
-- MIGRACIÓN: Crear tabla password_reset_token
-- ============================================
-- Fecha: 2025-12-27
-- Motivo: Implementar funcionalidad completa de reset de contraseña
--
-- PROBLEMA ANTERIOR:
-- - Funciones resetear_password() y confirmar_reset_password() eran stubs
-- - Solo retornaban mensajes sin funcionalidad real
-- - No había manera de resetear contraseñas de forma segura
--
-- SOLUCIÓN:
-- - Crear tabla para almacenar tokens de reset temporales
-- - Tokens seguros generados con secrets.token_urlsafe()
-- - Expiración automática (1 hora)
-- - Un solo uso por token
-- - Tracking de IP para seguridad
-- ============================================


-- ============================================
-- PASO 1: Crear la tabla password_reset_token
-- ============================================

CREATE TABLE IF NOT EXISTS password_reset_token (
    id BIGSERIAL PRIMARY KEY,
    usuario_id BIGINT NOT NULL,
    token VARCHAR(255) NOT NULL UNIQUE,
    fecha_creacion TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    fecha_expiracion TIMESTAMP WITH TIME ZONE NOT NULL,
    usado BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_uso TIMESTAMP WITH TIME ZONE,
    ip_solicitante VARCHAR(50),

    -- Foreign key
    CONSTRAINT fk_password_reset_usuario
        FOREIGN KEY (usuario_id)
        REFERENCES usuario(id)
        ON DELETE CASCADE,

    -- Indices para performance
    CONSTRAINT idx_password_reset_token_unique UNIQUE (token)
);

-- Comentario en la tabla
COMMENT ON TABLE password_reset_token IS
'Tokens temporales para reset de contraseña.
Características:
- Tokens únicos y seguros (URL-safe, 43 caracteres)
- Expiración automática (default: 1 hora)
- Un solo uso (campo usado)
- Tracking de IP para seguridad';

-- Comentarios en columnas
COMMENT ON COLUMN password_reset_token.token IS 'Token URL-safe generado con secrets.token_urlsafe(32)';
COMMENT ON COLUMN password_reset_token.fecha_expiracion IS 'Timestamp UTC de expiración (normalmente fecha_creacion + 1 hora)';
COMMENT ON COLUMN password_reset_token.usado IS 'Marca si el token ya fue utilizado (un solo uso)';
COMMENT ON COLUMN password_reset_token.fecha_uso IS 'Timestamp UTC de cuándo se usó el token';
COMMENT ON COLUMN password_reset_token.ip_solicitante IS 'IP del cliente que solicitó el reset (seguridad)';


-- ============================================
-- PASO 2: Crear índices para optimización
-- ============================================

-- Índice en usuario_id (para buscar tokens de un usuario)
CREATE INDEX IF NOT EXISTS idx_password_reset_usuario_id
    ON password_reset_token(usuario_id);

-- Índice en token (para búsqueda rápida al validar)
CREATE INDEX IF NOT EXISTS idx_password_reset_token_lookup
    ON password_reset_token(token)
    WHERE usado = FALSE;

-- Índice en fecha_expiracion (para limpiar tokens expirados)
CREATE INDEX IF NOT EXISTS idx_password_reset_fecha_exp
    ON password_reset_token(fecha_expiracion);


-- ============================================
-- PASO 3: Función para limpiar tokens expirados (opcional)
-- ============================================

CREATE OR REPLACE FUNCTION limpiar_tokens_expirados()
RETURNS INTEGER AS $$
DECLARE
    tokens_eliminados INTEGER;
BEGIN
    -- Eliminar tokens expirados hace más de 7 días
    DELETE FROM password_reset_token
    WHERE fecha_expiracion < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS tokens_eliminados = ROW_COUNT;

    RAISE NOTICE '🧹 Tokens de reset expirados eliminados: %', tokens_eliminados;

    RETURN tokens_eliminados;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION limpiar_tokens_expirados() IS
'Elimina tokens de reset expirados hace más de 7 días.
Ejecutar periódicamente (cron job) para mantener la tabla limpia.
Uso: SELECT limpiar_tokens_expirados();';


-- ============================================
-- PASO 4: Verificación post-migración
-- ============================================

DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'password_reset_token'
    ) THEN
        RAISE NOTICE '✅ Tabla password_reset_token creada exitosamente';
    ELSE
        RAISE EXCEPTION '❌ Error: Tabla password_reset_token no fue creada';
    END IF;
END $$;


-- ============================================
-- PASO 5: Consultas útiles de verificación
-- ============================================

-- Ver estructura de la tabla
-- \d password_reset_token

-- Ver tokens activos (no usados y no expirados)
-- SELECT
--     prt.id,
--     u.email,
--     prt.fecha_creacion,
--     prt.fecha_expiracion,
--     prt.usado,
--     prt.ip_solicitante,
--     CASE
--         WHEN prt.fecha_expiracion < NOW() THEN 'EXPIRADO'
--         WHEN prt.usado THEN 'USADO'
--         ELSE 'ACTIVO'
--     END AS estado
-- FROM password_reset_token prt
-- JOIN usuario u ON prt.usuario_id = u.id
-- ORDER BY prt.fecha_creacion DESC
-- LIMIT 20;

-- Ver estadísticas
-- SELECT
--     COUNT(*) AS total_tokens,
--     COUNT(CASE WHEN usado THEN 1 END) AS usados,
--     COUNT(CASE WHEN fecha_expiracion < NOW() THEN 1 END) AS expirados,
--     COUNT(CASE WHEN usado = FALSE AND fecha_expiracion > NOW() THEN 1 END) AS activos
-- FROM password_reset_token;


-- ============================================
-- PASO 6: Ejemplo de uso desde la aplicación
-- ============================================

/*
FLUJO COMPLETO DE RESET PASSWORD:

1. Usuario solicita reset:
   POST /auth/reset-password
   {
     "email": "user@example.com"
   }

   Backend:
   - Genera token seguro: secrets.token_urlsafe(32)
   - Guarda en password_reset_token con expiración de 1 hora
   - (TODO) Envía email con enlace: https://app.com/reset?token=ABC123...
   - Retorna mensaje genérico (no revela si email existe)

2. Usuario recibe email y hace clic en enlace

3. Frontend muestra formulario de nueva contraseña

4. Usuario envía nueva contraseña:
   POST /auth/confirm-reset-password
   {
     "token": "ABC123...",
     "nuevo_password": "nuevaPassword123"
   }

   Backend:
   - Busca token en BD
   - Valida que no esté usado
   - Valida que no esté expirado
   - Hashea nueva contraseña
   - Actualiza usuario
   - Marca token como usado
   - Invalida otros tokens del usuario
*/


-- ============================================
-- PASO 7: Rollback (en caso de problemas)
-- ============================================

-- Si necesitas revertir la migración:
/*
DROP TABLE IF EXISTS password_reset_token CASCADE;
DROP FUNCTION IF EXISTS limpiar_tokens_expirados();
*/


-- ============================================
-- PASO 8: Mantenimiento recomendado
-- ============================================

-- Configurar cron job para limpiar tokens antiguos:
/*
-- Opción 1: Cron de PostgreSQL (pg_cron extension)
SELECT cron.schedule(
    'cleanup-reset-tokens',
    '0 2 * * *',  -- Cada día a las 2 AM
    $$SELECT limpiar_tokens_expirados();$$
);

-- Opción 2: Cron de sistema (crontab -e)
0 2 * * * psql -h localhost -U postgres -d tutoria -c "SELECT limpiar_tokens_expirados();"

-- Opción 3: Tarea programada en la aplicación (FastAPI + APScheduler)
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(
    limpiar_tokens_db,
    'cron',
    hour=2,
    minute=0
)
scheduler.start()
*/


-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

-- 1. SEGURIDAD:
--    - Tokens generados con secrets.token_urlsafe() (criptográficamente seguros)
--    - Tokens de un solo uso (campo usado)
--    - Expiración automática (1 hora)
--    - IP tracking para auditoría
--    - No se retorna token en respuesta en producción (solo por email)

-- 2. PRIVACIDAD:
--    - No se revela si un email existe o no
--    - Mismo mensaje para emails existentes y no existentes
--    - Previene enumeración de usuarios

-- 3. USABILIDAD:
--    - Tokens válidos por 1 hora (balance seguridad/conveniencia)
--    - Usuario puede solicitar múltiples tokens (los anteriores se invalidan)
--    - Mensajes de error claros (token expirado, usado, inválido)

-- 4. RENDIMIENTO:
--    - Índices en columnas clave (usuario_id, token, fecha_expiracion)
--    - Limpieza periódica de tokens antiguos
--    - Foreign key con ON DELETE CASCADE (limpia automáticamente si usuario se borra)

-- 5. PRODUCCIÓN:
--    - ⚠️ IMPORTANTE: Configurar servicio de email (SMTP, SendGrid, etc.)
--    - Cambiar variable DEBUG a False en producción
--    - Monitorear intentos de reset (posibles ataques)
--    - Considerar rate limiting (max X solicitudes por IP/hora)

-- 6. TESTING:
--    - En modo DEBUG, el token se incluye en la respuesta
--    - En producción, solo se envía por email
--    - Verificar que emails lleguen correctamente
--    - Probar escenarios: token expirado, usado, inválido


-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================

RAISE NOTICE '';
RAISE NOTICE '╔════════════════════════════════════════════════════════════════╗';
RAISE NOTICE '║  ✅ MIGRACIÓN COMPLETADA: password_reset_token                ║';
RAISE NOTICE '║                                                                ║';
RAISE NOTICE '║  Próximos pasos:                                               ║';
RAISE NOTICE '║  1. Configurar servicio de email (SMTP/SendGrid)              ║';
RAISE NOTICE '║  2. Actualizar frontend con formulario de reset               ║';
RAISE NOTICE '║  3. Probar flujo completo end-to-end                          ║';
RAISE NOTICE '║  4. Configurar cron job para limpiar tokens antiguos          ║';
RAISE NOTICE '║  5. Agregar rate limiting (opcional pero recomendado)         ║';
RAISE NOTICE '║                                                                ║';
RAISE NOTICE '║  Endpoints disponibles:                                        ║';
RAISE NOTICE '║  - POST /auth/reset-password                                   ║';
RAISE NOTICE '║  - POST /auth/confirm-reset-password                           ║';
RAISE NOTICE '║                                                                ║';
RAISE NOTICE '║  Documentación: RESET_PASSWORD_README.md                       ║';
RAISE NOTICE '╚════════════════════════════════════════════════════════════════╝';
RAISE NOTICE '';
