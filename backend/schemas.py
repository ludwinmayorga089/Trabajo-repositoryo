from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class ProductoCreate(BaseModel):
    nombre: str
    precio: int

class ProductoResponse(BaseModel):
    id: int
    nombre: str
    precio: int
    class Config:
        orm_mode = True
