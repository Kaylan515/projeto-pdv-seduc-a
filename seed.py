# ============================================================
# seed.py — Script para popular o banco com dados iniciais
# ============================================================
# Execute uma vez para criar os usuários de teste:
#   python seed.py
# ============================================================

from app.database import SessionLocal, engine, Base
from app.models.usuario import Usuario
from app.auth import hash_senha

# Garante que as tabelas existem antes de inserir
Base.metadata.create_all(bind=engine)

# Usuários a criar — fácil de expandir conforme o projeto cresce
USUARIOS = [
    {
        "nome": "Admin do Sistema",
        "email": "admin@estoque.com",
        "senha": "admin123",
        "role": "admin",
    },
    {
        "nome": "Operador Padrão",
        "email": "operador@estoque.com",
        "senha": "operador123",
        "role": "operador",
    },
]


def seed():
    db = SessionLocal()

    try:
        for dados in USUARIOS:
            # Verifica se o usuário já existe para não duplicar ao rodar o script mais de uma vez
            existente = db.query(Usuario).filter(
                Usuario.email == dados["email"]
            ).first()

            if existente:
                print(f"[SKIP]  {dados['email']} — já existe no banco")
                continue

            usuario = Usuario(
                nome=dados["nome"],
                email=dados["email"],
                senha_hash=hash_senha(dados["senha"]),  # nunca salvar senha pura
                role=dados["role"],
            )

            db.add(usuario)
            print(f"[OK]    {dados['email']} criado com role '{dados['role']}'")

        db.commit()
        print("\nSeed concluído!")

    except Exception as e:
        db.rollback()  # desfaz tudo se algo der errado
        print(f"[ERRO] {e}")

    finally:
        db.close()


if __name__ == "__main__":
    seed()