import datetime
import enum
from typing import Annotated

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

from sql.database import Base

intpk = Annotated[int, mapped_column(primary_key=True)]
class StateDevice(enum.Enum):
    on = "on"
    off = "off"
    unknown = 'unknown'


class DeviceDataOrm(Base):
    __tablename__ = "device_data"

    id: Mapped[intpk]
    status: Mapped[str] = mapped_column(nullable=True)
    state: Mapped[StateDevice] = mapped_column(nullable=True)
    created_at: Mapped[str] = mapped_column(DateTime(), default=datetime.datetime.now)
    updated_at: Mapped[str] = mapped_column(DateTime(), default=datetime.datetime.now,onupdate=datetime.datetime.now)
    repr_cols_num = 2
    repr_cols = ("created_at", )
