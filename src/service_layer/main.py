"""
2. Сервис
Общается с устройством (через файлы input и output ), общается с управляющим
сервисом по WebSockets.
Каждые 10 секунд запрашивает статус устройства и отправляет его в управляющий
сервис.Умеет получать команды на включение/выключение устройства и отправлять их в само
устройство.
Пути к файлам input , output , настройки соединения WS необходимо хранить в файле
конфигурации, но так же должна быть возможность переопределить через environment.
"""
import json
import os
import sys
import threading
import time
from enum import Enum
from pathlib import Path

import websockets
from loguru import logger
from pydantic import BaseModel
from websockets.sync.client import connect

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
src_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(src_directory)
from device_emulator.main import Task  # noqa: E402
from sql.orm import ORM  # noqa: E402
from src.settings import settings  # noqa: E402

logger.add("device.log", rotation="50 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
class DeviceCommand(Enum):
    ON = "0x01"
    OFF = "0x02"
    GET_STATUS = "0x03"


class BridgeForDevice:
    def __init__(self, default_file_path):
        self.default_path = default_file_path
        self.incoming_message = []
        self.last_update_status = time.time()

class StatusDTO(BaseModel):
    sender_name: str = 'layer'
    task_name: str
    device_name: str
    response_code: str

class BridgeForDeviceWithWebsocket(BridgeForDevice):
    def __init__(self, default_file_path):
        super().__init__(default_file_path)

    def get_status(self):
        device_name='divice_1'
        response_code= Task().device_status()
        return(device_name,response_code)

    def check_device_status(self):
        data_status=self.get_status()
        status_dto=StatusDTO(**{'task_name': 'device_status_timeout10',
                                'device_name': data_status[0],
                                'response_code': data_status[1]})
        return json.dumps(status_dto.model_dump_json())

    def receive_messages(self, websocket: websockets):
        while True:
            try:
                message = json.loads(websocket.recv())
                if not self.validate_task(['device_status_timeout10', 'for_web'], message['task_name']):
                    logger.info(f'Получена новая задача для эмулятора {message}')
                    self.incoming_message.append(message)
            except (websockets.exceptions.ConnectionClosed, TypeError) as e:
                logger.error(f'websockets.exceptions.ConnectionClosed -  {e}')

    def transfer_respons_from_device(self):
        with open(f'{self.default_path}/output', "r") as f:
            response = f.read()
            logger.info(f'Получен код ответа output - {response}')
        if len(response) != 0:
            return response
        logger.error('Device offline')
        return 'Device offline'

    def transfer_command_to_device(self, command: str) ->str:
        with open(f'{self.default_path}/input', "w") as f:
            logger.info(f'Запись команды в input - {command}')
            f.write(command)
        return self.transfer_respons_from_device()

    def push_sql_data_to_web(self, ws: websockets):
        if data := ORM.convert_device_data_to_dto():
            logger.info(f'Получены данные для web - {data}')
            ws.send(data)
        else:
            logger.error('Ошибка получения данный в валидаторе ORM.convert_device_data_to_dto()')
    @staticmethod
    def clean_file(path: str, name: str):
        with open(f'{path}/{name}', "wb") as f:
            pass
    def check_freelance_request_status(self, code: str, ws: websockets) -> bool:
        if code == DeviceCommand.GET_STATUS.value:
            self.clean_file(settings.file_inp_path,settings.file_inp_name) # очищаем старый ответ
            self.transfer_command_to_device(DeviceCommand.GET_STATUS.value)
            logger.info('Получены внештатный запрос состояния эмулятора')
            time.sleep(2)# даем время устройству на ответ
            status_dto=StatusDTO(**{'task_name': 'device_status_timeout10',
                                'device_name': self.get_status()[0],
                                'response_code': self.transfer_respons_from_device()}) #по нажатию кнопки мы возьмем статус из output
            response_status=json.dumps(status_dto.model_dump_json())
            ws.send(response_status)
            logger.info(f'Получены ответ {response_status} на внештатный запрос состояния эмулятора')
            return True
    def main(self, ws: websockets):
        while True:
            if time.time() - self.last_update_status >= 10:
                response_status = self.check_device_status()
                ws.send(response_status)
                self.push_sql_data_to_web(ws)  # Push data from the database to the web every 10 seconds for convenience
                self.last_update_status = time.time()
                logger.info(f'Прошло 10сек, отправляю в main сервис данные - {response_status}')
            if len(self.incoming_message) > 0:
                logger.info(f'Появилась задача для эмулятора, передаю {self.incoming_message[0]["task_name"]}')
                time.sleep(5)
                if self.check_freelance_request_status(self.incoming_message[0]['task_name'], ws):
                    self.incoming_message.pop(0)
                    continue
                response = self.transfer_command_to_device(self.incoming_message[0]['task_name'])
                logger.info(f'Ответ эмулятора, перенаправляю {response}')
                status_dto = StatusDTO(task_name=self.incoming_message[0]['task_name'],
                                       device_name='divice_1',
                                       response_code=response)
                self.incoming_message.pop(0)
                ws.send(status_dto.model_dump_json())
#
    def start(self, ws: websockets):
        threads = [threading.Thread(target=self.receive_messages, args=(ws,)),
                   threading.Thread(target=self.main, args=(ws,))
                   ]
        for thread in threads:
            thread.start()
        while True:
            to_send = input()
            ws.send(to_send)


    def validate_task(self,not_necessary_tasks: list, message: str)-> bool:
        necessary = any(task in message for task in not_necessary_tasks)
        duplicate = False
        try:
            if message ==  self.incoming_message[-1]['task_name']:
                duplicate = True
        except (KeyError,IndexError):
             ...
        if necessary or duplicate:
            return True

if __name__ == '__main__':
    logger.info(f'Запуск клиента на адресе {f"ws://{settings.ws_host}:{settings.ws_port}"}')
    default_path = Path(__file__).parent.parent.parent
    with connect(f"ws://{settings.ws_host}:{settings.ws_port}") as ws:
        device_manager = BridgeForDeviceWithWebsocket(default_path)
        device_manager.start(ws)