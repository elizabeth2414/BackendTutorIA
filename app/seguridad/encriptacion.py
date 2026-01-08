from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
import os

# Configuración para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuración para encriptación Fernet
def generar_clave_fernet():
    return Fernet.generate_key()

# Usar una clave fija o generar una (en producción usar environment variable)
clave_fernet = os.getenv("FERNET_KEY", "tu-clave-secreta-aqui-32-bytes")
fernet = Fernet(base64.urlsafe_b64encode(clave_fernet.encode().ljust(32)[:32]))

def verificar_password(plain_password: str, hashed_password: str) -> bool:
    """Verificar contraseña contra hash"""
    return pwd_context.verify(plain_password, hashed_password)

def obtener_password_hash(password: str) -> str:
    password = password[:72]   # 🔥 evita error de bcrypt
    return pwd_context.hash(password)

def encriptar_texto(texto: str) -> str:
    """Encriptar texto sensible"""
    texto_bytes = texto.encode()
    texto_encriptado = fernet.encrypt(texto_bytes)
    return texto_encriptado.decode()

def desencriptar_texto(texto_encriptado: str) -> str:
    """Desencriptar texto"""
    texto_bytes = texto_encriptado.encode()
    texto_desencriptado = fernet.decrypt(texto_bytes)
    return texto_desencriptado.decode()

def validar_fortaleza_password(password: str) -> dict:
    """Validar fortaleza de contraseña"""
    errores = []
    
    if len(password) < 8:
        errores.append("La contraseña debe tener al menos 8 caracteres")
    
    if not any(c.isupper() for c in password):
        errores.append("La contraseña debe tener al menos una mayúscula")
    
    if not any(c.islower() for c in password):
        errores.append("La contraseña debe tener al menos una minúscula")
    
    if not any(c.isdigit() for c in password):
        errores.append("La contraseña debe tener al menos un número")
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        errores.append("La contraseña debe tener al menos un carácter especial")
    
    return {
        "es_valida": len(errores) == 0,
        "errores": errores,
        "nivel_seguridad": "alta" if len(errores) == 0 else "media" if len(errores) <= 2 else "baja"
    }