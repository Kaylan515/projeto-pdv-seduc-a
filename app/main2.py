# ============================================================
# main.py — Ponto de entrada da aplicação
# ============================================================

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse

from app.controllers import auth_controller
from app.auth import get_usuario_opcional  # ← troca aqui
from app.controllers import usuario_controller  # ← adicionar
from app.controllers import produto_controller  # ← adicionar
from app.controllers import categoria_controller
from app.controllers import movimentacao_controller
from app.controllers import armario_controller  # ← adicionar

app = FastAPI(title="Sistema de Estoque")

#Configura o FastAPI para servir arquivos estáticos (CSS, JS, imagens)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Configura o Jinja2 para renderizar os templates HTML
templates = Jinja2Templates(directory="app/templates")

# Inclui os routers dos controladores
app.include_router(auth_controller.router)
# Inclui o router do controlador de usuários (admin)
app.include_router(usuario_controller.router)  # ← adicionar
app.include_router(produto_controller.router)  # ← adicionar
app.include_router(categoria_controller.router)
app.include_router(movimentacao_controller.router)
app.include_router(armario_controller.router)   # ← adicionar


#Rodar o código: python -m uvicorn app.main:app --reload


@app.get("/")
def dashboard(
    request: Request,
    usuario = Depends(get_usuario_opcional)  # ← não lança erro se não logado
):
    """
    Se o usuário estiver logado, mostra o dashboard.
    Se não estiver, renderiza uma página de boas-vindas
    com links para login e cadastro — sem nenhum erro.
    """

    if usuario is None:
        # Não logado — exibe página pública de boas-vindas
        return templates.TemplateResponse(
            request,
            "welcome.html",
            {"request": request}
        )

    # Logado — exibe o dashboard com os dados do usuário
    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {"request": request, "usuario": usuario}
    )
    
