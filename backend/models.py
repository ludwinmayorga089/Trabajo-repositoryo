from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(100), unique=True, index=True)
    password = Column(String(255))
    role = Column(String(20), default="usuario")  # "usuario" o "admin"
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Producto(Base):
    __tablename__ = "productos"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(200), index=True)
    precio = Column(Float)
    descripcion = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ArchivosCargados(Base):
    __tablename__ = "archivos_cargados"
    
    id = Column(Integer, primary_key=True, index=True)
    nombre_archivo = Column(String(255), unique=True, index=True)
    fecha_carga = Column(DateTime(timezone=True), server_default=func.now())
    productos_insertados = Column(Integer, default=0)