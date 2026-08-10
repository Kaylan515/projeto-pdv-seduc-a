Configure a models do usuario
Em resumo, o padrão MVC é uma maneira eficaz de organizar o código em sua aplicação FastAPI, separando a lógica de negócios (Model), as rotas e funções de manipulação de solicitações HTTP (Controller) e a exibição dos dados (View).


# 1. Inicializa o Alembic — cria a pasta migrations/ e o alembic.ini
''''bash
python -m alembic init migrations
''''

Agora edite o arquivo alembic.ini — encontre esta linha e substitua:
ini# Antes:
sqlalchemy.url = driver://user:pass@localhost/dbname

# Depois (lê direto do .env via env.py):
sqlalchemy.url =
Depois edite migrations/env.py — encontre os dois trechos e substitua:


from dotenv import load_dotenv
import os

# Importamos nossa Base — ela conhece todos os Models registrados
from app.database import Base

# Importante: importar os models para que o Alembic os enxergue
# Sem este import, o Alembic não saberá que a tabela existe
from app.models import usuario  # noqa: F401

load_dotenv()

# Injeta a DATABASE_URL do .env no Alembic dinamicamente
# Isso evita duplicar a URL em dois lugares (alembic.ini e .env)
config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL"))


# Aponta para os metadados dos nossos Models
# O Alembic compara esses metadados com o banco para gerar as migrations
target_metadata = Base.metadata


Agora crie o arquivo app/models/__init__.py (pode ficar vazio por enquanto).
Depois, gere e aplique a primeira migration:


# 2. Gera a migration — o Alembic detecta os Models e cria o arquivo
alembic revision --autogenerate -m "criar tabela usuarios"

# 3. Aplica a migration no banco
alembic upgrade head

# Iniciar o servidor com hot-reload (recarrega ao salvar)
uvicorn app.main:app --reload

pip install bcrypt==4.3.0


criamos um arquivo seed para popular o banco com um usuário admin:
# arquivo: app/seed.py

