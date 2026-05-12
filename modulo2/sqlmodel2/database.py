from sqlmodel import create_engine, Session, SQLModel
from dotenv import load_dotenv
import os

# Carregar variáveis do arquivo .env
load_dotenv()

# Configuração do banco de dados
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)
def get_session() -> Session:
    return Session(engine)
