import asyncio
from typing import Annotated
from pathlib import Path
from sqlalchemy import String, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
default_path = Path(__file__).parent.parent

sync_engine = create_engine(
    url=f"sqlite:///{default_path}/sql/user_db.db",
    echo=False,
)

session_factory = sessionmaker(sync_engine)



class Base(DeclarativeBase):
    repr_cols_num = 3

    def __repr__(self):
        cols = []
        for idx, col in enumerate(self.__table__.columns.keys()):
            if col in self.repr_cols or idx < self.repr_cols_num:
                cols.append(f"{col}={getattr(self, col)}")

        return f"<{self.__class__.__name__} {', '.join(cols)}>"
