import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.routers.auth import register
from app.schemas.user import UserRegister
import traceback

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

payload = UserRegister(username='testadmin3', email='admin3@test.com', password='password123')

try:
    register(payload, db)
    print("Success")
except Exception as e:
    traceback.print_exc()
