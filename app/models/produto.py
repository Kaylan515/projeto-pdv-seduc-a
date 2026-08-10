# ============================================================
# models/produto.py — Tabela de produtos da loja AAPM SENAI
# ============================================================

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id            = Column(Integer, primary_key=True, index=True)
    nome          = Column(String(150), nullable=False, index=True)
    preco         = Column(Float, nullable=False, default=0.0)
    estoque_atual = Column(Integer, nullable=False, default=0)
    ativo         = Column(Boolean, default=True)

    # ----------------------------------------------------------
    # Caminho da imagem salva no servidor.
    # Armazenamos o path relativo, ex: "uploads/produto_1.jpg"
    # e montamos a URL completa no template: /static/uploads/...
    # nullable=True pois nem todo produto terá imagem.
    # ----------------------------------------------------------
    imagem_path = Column(String(255), nullable=True)

    # ----------------------------------------------------------
    # Chave estrangeira — liga cada produto a uma categoria.
    # nullable=True permite produtos sem categoria definida.
    # ondelete="SET NULL" → se a categoria for deletada,
    # o campo vira NULL em vez de quebrar a integridade.
    # ----------------------------------------------------------
    categoria_id = Column(
        Integer,
        ForeignKey("categorias.id", ondelete="SET NULL"),
        nullable=True
    )

    # ----------------------------------------------------------
    # Relacionamento ORM — permite acessar o objeto Categoria
    # diretamente pelo produto: produto.categoria.nome
    #
    # back_populates="produtos" conecta com o lado da Categoria.
    # ----------------------------------------------------------
    categoria = relationship(
        "Categoria",
        back_populates="produtos"
    )

    def __repr__(self):
        return f"<Produto id={self.id} nome={self.nome} estoque={self.estoque_atual}>"

    # @property é uma forma elegante de criar um método que se comporta como um atributo.
    # Isso é útil para lógica de apresentação, como montar a URL da imagem, sem poluir o modelo com detalhes de implementação.
    @property
    def imagem_url(self) -> str:
        """
        Retorna a URL pública da imagem para usar no template.
        Se não houver imagem, retorna um placeholder.

        Uso no template: <img src="{{ produto.imagem_url }}">
        """
        if self.imagem_path:
            return f"/static/{self.imagem_path}"
        return "/static/img/produto-placeholder.png"
    
    @property
    def estoque_baixo(self) -> bool:
        """
        Retorna True se o estoque estiver zerado ou em quantidade
        muito baixa. Usamos 5 como mínimo padrão — futuramente
        isso pode virar uma coluna configurável por produto.
        """
        return self.estoque_atual <= 5
    
    
# alembic revision --autogenerate -m "criar tabelas categorias e refatorar produtos"
# alembic upgrade head