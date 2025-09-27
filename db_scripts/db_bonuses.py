# db_scripts/bonuses.py
from sqlalchemy import select, update
from Models import BonusBalance
from .db_session import get_session

def get_bonus_balance(contragent_id: int) -> float:
    with get_session() as s:
        row = s.scalar(select(BonusBalance.balance).where(BonusBalance.contragent_id == contragent_id))
        return row or 0.0

def set_bonus_balance(contragent_id: int, new_balance: float):
    with get_session() as s:
        # Проверяем, существует ли запись
        exists = s.scalar(select(BonusBalance.id).where(BonusBalance.contragent_id == contragent_id))
        if exists:
            s.execute(
                update(BonusBalance)
                .where(BonusBalance.contragent_id == contragent_id)
                .values(balance=new_balance)
            )
        else:
            s.add(BonusBalance(contragent_id=contragent_id, balance=new_balance))
        s.commit()

def add_bonus(contragent_id: int, amount: float):
    """Начислить бонусы."""
    old = get_bonus_balance(contragent_id)
    set_bonus_balance(contragent_id, old + amount)

def spend_bonus(contragent_id: int, amount: float):
    """Списать бонусы."""
    old = get_bonus_balance(contragent_id)
    if amount > old:
        raise ValueError("Недостаточно бонусов")
    set_bonus_balance(contragent_id, old - amount)