import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import Column, String, Integer, Uuid, Table, insert, delete, select, DateTime
from vinted_bot.models import engine, metadata

channel_bot_table = Table(
    "channels_bot",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("channel_id", String, nullable=False),
    Column("webhook_id", String, nullable=False),
    Column("webhook_name", String, nullable=False),
    Column("webhook_url", String, nullable=False),
    Column("created_at", DateTime, default=datetime.utcnow),
)


@dataclass
class ChannelsBot:
    id: uuid.UUID
    channel_id: str
    webhook_id: str
    webhook_name: str
    webhook_url: str
    created_at: datetime


def insert_channel_bot(channel_id, webhook_id, webhook_name, webhook_url) -> uuid.UUID:
    insert_statement = insert(channel_bot_table).values(
        id=uuid.uuid4(),
        channel_id=channel_id,
        webhook_id=webhook_id,
        webhook_name=webhook_name,
        webhook_url=webhook_url,
        created_at=datetime.utcnow()
    )
    with engine.begin() as conn:
        result = conn.execute(insert_statement)
    return result.inserted_primary_key[0]


def delete_channel_bot(channel_id) :
    delete_statement = delete(channel_bot_table).where(channel_bot_table.c.channel_id == channel_id)
    with engine.begin() as conn:
        result = conn.execute(delete_statement)


def get_channel_bot(channel_id) -> ChannelsBot | None:
    try:
        with engine.begin() as connection:
            result = connection.execute(channel_bot_table.select().where(channel_bot_table.c.channel_id == channel_id)).one()
        return ChannelsBot(*result)
    except Exception:
        return None


def get_all_channel_bot():
    with engine.begin() as connection:
        result = connection.execute(select(channel_bot_table)).all()
    return [ChannelsBot(*row) for row in result]

def update_webhook_name(channel_id, webhook_name):
    update_statement = channel_bot_table.update().where(channel_bot_table.c.channel_id == channel_id).values(webhook_name=webhook_name)
    with engine.begin() as conn:
        result = conn.execute(update_statement)