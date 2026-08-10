# A ordem de import importa:
# Categoria deve ser importada antes de Produto
# para o SQLAlchemy resolver o relacionamento corretamente.

from app.models import categoria  # noqa: F401
from app.models import produto    # noqa: F401
from app.models import usuario    # noqa: F401
from app.models import movimentacao  # noqa: F401
from app.models import armario       # noqa: F401
from app.models import cliente       # noqa: F401
from app.models import venda         # noqa: F401