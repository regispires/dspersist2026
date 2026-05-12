from sqlalchemy import create_engine
from models import Base
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Configuração do banco de dados
engine = create_engine(os.getenv("DATABASE_URL"), echo=True)

# Criar a(s) tabela(s) no banco de dados
# Base.metadata.create_all(engine)
