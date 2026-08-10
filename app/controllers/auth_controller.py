# ============================================================
# controllers/auth_controller.py — Rotas de autenticação
# ============================================================
# Um controller no padrão MVC contém as rotas (endpoints)
# e a lógica que conecta o Model ao template (View).
# ============================================================

from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.auth import hash_senha, verificar_senha, criar_token

# APIRouter agrupa as rotas deste módulo com o prefixo /auth
router = APIRouter(prefix="/auth", tags=["Autenticação"])

templates = Jinja2Templates(directory="app/templates")


# ============================================================
# REGISTRO
# ============================================================

@router.get("/register")
def pagina_registro(request: Request):
    """Exibe o formulário de cadastro."""
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"request": request}
    )


@router.post("/register")
def registrar(
    request: Request,
    nome: str = Form(...),
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Processa o envio do formulário de cadastro.

    Form(...) instrui o FastAPI a ler os campos do
    corpo do formulário HTML (application/x-www-form-urlencoded).
    O "..." significa que o campo é obrigatório.
    """

    # Verifica se o email já está cadastrado
    usuario_existente = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    if usuario_existente:
        # Retorna ao formulário com mensagem de erro
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {
                "request": request,
                "erro": "Este e-mail já está cadastrado."
            },
            status_code=400
        )

    # Cria o novo usuário com a senha já "hashada"
    novo_usuario = Usuario(
        nome=nome,
        email=email,
        senha_hash=hash_senha(senha),  # NUNCA salvar a senha pura
        role="operador"                # role padrão para novos cadastros
    )

    db.add(novo_usuario)    # prepara o INSERT
    db.commit()             # executa no banco
    db.refresh(novo_usuario)  # atualiza o objeto com o id gerado

    # Redireciona para o login após cadastro bem-sucedido
    return RedirectResponse(url="/auth/login?cadastro=ok", status_code=302)


# ============================================================
# LOGIN
# ============================================================

@router.get("/login")
def pagina_login(request: Request):
    """Exibe o formulário de login."""
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"request": request}
    )


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    Processa o login e define o cookie JWT.

    Fluxo:
    1. Busca o usuário pelo email
    2. Verifica a senha com bcrypt
    3. Gera o token JWT
    4. Salva o token em um cookie HttpOnly
    5. Redireciona para a página principal
    """

    # Busca o usuário no banco pelo email
    usuario = db.query(Usuario).filter(
        Usuario.email == email
    ).first()

    # Verifica usuário E senha em passos separados para evitar
    # "timing attacks" (atacante deduz se o email existe pelo tempo de resposta)
    senha_correta = (
        usuario is not None and
        verificar_senha(senha, usuario.senha_hash)
    )

    if not senha_correta:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "request": request,
                "erro": "E-mail ou senha incorretos."
            },
            status_code=401
        )

    if not usuario.ativo:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {
                "request": request,
                "erro": "Usuário inativo. Contate o administrador."
            },
            status_code=403
        )

    # Dados que ficarão no payload do JWT
    # "sub" (subject) é a convenção JWT para identificar o usuário
    token_data = {
        "sub": usuario.email,
        "nome": usuario.nome,
        "role": usuario.role,
        "id": usuario.id
    }

    token = criar_token(token_data)

    # Cria a resposta de redirecionamento
    response = RedirectResponse(url="/", status_code=302)

    # Define o cookie com o token JWT
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,    # JavaScript NÃO pode ler este cookie (proteção XSS)
        max_age=3600,     # expira em 1 hora (em segundos)
        samesite="lax",   # proteção básica contra CSRF
        # secure=True     # ativar em produção (exige HTTPS)
    )

    return response


# ============================================================
# LOGOUT
# ============================================================

@router.get("/logout")
def logout():
    """
    Remove o cookie do browser, encerrando a sessão.
    Basta deletar o cookie — o token em si é stateless,
    não precisamos removê-lo do banco.
    """
    response = RedirectResponse(url="/auth/login", status_code=302)
    response.delete_cookie("access_token")
    return response