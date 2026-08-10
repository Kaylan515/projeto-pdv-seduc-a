# ============================================================
# main.py
# ============================================================

from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.controllers import (
    auth_controller,
    usuario_controller,
    produto_controller,
    categoria_controller,
    movimentacao_controller,
    armario_controller,
    cliente_controller,
    pdv_controller,
)
from app.models.produto import Produto
from app.models.armario import Armario, StatusArmario
from app.models.movimentacao import Movimentacao, TipoMovimentacao
from app.models.categoria import Categoria
from app.auth import get_usuario_logado, get_usuario_opcional

app = FastAPI(title="AAPM SENAI")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

templates = Jinja2Templates(directory="app/templates")

app.include_router(auth_controller.router)
app.include_router(usuario_controller.router)
app.include_router(produto_controller.router)
app.include_router(categoria_controller.router)
app.include_router(movimentacao_controller.router)
app.include_router(armario_controller.router)
app.include_router(cliente_controller.router)
app.include_router(pdv_controller.router)


# ============================================================
# PÁGINA PÚBLICA — visitante não logado
# ============================================================

@app.get("/")
def home(
    request: Request,
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_opcional)
):
    if usuario is None:
        return templates.TemplateResponse(
            request,
            "welcome.html",
            {"request": request}
        )
    return RedirectResponse(url="/dashboard", status_code=302)


# ============================================================
# DASHBOARD — só para logados
# ============================================================

@app.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    usuario = Depends(get_usuario_logado)
):
    # ----------------------------------------------------------
    # PRODUTOS
    # ----------------------------------------------------------
    todos_produtos = db.query(Produto).filter(Produto.ativo == True).all()

    total_produtos   = len(todos_produtos)
    estoque_baixo    = [p for p in todos_produtos if p.estoque_baixo]

    # ----------------------------------------------------------
    # ARMÁRIOS
    # ----------------------------------------------------------
    todos_armarios   = db.query(Armario).filter(Armario.ativo == True).all()
    armarios_disponiveis = sum(
        1 for a in todos_armarios
        if a.status == StatusArmario.DISPONIVEL
    )
    armarios_alugados = sum(
        1 for a in todos_armarios
        if a.status == StatusArmario.ALUGADO
    )

    # ----------------------------------------------------------
    # MOVIMENTAÇÕES RECENTES — últimas 8
    # ----------------------------------------------------------
    movimentacoes_recentes = (
        db.query(Movimentacao)
        .order_by(Movimentacao.criado_em.desc())
        .limit(8)
        .all()
    )

    # ----------------------------------------------------------
    # CATEGORIAS
    # ----------------------------------------------------------
    total_categorias = db.query(Categoria).filter(
        Categoria.ativo == True
    ).count()

    return templates.TemplateResponse(
        request,
        "dashboard.html",
        {
            "request":               request,
            "usuario":               usuario,
            "total_produtos":        total_produtos,
            "total_categorias":      total_categorias,
            "estoque_baixo":         estoque_baixo,
            "armarios_disponiveis":  armarios_disponiveis,
            "armarios_alugados":     armarios_alugados,
            "total_armarios":        len(todos_armarios),
            "movimentacoes_recentes": movimentacoes_recentes,
            "TipoMovimentacao":      TipoMovimentacao,
        }
    )