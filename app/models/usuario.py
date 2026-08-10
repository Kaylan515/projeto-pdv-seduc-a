# ============================================================
# models/usuario.py — Tabela de usuários
# ============================================================
# Um Model SQLAlchemy é uma classe Python que representa
# uma tabela no banco de dados. Cada atributo da classe
# corresponde a uma coluna da tabela.
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func  # para timestamps automáticos
from app.database import Base


class Usuario(Base):
    # Nome da tabela no banco de dados
    __tablename__ = "usuarios"

    # ----------------------------------------------------------
    # Colunas da tabela
    # ----------------------------------------------------------

    # Chave primária — gerada automaticamente pelo banco
    id = Column(Integer, primary_key=True, index=True)

    # Nome completo do usuário
    nome = Column(String(100), nullable=False)

    # Email único — usado como "username" no login
    email = Column(String(150), unique=True, index=True, nullable=False)

    # Senha NUNCA é armazenada em texto puro.
    # Aqui guardamos apenas o hash gerado pelo bcrypt.
    # O bcrypt produz strings de ~60 caracteres.
    senha_hash = Column(String(255), nullable=False)

    # Perfil do usuário: "admin" ou "operador"
    # Define o que cada usuário pode fazer no sistema
    role = Column(String(20), nullable=False, default="operador")

    # Permite desativar um usuário sem excluí-lo do banco
    ativo = Column(Boolean, default=True)

    # Preenchido automaticamente pelo banco ao criar o registro
    # server_default=func.now() delega ao banco, não ao Python
    criado_em = Column(DateTime, server_default=func.now())

    # Representação textual do objeto — útil para debug
    def __repr__(self):
        return f"<Usuario id={self.id} email={self.email} role={self.role}>"