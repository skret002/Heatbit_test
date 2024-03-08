"""
1. Эмулятор устройства
Отслеживает изменение файла input . В этот файл будут писаться команды сервисом
#2. В файл output пишет результат выполнения команды.
Необходима возможность задать пути к файлам input и output через environment
переменные при запуске.
Команды эмулятора
0x01 - Включить устройство
0x02 - Выключить устройство
0x03 - Получить статус
Ответы на команды
0x00 - Успешное выполнение команды
0x01 - Ошибка выполнения команды
0x02 {random_number} - Статус у
"""
import sys
import time
from random import randint
from abc import ABC,abstractmethod
from loguru import logger
sys.path.insert(1, '../../')
from src.settings import settings


logger.add("device.log", rotation="50 MB", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}")
"""
1. Отслеживает изменение файла input . В этот файл будут писаться команды сервисом
2. В файл output пишет результат выполнения команды.
"""
class TaskAbs(ABC):  # Абстрактный класс делаю как контракт, что бы в дальнейшем эти методы были обязательно реализованы

    @abstractmethod
    def device_on():
        ...
    @abstractmethod
    def device_off():
        ...
    @abstractmethod
    def device_status():
        ...

class Task(TaskAbs):
    def __init__(self):   # дедаю через init для того, что бы при необходимости легко можно было поменять в settings значения и все.
        self.success = settings.status_command['success']
        self.error = settings.status_command['error']
        self.status = settings.status_command['status']

    def device_on(self):
        return self.success

    def device_off(self):
        return self.success

    def device_status(self):
        logger.info('Устройство получил запрос статуса')
        status = randint(0,255)
        logger.info(f'Устройство отдает  статус {self.status} {status}')
        return f'{self.status} {status}'
    def set_command(self,command):   # есть ведь вероятность увеличения списка команд, надо подумать как сделать красивее
        if command == 'devise_on':
            return self.device_on()
        elif command == 'devise_off':
            return self.device_off()
        return self.device_status()

def clean_file(path: str, name: str):
    with open(f'{path}/{name}', "wb") as f:
        pass

def read_input_file(path: str, name: str) -> str or None:
    with open(f'{path}/{name}', "r") as f:
        return f.read()

def write_info(path: str, name: str, info: str) ->None:
    print('Путь',f'{path}/{name}',info)
    with open(f'{path}/{name}', "w") as f:
        f.write(info)


"""
В решении этой части задачи я что то погорячился. Понятно что ее можно было решить в одном цикле.
"""

def main():  # sourcery skip: hoist-similar-statement-from-if, hoist-statement-from-if
    logger.info("Запуск")
    while True:
        time.sleep(1)
        task = read_input_file(settings.file_inp_path,settings.file_inp_name) #считываем файл input
        if task in settings.task_command: # Если файл не пустой и есть соотвествующая команда из набора в settings
            logger.info(f'Устройство получил команду - {task}')
            response = Task().set_command(settings.task_command[task])  #отправили на выполнение
            logger.info(f'Результат выполнение команды устройством - {response}')
            write_info(settings.file_output_path , settings.file_output_name , response) #Записали ответ
            clean_file(settings.file_inp_path,settings.file_inp_name) #почему этот код дублирован, если вынести за условие, команда может придти после считывания и будет удалена
            logger.info('Файл input очищен')
        elif len(task) > 0:
            write_info(settings.file_output_path , settings.file_output_name , settings.status_command['error'])  # если команда не верная кладем ответ неудачи
            logger.error(f'Получен не существующий код команды - {task}')
            clean_file(settings.file_inp_path,settings.file_inp_name) #почему этот код дублирован, если вынести за условие, команда может придти после считывания и будет удалена


if __name__ == '__main__':
    main()