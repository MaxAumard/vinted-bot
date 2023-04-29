import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, String, Integer, Uuid, Table, insert, delete, select, DateTime
from vinted_bot.models import engine, metadata
from vinted_bot.models.channels_bot import get_channel_bot

search_table = Table(
    "searches",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("channel_id", String, nullable=False),
    Column("webhook_url", String, nullable=False),
    Column("add_at", DateTime, default=datetime.utcnow),
    Column("search", String, nullable=False),
    Column("max_price", Integer, nullable=True),
)


@dataclass
class Search:
    id: uuid.UUID
    channel_id: str
    webhook_url: str
    add_at: datetime
    search: str
    max_price: int


def insert_search(channel_id, search, max_price) -> uuid.UUID:
    insert_statement = insert(search_table).values(
        id=uuid.uuid4(),
        channel_id=channel_id,
        webhook_url=get_channel_bot(channel_id).webhook_url,
        search=search,
        add_at=datetime.utcnow(),
        max_price=max_price,
    )
    with engine.begin() as conn:
        result = conn.execute(insert_statement)
    return result.inserted_primary_key[0]


def delete_search(channel_id, search):
    delete_statement = delete(search_table).where(search_table.c.channel_id == channel_id).where(
        search_table.c.search == search)
    with engine.begin() as conn:
        result = conn.execute(delete_statement)


def get_searches_by_channel(channel_id) -> list[Search] | None:
    try:
        with engine.begin() as connection:
            result = connection.execute(search_table.select().where(search_table.c.channel_id == channel_id)).all()
        return [Search(*row) for row in result]
    except Exception:
        return None


def get_all_searches() -> list[Search] | None:
    try:
        with engine.begin() as connection:
            result = connection.execute(search_table.select().distinct(search_table.c.search)).all()
        return [Search(*row) for row in result]
    except Exception:
        return None


def delete_search_by_channel(channel_id):
    delete_statement = delete(search_table).where(search_table.c.channel_id == channel_id)
    with engine.begin() as conn:
        result = conn.execute(delete_statement)

def get_searches_by_search(search) -> list[Search] | None:
    try:
        with engine.begin() as connection:
            result = connection.execute(search_table.select().where(search_table.c.search == search)).all()
        return [Search(*row) for row in result]
    except Exception:
        return None