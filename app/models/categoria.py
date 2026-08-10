# ============================================================
# models/categoria.py — Tabela de categorias
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id    = Column(Integer, primary_key=True, index=True)
    nome  = Column(String(100), nullable=False, unique=True)
    ativo = Column(Boolean, default=True)

    # ----------------------------------------------------------
    # Relacionamento reverso — permite acessar os produtos de
    # uma categoria diretamente: categoria.produtos
    #
    # back_populates="categoria" conecta com o lado do Produto.
    # lazy="select" carrega os produtos apenas quando acessados.
    # ----------------------------------------------------------
    produtos = relationship(
        "Produto",
        back_populates="categoria",
        lazy="select"
    )

    def __repr__(self):
        return f"<Categoria id={self.id} nome={self.nome}>"