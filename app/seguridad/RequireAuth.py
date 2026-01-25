from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

SECRET = "CAMBIA_ESTO"
ALGO = "HS256"

def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        return {"id": payload["sub"], "role": payload["role"]}
    except (JWTError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

def require_roles(*roles):
    def checker(user=Depends(get_current_user)):
        if user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No autorizado")
        return user
    return checker

@app.get("/api/padre/menu")
def padre_menu(user=Depends(require_roles("PADRE"))):
    return {"menu": "padre"}

@app.get("/api/docente/menu")
def docente_menu(user=Depends(require_roles("DOCENTE"))):
    return {"menu": "docente"}

@app.get("/api/admin/menu")
def admin_menu(user=Depends(require_roles("ADMIN"))):
    return {"menu": "admin"}

