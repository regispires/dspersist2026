import sqlite3
from sqlmodel import create_engine, Session
from sqlalchemy import event, Engine
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração do banco de dados
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)

def get_session() -> Session:
    return Session(engine)

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if type(dbapi_connection) is sqlite3.Connection:  # somente para o SQLite
       cursor = dbapi_connection.cursor()
       cursor.execute("PRAGMA foreign_keys=ON")
       cursor.close()