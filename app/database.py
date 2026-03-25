import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://admin:password@db:5432/soap_history")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class SOAPHistory(Base):
    __tablename__ = "soap_history"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    dialog = Column(Text)
    soap_result = Column(Text)
    mode = Column(String)

# создаем таблицы
Base.metadata.create_all(bind=engine)

def save_log(dialog: str, soap: dict, mode: str):
    db = SessionLocal()
    try:
        new_log = SOAPHistory(
            dialog=dialog,
            soap_result=str(soap),
            mode=mode
        )
        db.add(new_log)
        db.commit()
    finally:
        db.close()