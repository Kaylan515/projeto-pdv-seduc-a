# ============================================================
# controllers/produto_controller.py — CRUD produtos AAPM SENAI
# ============================================================

import math
import os
import shutil

from fastapi import (
    APIRouter,
    Depends,
    Request,
    Form,
    UploadFile,
    File,
)

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.produto import Produto
from app.models.categoria import Categoria
from app.auth import get_usuario_logado, get_admin


router = APIRouter(prefix="/produtos", tags=["Produtos"])

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# PASTA DE UPLOADS
# ============================================================

UPLOAD_DIR = "app/static/uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


# ============================================================
# LISTAGEM DE PRODUTOS
# ============================================================

@router.get("/")
def listar_produtos(
    request: Request,
    busca: str = "",
    categoria_id: int = 0,
    pagina: int = 1,
    por_pagina: int = 10,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    # Busca somente produtos ativos
    query = db.query(Produto).filter(
        Produto.ativo == True
    )

    # Filtro por nome
    if busca:
        query = query.filter(
            Produto.nome.ilike(f"%{busca}%")
        )

    # Filtro por categoria
    if categoria_id:
        query = query.filter(
            Produto.categoria_id == categoria_id
        )

    # Ordenação
    query = query.order_by(Produto.nome)

    # Total de produtos encontrados
    total_produtos = query.count()

    # Garante valores válidos para paginação
    pagina = max(pagina, 1)
    por_pagina = max(por_pagina, 1)

    # Calcula quantidade de páginas
    total_paginas = (
        math.ceil(total_produtos / por_pagina)
        if total_produtos
        else 1
    )

    # Impede que o usuário tente acessar uma página inexistente
    if pagina > total_paginas:
        pagina = total_paginas

    # Calcula o deslocamento corretamente
    offset = (pagina - 1) * por_pagina

    # Busca somente os produtos da página atual
    produtos = (
        query
        .offset(offset)
        .limit(por_pagina)
        .all()
    )

    # Busca categorias ativas
    categorias = (
        db.query(Categoria)
        .filter(Categoria.ativo == True)
        .all()
    )

    # Renderiza a página
    return templates.TemplateResponse(
        request,
        "produtos/index.html",
        {
            "request": request,
            "usuario": usuario,
            "produtos": produtos,
            "categorias": categorias,
            "busca": busca,
            "categoria_id": categoria_id,

            # Paginação
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_paginas": total_paginas,
            "total_produtos": total_produtos,
        }
    )


# ============================================================
# CADASTRO
# ============================================================

@router.get("/novo")
def form_novo_produto(
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    categorias = (
        db.query(Categoria)
        .filter(Categoria.ativo == True)
        .all()
    )

    return templates.TemplateResponse(
        request,
        "produtos/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": None,
            "categorias": categorias,
        }
    )


# ============================================================
# CRIAR PRODUTO
# ============================================================

@router.post("/novo")
async def criar_produto(
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    categorias = (
        db.query(Categoria)
        .filter(Categoria.ativo == True)
        .all()
    )

    # Verifica duplicidade de nome
    if db.query(Produto).filter(
        Produto.nome.ilike(nome)
    ).first():

        return templates.TemplateResponse(
            request,
            "produtos/form.html",
            {
                "request": request,
                "usuario": admin,
                "editando": None,
                "categorias": categorias,
                "erro": "Já existe um produto com este nome.",
                "valores": {
                    "nome": nome,
                    "preco": preco,
                    "estoque_atual": estoque_atual,
                    "categoria_id": categoria_id,
                },
            },
            status_code=400
        )

    # Salva imagem
    imagem_path = await _salvar_imagem(imagem)

    # Cria produto
    produto = Produto(
        nome=nome,
        preco=preco,
        estoque_atual=estoque_atual,
        categoria_id=categoria_id or None,
        imagem_path=imagem_path,
    )

    db.add(produto)
    db.commit()

    return RedirectResponse(
        url="/produtos?criado=ok",
        status_code=302
    )


# ============================================================
# DETALHE DO PRODUTO
# ============================================================

@router.get("/{produto_id}")
def detalhe_produto(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    usuario=Depends(get_usuario_logado)
):
    produto = (
        db.query(Produto)
        .filter(
            Produto.id == produto_id,
            Produto.ativo == True
        )
        .first()
    )

    if not produto:
        return RedirectResponse(
            url="/produtos",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "produtos/detalhe.html",
        {
            "request": request,
            "usuario": usuario,
            "produto": produto,
        }
    )


# ============================================================
# FORMULÁRIO DE EDIÇÃO
# ============================================================

@router.get("/{produto_id}/editar")
def form_editar_produto(
    produto_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    editando = (
        db.query(Produto)
        .filter(Produto.id == produto_id)
        .first()
    )

    categorias = (
        db.query(Categoria)
        .filter(Categoria.ativo == True)
        .all()
    )

    if not editando:
        return RedirectResponse(
            url="/produtos",
            status_code=302
        )

    return templates.TemplateResponse(
        request,
        "produtos/form.html",
        {
            "request": request,
            "usuario": admin,
            "editando": editando,
            "categorias": categorias,
        }
    )


# ============================================================
# EDITAR PRODUTO
# ============================================================

@router.post("/{produto_id}/editar")
async def editar_produto(
    produto_id: int,
    request: Request,
    nome: str = Form(...),
    preco: float = Form(...),
    estoque_atual: int = Form(...),
    categoria_id: int = Form(0),
    imagem: UploadFile = File(None),
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    editando = (
        db.query(Produto)
        .filter(Produto.id == produto_id)
        .first()
    )

    categorias = (
        db.query(Categoria)
        .filter(Categoria.ativo == True)
        .all()
    )

    if not editando:
        return RedirectResponse(
            url="/produtos",
            status_code=302
        )

    # Verifica conflito de nome
    conflito = (
        db.query(Produto)
        .filter(
            Produto.nome.ilike(nome),
            Produto.id != produto_id
        )
        .first()
    )

    if conflito:
        return templates.TemplateResponse(
            request,
            "produtos/form.html",
            {
                "request": request,
                "usuario": admin,
                "editando": editando,
                "categorias": categorias,
                "erro": "Já existe outro produto com este nome.",
            },
            status_code=400
        )

    # Salva nova imagem
    nova_imagem_path = await _salvar_imagem(imagem)

    if nova_imagem_path:

        # Remove imagem antiga
        _remover_imagem(editando.imagem_path)

        # Atualiza caminho
        editando.imagem_path = nova_imagem_path

    # Atualiza dados
    editando.nome = nome
    editando.preco = preco
    editando.estoque_atual = estoque_atual
    editando.categoria_id = categoria_id or None

    db.commit()

    return RedirectResponse(
        url=f"/produtos/{produto_id}?editado=ok",
        status_code=302
    )


# ============================================================
# DESATIVAR PRODUTO
# ============================================================

@router.post("/{produto_id}/desativar")
def desativar_produto(
    produto_id: int,
    db: Session = Depends(get_db),
    admin=Depends(get_admin)
):
    produto = (
        db.query(Produto)
        .filter(Produto.id == produto_id)
        .first()
    )

    if produto:
        produto.ativo = False
        db.commit()

    return RedirectResponse(
        url="/produtos?desativado=ok",
        status_code=302
    )


# ============================================================
# SALVAR IMAGEM
# ============================================================

async def _salvar_imagem(
    imagem: UploadFile | None
) -> str | None:

    """
    Salva o arquivo enviado em /static/uploads/
    e retorna o caminho relativo para guardar no banco.

    Retorna None se nenhum arquivo foi enviado.
    """

    # Nenhum arquivo enviado
    if not imagem or not imagem.filename:
        return None

    # Extensões permitidas
    extensoes_permitidas = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    _, ext = os.path.splitext(
        imagem.filename.lower()
    )

    # Verifica extensão
    if ext not in extensoes_permitidas:
        return None

    # Nome do arquivo
    nome_arquivo = imagem.filename

    # Caminho completo
    caminho_completo = os.path.join(
        UPLOAD_DIR,
        nome_arquivo
    )

    # Salva arquivo
    with open(caminho_completo, "wb") as buffer:
        shutil.copyfileobj(
            imagem.file,
            buffer
        )

    # Caminho relativo ao /static
    return f"uploads/{nome_arquivo}"


# ============================================================
# REMOVER IMAGEM
# ============================================================

def _remover_imagem(
    imagem_path: str | None
) -> None:

    """
    Remove o arquivo de imagem do disco,
    caso ele exista.
    """

    if not imagem_path:
        return

    caminho = os.path.join(
        "app/static",
        imagem_path
    )

    if os.path.exists(caminho):
        os.remove(caminho)