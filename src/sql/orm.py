import json
import os
from datetime import datetime

from pydantic import BaseModel
from sql.database import Base, session_factory, sync_engine
from sql.models import DeviceDataOrm
from sqlalchemy import insert, select


class DeviceDataDTO(BaseModel):
    id: int
    task_name: str ='for_web'
    status: str
    state: str
    created_at: datetime
    updated_at: datetime

class ORM:
    @staticmethod
    def create_tables():
        # Проверяем, существует ли файл базы данных
        db_file_path = "../sql/user_db.db"
        if not os.path.exists(db_file_path):
            sync_engine.echo = False
            Base.metadata.drop_all(sync_engine)
            Base.metadata.create_all(sync_engine)
            sync_engine.echo = True
        else:
            print("Файл базы данных уже существует.")

    @staticmethod
    def insert_or_update(status: str = 'unknown',state: str='unknown'):
        print(f'входящие данные tatus-{status}  state-{state}')
        data = [
                {"status": status,"state":state},
        ]
        with session_factory() as session:
            sql_data=session.query(DeviceDataOrm).first()
            print('>',sql_data)
            if sql_data is None:
                insert_data= insert(DeviceDataOrm).values(data)
                session.execute(insert_data)
            else:
                sql_data.status = status if status !='unknown' else sql_data.status
                sql_data.state = state if state !='unknown' else sql_data.state
            session.commit()

    def convert_device_data_to_dto():
        with session_factory() as session:
            query = (
                select(DeviceDataOrm)
            )
            res = session.execute(query)
            result_orm = res.scalars().all()
            try:
                ready_data = [
                    DeviceDataDTO.model_validate(row, from_attributes=True
                                                 ).model_dump_json()
                    for row in result_orm][0]
            except Exception:
                return False
            print('ready_data',ready_data)
            return json.dumps(ready_data)