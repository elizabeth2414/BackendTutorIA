# app/main.py

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
import traceback

from app.logs.logger import logger
from app.config import SessionLocal
from app.routers import api_router

# =====================================================
# APP
# =====================================================
app = FastAPI(
    title="Tutor IA - Backend",
    version="1.0.0"
)

logger.info("🚀 Backend TutorIA iniciado correctamente")

# =====================================================
# MIDDLEWARE PARA LOGGING DE REQUESTS
# =====================================================
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"📥 {request.method} {request.url.path}")
    logger.info(f"   Origin: {request.headers.get('origin', 'No origin')}")
    
    try:
        response = await call_next(request)
        logger.info(f"📤 Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"❌ Error procesando request: {e}")
        logger.error(traceback.format_exc())
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# =====================================================
# CORS CONFIG
# =====================================================
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://192.168.54.55:5173",
    "capacitor://localhost",
    "http://localhost:8080",
    "ionic://localhost",
    "http://localhost",
    "https://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# =====================================================
# ENDPOINTS DE PRUEBA
# =====================================================
@app.get("/")
def root():
    return {"message": "API TutorIA funcionando correctamente"}

@app.get("/test")
def test():
    logger.info("Se llamó al endpoint /test")
    return {"message": "Todo OK"}

@app.get("/test-db")
def test_db():
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"message": "🚀 Conexión a la base de datos exitosa"}
    except SQLAlchemyError as e:
        logger.error(str(e))
        return {
            "message": "❌ Error en la conexión a la base de datos",
            "detail": str(e),
        }

# =====================================================
# ENDPOINT DE PRUEBA CORS
# =====================================================
@app.post("/api/test-cors")
async def test_cors():
    return {"message": "✅ CORS funcionando correctamente"}

# =====================================================
# REGISTRO DE ROUTERS
# =====================================================
app.include_router(api_router, prefix="/api")

# =====================================================
# MANEJADOR DE ERRORES GLOBAL
# =====================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"❌ Error global: {exc}")
    logger.error(traceback.format_exc())
    
    return JSONResponse(
        status_code=500,
        content={
            "message": "Error interno del servidor",
            "detail": str(exc),
            "path": request.url.path
        }
    )