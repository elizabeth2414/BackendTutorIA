-- ============================================
-- MIGRACIÓN: Deprecar función PostgreSQL agregar_puntos_estudiante
-- ============================================
-- Fecha: 2025-12-27
-- Motivo: Unificación de lógica de puntos en Python
--
-- CONTEXTO:
-- Existía duplicación de lógica entre una función PostgreSQL
-- y una función Python. La función Python es más mantenible,
-- testeable y está siendo usada actualmente.
-- La función PostgreSQL NO está siendo invocada desde ningún lugar.
-- ============================================

-- ============================================
-- OPCIÓN 1: ELIMINAR LA FUNCIÓN (RECOMENDADO)
-- ============================================
-- Solo ejecutar si estás 100% seguro de que no se usa

-- DROP FUNCTION IF EXISTS agregar_puntos_estudiante(BIGINT, INTEGER, VARCHAR);


-- ============================================
-- OPCIÓN 2: MARCAR COMO DEPRECATED (CONSERVADOR)
-- ============================================
-- Renombrar la función para que sea evidente que está deprecated
-- y agregar comentario explicativo

-- Renombrar la función original
-- DO $$
-- BEGIN
--     IF EXISTS (
--         SELECT 1 FROM pg_proc
--         WHERE proname = 'agregar_puntos_estudiante'
--     ) THEN
--         ALTER FUNCTION agregar_puntos_estudiante(BIGINT, INTEGER, VARCHAR)
--         RENAME TO _deprecated_agregar_puntos_estudiante;
--
--         RAISE NOTICE '✅ Función renombrada a _deprecated_agregar_puntos_estudiante';
--     END IF;
-- END $$;

-- Agregar comentario explicativo
-- COMMENT ON FUNCTION _deprecated_agregar_puntos_estudiante(BIGINT, INTEGER, VARCHAR) IS
-- 'DEPRECATED: Esta función está obsoleta. Usa app.servicios.gamificacion.agregar_puntos_estudiante() en Python.
-- La lógica fue unificada en la capa de aplicación para mejor mantenibilidad.
-- Esta función será eliminada en una versión futura.
-- Fecha de deprecación: 2025-12-27';


-- ============================================
-- OPCIÓN 3: HACER QUE LA FUNCIÓN LANCE ERROR
-- ============================================
-- Reemplazar la función para que lance un error si alguien intenta usarla

-- CREATE OR REPLACE FUNCTION agregar_puntos_estudiante(
--     p_estudiante_id BIGINT,
--     p_puntos INTEGER,
--     p_motivo VARCHAR DEFAULT 'Sin motivo'
-- ) RETURNS VOID AS $$
-- BEGIN
--     RAISE EXCEPTION
--         'La función agregar_puntos_estudiante() está DEPRECATED. '
--         'Usa app.servicios.gamificacion.agregar_puntos_estudiante() en Python. '
--         'Migración realizada: 2025-12-27';
-- END;
-- $$ LANGUAGE plpgsql;


-- ============================================
-- VERIFICACIÓN POST-MIGRACIÓN
-- ============================================

-- Verificar que la función Python está funcionando:
-- SELECT * FROM historial_puntos ORDER BY fecha DESC LIMIT 5;
-- SELECT * FROM nivel_estudiante LIMIT 5;

-- Verificar que no hay llamadas a la función PostgreSQL en el código:
-- grep -r "agregar_puntos_estudiante" app/

-- ============================================
-- ROLLBACK (en caso de problemas)
-- ============================================

-- Si necesitas revertir la OPCIÓN 1 (DROP):
-- Restaurar desde backup o recrear la función manualmente

-- Si necesitas revertir la OPCIÓN 2 (RENAME):
-- ALTER FUNCTION _deprecated_agregar_puntos_estudiante(BIGINT, INTEGER, VARCHAR)
-- RENAME TO agregar_puntos_estudiante;

-- Si necesitas revertir la OPCIÓN 3 (ERROR):
-- Restaurar la función original desde el schema dump


-- ============================================
-- NOTAS IMPORTANTES
-- ============================================

-- 1. Toda la lógica de puntos está ahora centralizada en:
--    app/servicios/gamificacion.py → agregar_puntos_estudiante()

-- 2. Beneficios de usar Python:
--    ✅ Mejor logging y debugging
--    ✅ Validaciones robustas
--    ✅ Manejo de errores detallado
--    ✅ Testeable con unit tests
--    ✅ Integración con FastAPI
--    ✅ Crear NivelEstudiante automáticamente si no existe

-- 3. Desventajas de mantener la función PostgreSQL:
--    ❌ Duplicación de lógica (DRY violation)
--    ❌ Difícil de mantener consistencia
--    ❌ No se está usando actualmente
--    ❌ Confusión sobre source of truth

-- 4. Antes de ejecutar esta migración:
--    ✅ Hacer backup de la base de datos
--    ✅ Verificar en producción que NO se usa la función
--    ✅ Probar en staging primero
--    ✅ Documentar el cambio

-- ============================================
-- INSTRUCCIONES DE USO
-- ============================================

-- 1. Hacer backup:
--    pg_dump -h localhost -U postgres tutoria > backup_antes_migracion.sql

-- 2. Elegir y descomentar UNA de las opciones (1, 2 o 3)

-- 3. Ejecutar la migración:
--    psql -h localhost -U postgres -d tutoria -f migrations/deprecar_funcion_agregar_puntos.sql

-- 4. Verificar que todo funciona:
--    - Probar endpoint POST /gamificacion/puntos
--    - Verificar logs de la aplicación
--    - Revisar tabla nivel_estudiante

-- 5. Monitorear en producción por 1 semana

-- 6. Si todo OK después de 1 semana, ejecutar OPCIÓN 1 (DROP definitivo)

-- ============================================
-- FIN DE MIGRACIÓN
-- ============================================
