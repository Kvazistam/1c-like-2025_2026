from __future__ import annotations
import hashlib

from sqlalchemy import (
    select
)

from Models import *
from db_scripts.db_session import get_session

# --- Пользователи (для будущего входа) ---


def user_add(username: str, plain_password: str, role: str) -> None:
    ph = hashlib.sha256(plain_password.encode()).hexdigest()
    with get_session() as s:
        s.add(User(username=username, passhash=ph, role=role))
        s.commit()


def user_check(username: str, plain_password: str) -> tuple[bool, str]:
    ph = hashlib.sha256(plain_password.encode()).hexdigest()
    with get_session() as s:
        u = s.scalar(select(User).where(User.username == username))
        if u and u.passhash == ph:
            return True, u.role
        return False, ''
