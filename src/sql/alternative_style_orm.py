import os
import sys
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.settings import settings

from .alternative_style_models import DeviceDataDTO, DeviceDataOrm, StateDevice

src_directory = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
sys.path.append(src_directory)
project_root = Path(__file__).parent.parent.parent
db_path = f"{project_root}{settings.db_path}"
engine = create_engine(f"{settings.db_connect}{db_path}", echo=True)
# Создание строки подключения, используя абсолютный путь
Base = declarative_base()
Session = sessionmaker(bind=engine)


class ORM:
    @staticmethod
    def insert_or_update(status: str = "unknown", state: str = "unknown"):
        if not os.path.exists(db_path):
            DeviceDataOrm.create_tables()
        with Session() as session:
            sql_data = (
                session.query(DeviceDataOrm).filter_by(id=1).first()
            )
            if sql_data is None:
                new_data = DeviceDataOrm(
                    status=status, state=StateDevice[state])
                session.add(new_data)
            else:
                sql_data.status = status if status != "unknown" else sql_data.status
                sql_data.state = (
                    StateDevice[state] if state != "unknown" else sql_data.state
                )
            session.commit()

    @staticmethod
    def convert_device_data_to_dto():
        with Session() as session:
            query = session.query(DeviceDataOrm).filter_by(id=1).first()
            print("query", query.status)
            if query is None:
               return False
            try:
               state_value = (
                   query.state.value
                   if isinstance(query.state, StateDevice)
                   else query.state
               )
               ready_data = DeviceDataDTO(
                   id=query.id,
                   status=query.status,
                   state=state_value,
                   created_at=query.created_on,
                   updated_at=query.updated_on,
               )
            except Exception:
               return False
        return ready_data.json()