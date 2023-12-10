import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path
load_dotenv()
default_path = Path(__file__).parent.parent.parent

@dataclass
class DeviceOption:
    file_inp_name: str
    file_output_name: str
    file_inp_path: str
    file_output_path: str
    status_command: dict
    task_command: dict

def get_settings():
    os.path.abspath(__file__)
    return DeviceOption(
        file_inp_name = os.getenv('FILE_INPUT_NAME'),
        file_output_name = os.getenv('FILE_OUTPUT_NAME') ,
        file_inp_path = os.getenv('FILE_INPUT_PATH') or  default_path,
        file_output_path = os.getenv('FILE_OUTPUT_PATH') or  default_path,
        status_command = {'success':'0x00','error':'0x01','status':'0x02'},
        task_command = {'0x01':'devise_on', '0x02':'devise_off' , '0x03':'devise_status' }
    )
settings=get_settings()