from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel, EmailStr
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional, List
import openpyxl
import json
from io import BytesIO
import asyncio

from database import get_db, engine, Base
from models import User, Producto, ArchivosCargados
from auth import create_access_token, get_current_user, admin_required

# === CREAR TABLAS ===
Base.metadata.create_all(bind=engine)

app = FastAPI()

SECRET_KEY = "clave_super_secreta_cambiar_en_produccion_123"
ALGORITHM = "HS256"
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# === CORS ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === ESQUEMAS PYDANTIC ===
class UserCreate(BaseModel):
    email: str
    password: str
    role: str = "usuario"

class UserResponse(BaseModel):
    id: int
    email: str
    role: str
    class Config:
        from_attributes = True

class ProductoCreate(BaseModel):
    nombre: str
    precio: float
    descripcion: Optional[str] = None

class ProductoResponse(BaseModel):
    id: int
    nombre: str
    precio: float
    descripcion: Optional[str] = None
    class Config:
        from_attributes = True

class ProductoUpdate(BaseModel):
    nombre: Optional[str] = None
    precio: Optional[float] = None
    descripcion: Optional[str] = None

# === FUNCIONES AUXILIARES ===
def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# === AUTH ENDPOINTS ===
@app.post("/api/auth/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    # Validar que no exista
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya existe")
    
    # Crear usuario
    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return {"msg": "Usuario registrado", "user": UserResponse.from_orm(new_user)}

@app.post("/api/auth/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Username aquí es el email
    user = db.query(User).filter(User.email == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
    
    token = create_access_token({
        "sub": user.email,
        "user_id": user.id,
        "role": user.role
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": UserResponse.from_orm(user)
    }

@app.get("/api/auth/me")
def get_me(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserResponse.from_orm(user)

# === USUARIOS ENDPOINTS (Solo Admin) ===
@app.get("/api/usuarios")
def list_usuarios(
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    usuarios = db.query(User).all()
    return [UserResponse.from_orm(u) for u in usuarios]

@app.get("/api/usuarios/{user_id}")
def get_usuario(
    user_id: int,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return UserResponse.from_orm(usuario)

@app.put("/api/usuarios/{user_id}")
def update_usuario(
    user_id: int,
    user_update: UserCreate,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.email = user_update.email
    usuario.password = hash_password(user_update.password)
    usuario.role = user_update.role
    
    db.commit()
    db.refresh(usuario)
    return UserResponse.from_orm(usuario)

@app.delete("/api/usuarios/{user_id}")
def delete_usuario(
    user_id: int,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    usuario = db.query(User).filter(User.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    db.delete(usuario)
    db.commit()
    return {"msg": "Usuario eliminado"}


@app.post("/api/usuarios")
def create_usuario(
    user: UserCreate,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Validar que no exista
    existing = db.query(User).filter(User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email ya existe")
    
    # Crear usuario
    new_user = User(
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse.from_orm(new_user)

# === PRODUCTOS ENDPOINTS ===
@app.get("/api/productos")
def list_productos(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    productos = db.query(Producto).all()
    return [ProductoResponse.from_orm(p) for p in productos]

@app.get("/api/productos/{producto_id}")
def get_producto(
    producto_id: int,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return ProductoResponse.from_orm(producto)

@app.post("/api/productos")
def create_producto(
    producto: ProductoCreate,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Verificar si el producto ya existe (por nombre)
    producto_existente = db.query(Producto).filter(
        Producto.nombre == producto.nombre.strip()
    ).first()
    
    if producto_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"Producto ya existe: '{producto.nombre}'"
        )
    
    new_producto = Producto(
        nombre=producto.nombre.strip(),
        precio=producto.precio,
        descripcion=producto.descripcion.strip() if producto.descripcion else None
    )
    db.add(new_producto)
    db.commit()
    db.refresh(new_producto)
    return ProductoResponse.from_orm(new_producto)

@app.put("/api/productos/{producto_id}")
def update_producto(
    producto_id: int,
    producto: ProductoUpdate,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    db_producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    if producto.nombre:
        db_producto.nombre = producto.nombre
    if producto.precio:
        db_producto.precio = producto.precio
    if producto.descripcion:
        db_producto.descripcion = producto.descripcion
    
    db.commit()
    db.refresh(db_producto)
    return ProductoResponse.from_orm(db_producto)

@app.delete("/api/productos/{producto_id}")
def delete_producto(
    producto_id: int,
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(producto)
    db.commit()
    return {"msg": "Producto eliminado"}

# === UPLOAD XLS CON PROGRESO EN VIVO ===
@app.post("/api/upload/productos")
async def upload_productos(
    file: UploadFile = File(...),
    current_user: dict = Depends(admin_required),
    db: Session = Depends(get_db)
):
    # Validar extensión
    if not file.filename.endswith(('.xls', '.xlsx')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos XLS/XLSX")
    
    # Verificar si el archivo ya fue cargado anteriormente
    archivo_existente = db.query(ArchivosCargados).filter(
        ArchivosCargados.nombre_archivo == file.filename
    ).first()
    
    if archivo_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"Documento ya utilizado: '{file.filename}' fue cargado el {archivo_existente.fecha_carga.strftime('%d/%m/%Y %H:%M')}"
        )
    
    # Leer archivo
    contents = await file.read()
    wb = openpyxl.load_workbook(BytesIO(contents))
    ws = wb.active
    
    errores = []
    insertados = 0
    productos_duplicados = []
    filas = ws.max_row - 1  # Excluir encabezado
    
    for idx, row in enumerate(ws.iter_rows(min_row=2, values_only=True), 1):
        try:
            nombre, precio, descripcion = row[0], row[1], row[2] if len(row) > 2 else None
            
            if not nombre or precio is None:
                errores.append(f"Fila {idx+1}: Campos requeridos vacíos")
                continue
            
            # Validar precio sea número
            try:
                precio = float(precio)
            except:
                errores.append(f"Fila {idx+1}: Precio no es un número válido")
                continue
            
            # Verificar si el producto ya existe (por nombre)
            producto_existente = db.query(Producto).filter(
                Producto.nombre == str(nombre).strip()
            ).first()
            
            if producto_existente:
                productos_duplicados.append(f"Producto ya existe: '{nombre}'")
                continue
            
            # Insertar producto nuevo
            new_producto = Producto(
                nombre=str(nombre).strip(),
                precio=precio,
                descripcion=str(descripcion).strip() if descripcion else None
            )
            db.add(new_producto)
            insertados += 1
            
        except Exception as e:
            errores.append(f"Fila {idx+1}: {str(e)}")
    
    # Si hay productos duplicados, no guardar nada y retornar error
    if productos_duplicados:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail={
                "mensaje": "Se encontraron productos duplicados",
                "duplicados": productos_duplicados
            }
        )
    
    # Guardar todos los productos
    db.commit()
    
    # Registrar el archivo como cargado
    nuevo_archivo = ArchivosCargados(
        nombre_archivo=file.filename,
        productos_insertados=insertados
    )
    db.add(nuevo_archivo)
    db.commit()
    
    return {
        "insertados": insertados,
        "total": filas,
        "errores": errores + productos_duplicados,
        "porcentaje": round((insertados / filas * 100) if filas > 0 else 0, 2),
        "mensaje": f"Archivo '{file.filename}' procesado correctamente"
    }