"""
Script para inicializar la base de datos con usuarios de prueba
Ejecutar: python init_db.py
"""
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database import SessionLocal, engine, Base
from models import User, Producto

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def init_database():
    # Crear todas las tablas
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existen usuarios
        existing_users = db.query(User).count()
        
        if existing_users == 0:
            print("🔧 Creando usuarios de prueba...")
            
            # Crear admin
            admin = User(
                email="admin@demo.com",
                password=hash_password("123"),
                role="admin"
            )
            db.add(admin)
            
            # Crear usuario normal
            user = User(
                email="user@demo.com",
                password=hash_password("123"),
                role="usuario"
            )
            db.add(user)
            
            db.commit()
            print("✅ Usuarios creados:")
            print("   - admin@demo.com / 123 (Administrador)")
            print("   - user@demo.com / 123 (Usuario)")
        else:
            print(f"ℹ️  Ya existen {existing_users} usuarios en la base de datos")
        
        # Crear productos de ejemplo
        existing_products = db.query(Producto).count()
        
        if existing_products == 0:
            print("\n🔧 Creando productos de ejemplo...")
            
            productos_demo = [
                Producto(nombre="Laptop HP", precio=899.99, descripcion="Laptop 15.6 pulgadas"),
                Producto(nombre="Mouse Logitech", precio=29.99, descripcion="Mouse inalámbrico"),
                Producto(nombre="Teclado Mecánico", precio=120.00, descripcion="RGB retroiluminado"),
                Producto(nombre="Monitor LG 27\"", precio=299.99, descripcion="Monitor Full HD"),
                Producto(nombre="Audífonos Sony", precio=89.50, descripcion="Bluetooth con cancelación"),
            ]
            
            for producto in productos_demo:
                db.add(producto)
            
            db.commit()
            print(f"✅ {len(productos_demo)} productos de ejemplo creados")
        else:
            print(f"ℹ️  Ya existen {existing_products} productos en la base de datos")
        
        print("\n🎉 Base de datos inicializada correctamente")
        
    except Exception as e:
        print(f"❌ Error al inicializar: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 INICIALIZANDO BASE DE DATOS")
    print("=" * 50)
    init_database()
    print("=" * 50)