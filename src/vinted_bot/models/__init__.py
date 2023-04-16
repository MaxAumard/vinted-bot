from sqlalchemy import create_engine, MetaData

engine = create_engine(
    "sqlite:///vinted_bot.db",
    echo=False,
)
metadata = MetaData()


def init_db():
    metadata.create_all(engine)
init_db()
def delete_db():
    metadata.drop_all(engine)
