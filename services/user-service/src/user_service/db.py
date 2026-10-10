from sqlmodel import create_engine, Session
import os

DB_URL = os.getenv("DB_URL", "sqlite:///database.db")

connection_args = {"check_same_thread":False} if DB_URL.startswith("sqlite") else {}

engine = create_engine(DB_URL, connect_args=connection_args)

def get_session():
    with Session(engine) as session:
        yield session