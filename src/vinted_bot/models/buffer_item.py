import uuid
from dataclasses import dataclass
from sqlalchemy import Column, String, Table, insert, delete, Uuid

from vinted_bot.models import metadata, engine

buffer_item_table = Table(
    "buffer_item",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("search", String, nullable=False),
    Column("image", String, nullable=False),
    Column("price", String, nullable=False),
    Column("title", String, nullable=False),
    Column("url", String, nullable=False),
)


@dataclass
class Item:
    id: uuid.UUID
    search: str
    image: str
    price: str
    title: str
    url: str


def insert_buffer_item(id, search, image, price, title, url) -> str:
    insert_statement = insert(buffer_item_table).values(
        id=uuid.uuid4(),
        search=search,
        image=image,
        price=price,
        title=title,
        url=url,
    )
    with engine.begin() as conn:
        result = conn.execute(insert_statement)
    return result.inserted_primary_key[0]


def get_buffer_items(search) -> list[Item] | None:
    try:
        with engine.begin() as connection:
            result = connection.execute(buffer_item_table.select().where(buffer_item_table.c.search == search)).all()
        return [Item(*row) for row in result]
    except Exception:
        return None


def delete_buffer_item(search):
    delete_statement = delete(buffer_item_table).where(buffer_item_table.c.search == search)
    with engine.begin() as conn:
        result = conn.execute(delete_statement)
