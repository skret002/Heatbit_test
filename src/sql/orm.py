import sys
import json
sys.path.insert(1, '/')
sys.path.insert(1, '../')
from sqlalchemy import insert, select
from pydantic import BaseModel
from datetime import datetime
from sql.database import Base, sync_engine,session_factory
from sql.models import DeviceDataOrm

class DeviceDataDTO(BaseModel):
    id: int
    task_name: str ='for_web'
    status: str
    state: str
    created_at: datetime
    updated_at: datetime

class ORM:
    # Асинхронный вариант, не показанный в видео
    @staticmethod
    def create_tables():
        sync_engine.echo = False
        Base.metadata.drop_all(sync_engine)
        Base.metadata.create_all(sync_engine)
        sync_engine.echo = True

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
                    for row in result_orm
                ][0]
            except Exception as e:
                print('Ошибка в ORM',e)
                return False
            print('ready_data',ready_data)
            return json.dumps(ready_data)