"""
CRUD-операции для справочника «Единицы измерения»
"""

from typing import List, Dict, Any, Optional

from sqlalchemy import or_, select
from Models import Item, UnitOfMeasure
from enumerates import ITEM_TYPES
from .db_session import get_session

def unit_list_for_item(item_id: int) -> List[Dict[str, Any]]:
    """Возвращает ЕИ, доступные для данного товара."""
    with get_session() as s:
        item = s.get(Item, item_id)
        if not item:
            return []

        stmt = select(UnitOfMeasure.id, UnitOfMeasure.name)
        
        stmt = stmt.where(UnitOfMeasure.applicable_to == item.item_type)
            
        rows = s.execute(stmt).mappings().all()
        return [dict(r) for r in rows]


def unit_list_all() -> List[Dict[str, Any]]:
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

def unit_list_applicable(applicable_to = ITEM_TYPES[0]):
    """
    Возвращает список всех доступных единиц измерения.
    """
    with get_session() as s:
        rows = s.execute(
            select(UnitOfMeasure.id, 
                   UnitOfMeasure.name, 
                   UnitOfMeasure.ratio_to_base, 
                   UnitOfMeasure.weight, 
                   UnitOfMeasure.volume).order_by(UnitOfMeasure.name)
            .where(UnitOfMeasure.applicable_to == applicable_to)
        ).mappings().all()
        return [dict(row) for row in rows]

def unit_add(
    name: str,
    ratio_to_base: float,
    weight: Optional[float] = None,
    volume: Optional[float] = None,
    applicable_to = ITEM_TYPES[0]
) -> int:
    """
    Добавляет новую единицу измерения.
    
    :param name: Название (например, "Коробка")
    :param ratio_to_base: Сколько базовых единиц в этой единице (например, 50000 для коробки сахара в граммах)
    :param weight: Вес одной единицы (в кг, опционально)
    :param volume: Объём одной единицы (в литрах, опционально)
    :param applicable_to: тип объекта.
    :return: ID новой записи
    """
    with get_session() as s:
        u = UnitOfMeasure(
            name=name,
            ratio_to_base=ratio_to_base,
            weight=weight,
            volume=volume,
            applicable_to=applicable_to
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
            
            
