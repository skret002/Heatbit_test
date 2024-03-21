"""
3. Управляющий сервис
Хранит состояние в  базе данных:
Состояние вкл/выкл
Статус (число)
По каким-либо триггерам (для удобства тестирования), должен уметь отправить
команду на включение или выключение устройства.
"""
import asyncio
import contextlib
import json
import os
import sys
from enum import Enum

import websockets
from loguru import logger
from pydantic import BaseModel

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
src_directory = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(src_directory)
from sql.alternative_style_orm import ORM
#from sql.orm import ORM
from src.settings import settings


class TaskToJson(BaseModel):
    task_name: str

class DeviceCommand(Enum):
    ON = "0x01"
    OFF = "0x02"


class HandlerTask:
    def __init__(self, server=None):
        self.server = server

    def set_server(self, server):
        self.server = server

    async def handler_task(self,button: list, check_message: dict) ->None:
        if check_message['task_name'] == 'command':
            message = json.dumps({'task_name': check_message['task_for_devise']})
            logger.info(f'Получена задача от тригера {check_message["task_for_devise"]}')
            with contextlib.suppress(KeyError):
                task_for_device = check_message.get('task_for_devise')
                if task_for_device in button.values():
                    task_name = button[task_for_device]
                    ORM.insert_or_update(None, task_name)
                else:
                    ...  # запрос состояния девайса, в бд отписывать не нужно
            await self.server.broadcast(message)  # отправляю задачу в сервис прослуйку

        elif check_message['task_name'] == 'device_status_timeout10':
            logger.info(f'Получено состояние эмулятора по таймауту {check_message}')
            ORM.insert_or_update(check_message['response_code'])
            logger.info(f'Отправляем код ответа в бд, код-{check_message["response_code"]}')
        elif check_message['task_name'] == 'for_web':
            await self.server.broadcast(json.dumps(check_message))
            logger.info(f'Отправляю данные на WEB {check_message}')
class WebSocketServer:
    def __init__(self):
        self.client_list = []
        self.button = {DeviceCommand.ON.value: "on", DeviceCommand.OFF.value: "off"}
        self.handler_task = HandlerTask()
        self.handler_task.set_server(self)

    async def get_message(self, websocket):
        try:
            return await websocket.recv()
        except websockets.exceptions.ConnectionClosed:
            logger.error('websockets.exceptions.ConnectionClosed')
            return None

    async def convert_json_to_dict(self, message: str) -> dict:
        try:
            check_message = json.loads(json.loads(message))
        except TypeError:
            check_message = json.loads(message)
        return check_message

    async def broker(self, websocket: websockets) -> None:
        while True:
            self.client_list.append(websocket)
            try:
                message = await self.get_message(websocket)
                check_message = await self.convert_json_to_dict(message)
                await self.handler_task.handler_task(self.button, check_message)
            except (websockets.exceptions.ConnectionClosed, TypeError) as e:
                logger.error(f'websockets.exceptions.ConnectionClosed -  {e}')
                self.client_list.remove(websocket)
    async def broadcast(self, message: str):
        for client in self.client_list:
            if client.open:
                await client.send(message)
            else:
                logger.error(f"клиент-{client} больше не на связи")
                self.client_list.remove(client)

    async def main(self):
        logger.info(
            f'Запуск сервера на адресе {f"ws://{settings.ws_host}:{settings.ws_port}"}'
        )
        event = asyncio.Event()
        async with websockets.serve(
            self.broker,
            settings.ws_host,
            settings.ws_port,
            timeout=10,
            ping_interval=None,
        ):
            await event.wait()


if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.run(server.main())