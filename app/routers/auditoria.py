from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.esquemas import auditoria as schemas
from app.servicios import auditoria as services
from app.config import get_db

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])

@router.get("/", response_model=List[schemas.AuditoriaResponse])
def listar_auditoria(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return services.obtener_auditoria(db, skip, limit)

@router.get("/{auditoria_id}", response_model=schemas.AuditoriaResponse)
def obtener_auditoria(auditoria_id: int, db: Session = Depends(get_db)):
    db_auditoria = services.obtener_auditoria_por_id(db, auditoria_id)
    if not db_auditoria:
        raise HTTPException(status_code=404, detail="Registro de auditoría no encontrado")
    return db_auditoria

@router.get("/usuario/{usuario_id}", response_model=List[schemas.AuditoriaResponse])
def listar_auditoria_usuario(usuario_id: int, db: Session = Depends(get_db)):
    return services.obtener_auditoria_por_usuario(db, usuario_id)