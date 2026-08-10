# ============================================================
# database.py — Configuração da conexão com o banco de dados
# ============================================================
# O SQLAlchemy é nosso ORM (Object Relational Mapper).
# Ele nos permite trabalhar com o banco usando classes Python
# em vez de escrever SQL puro.
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv
import os

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# Lê a URL do banco definida no .env
# Ex: "sqlite:///./estoque.db" ou "postgresql://user:senha@localhost/estoque"
DATABASE_URL = os.getenv("DATABASE_URL")

# ------------------------------------------------------------
# Engine — é o "motor" da conexão com o banco.
# Uma única instância é criada e reutilizada pela aplicação.
#
# connect_args={"check_same_thread": False} é necessário
# APENAS para SQLite, pois ele não permite múltiplas threads
# por padrão. PostgreSQL não precisa disso.
# ------------------------------------------------------------
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ------------------------------------------------------------
# SessionLocal — fábrica de sessões.
# Cada requisição HTTP receberá sua própria sessão isolada.
#
# autocommit=False → precisamos chamar db.commit() manualmente
# autoflush=False  → não envia queries ao banco automaticamente
# ------------------------------------------------------------
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ------------------------------------------------------------
# Base — classe pai de todos os nossos Models.
# Qualquer classe que herdar de Base será reconhecida
# pelo SQLAlchemy como uma tabela no banco de dados.
# ------------------------------------------------------------
class Base(DeclarativeBase):
    pass

# ------------------------------------------------------------
# get_db — função geradora usada como dependência do FastAPI.
#
# O padrão "yield" garante que a sessão será fechada
# ao final da requisição, mesmo se ocorrer um erro.
#
# Uso: def minha_rota(db: Session = Depends(get_db))
# ------------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db          # entrega a sessão para a rota
    finally:
        db.close()        # sempre fecha, com ou sem erro