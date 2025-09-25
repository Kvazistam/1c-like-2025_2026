from __future__ import annotations
import hashlib
import os
from datetime import date, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    create_engine, Date, or_,
    select, delete, func, event, update
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import selectinload
from sqlalchemy.orm import (
    Session
)

from Models import *
from enumerates import DOC_TYPES


DB_PATH= os.path.join(os.path.dirname(__file__), "..", "anime1c.db")
DB_URL = f"sqlite:///{DB_PATH}"

# ---- engine ----
engine: Engine = create_engine(DB_URL, echo=False, future=True)


# ---- FK включить для SQLite ----
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# ---- создание таблиц ----
def create_tables():
    Base.metadata.create_all(engine)


# ---- CRUD-обёртки ----
def get_session() -> Session:
    return Session(engine, future=True)


# --- Миграция / создание всего ---
def migrate():
    create_tables()
