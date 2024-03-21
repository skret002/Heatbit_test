
import enum
import os
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel
from sqlalchemy import Column, DateTime, Enum, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base

from src.settings import settings
project_root = Path(__file__).parent.parent.parent
db_path = f"{project_root}{settings.db_path}"

# Создание строки подключения, используя абсолютный путь
engine = create_engine(f"{settings.db_connect}{db_path}", echo=True)
Base = declarative_base()


class StateDevice(enum.Enum):
    ON = "0x01"
    OFF = "0x02"
    unknown = "unknown"

class DeviceDataOrm(Base):
    __tablename__ = "device_data"

    id = Column(Integer, primary_key=True)
    status = Column(String(20), nullable=True)
    state = Column(Enum(StateDevice))
    created_on = Column(DateTime(), default=datetime.now)
    updated_on = Column(DateTime(), default=datetime.now, onupdate=datetime.now)

    @staticmethod
    def create_tables():
        if not os.path.exists(db_path):
            Base.metadata.create_all(engine)

class DeviceDataDTO(BaseModel):
    id: int
    task_name: str = "for_web"
    status: str
    state: str
    created_at: datetime
    updated_at: datetime
