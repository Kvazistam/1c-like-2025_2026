"""
CRUD-операции для справочника «Единицы измерения»
"""

from typing import List, Dict, Any, Optional

from sqlalchemy import select
from Models import UnitOfMeasure
from .db_session import get_session

def unit_list_for_item(item_id: int) -> List[Dict[str, Any]]:
    """
    Возвращает все единицы измерения, доступные для товара.
    Пока возвращает все ЕИ (можно расширить логикой привязки к товару).
    """
    return unit_list()


def unit_list() -> List[Dict[str, Any]]:
    """
    Возвращает список всех единиц измерения.
    """
    with get_session() as s:
        rows = s.execute(
            select(UnitOfMeasure.id, 
                   UnitOfMeasure.name, 
                   UnitOfMeasure.ratio_to_base, 
                   UnitOfMeasure.weight, 
                   UnitOfMeasure.volume).order_by(UnitOfMeasure.name)
        ).mappings().all()
        return [dict(row) for row in rows]


def unit_add(
    name: str,
    ratio_to_base: float,
    weight: Optional[float] = None,
    volume: Optional[float] = None
) -> int:
    """
    Добавляет новую единицу измерения.
    
    :param name: Название (например, "Коробка")
    :param ratio_to_base: Сколько базовых единиц в этой единице (например, 50000 для коробки сахара в граммах)
    :param weight: Вес одной единицы (в кг, опционально)
    :param volume: Объём одной единицы (в литрах, опционально)
    :return: ID новой записи
    """
    with get_session() as s:
        u = UnitOfMeasure(
            name=name,
            ratio_to_base=ratio_to_base,
            weight=weight,
            volume=volume
        )
        s.add(u)
        s.commit()
        return u.id


def unit_get(unit_id: int) -> Optional[Dict[str, Any]]:
    """
    Получает единицу измерения по ID.
    """
    with get_session() as s:
        u = s.get(UnitOfMeasure, unit_id)
        return u.__dict__ if u else None


def unit_update(
    unit_id: int,
    name: str,
    ratio_to_base: float,
    weight: Optional[float] = None,
    volume: Optional[float] = None
) -> None:
    """
    Обновляет существующую единицу измерения.
    """
    with get_session() as s:
        u = s.get(UnitOfMeasure, unit_id)
        if u:
            u.name = name
            u.ratio_to_base = ratio_to_base
            u.weight = weight
            u.volume = volume
            s.commit()


def unit_delete(unit_id: int) -> None:
    """
    Удаляет единицу измерения.
    """
    with get_session() as s:
        u = s.get(UnitOfMeasure, unit_id)
        if u:
            s.delete(u)
            s.commit()