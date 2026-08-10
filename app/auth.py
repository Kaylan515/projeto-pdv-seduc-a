# ============================================================
# auth.py — Lógica de autenticação
# ============================================================
# Este módulo centraliza três responsabilidades:
#   1. Hash e verificação de senhas com bcrypt
#   2. Geração de tokens JWT
#   3. Leitura e validação do token vindo do cookie
# ============================================================

from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

# ------------------------------------------------------------
# CryptContext — configura o bcrypt como algoritmo de hash.
#
# O bcrypt é preferido por ser lento por design: ele adiciona
# um "custo" computacional que dificulta ataques de força bruta.
# deprecated="auto" garante que hashes antigos sejam atualizados.
# ------------------------------------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ============================================================
# FUNÇÕES DE SENHA
# ============================================================

def hash_senha(senha: str) -> str:
    """
    Transforma a senha em texto puro em um hash bcrypt.

    O bcrypt automaticamente:
    - Gera um salt aleatório (evita rainbow tables)
    - Aplica o algoritmo de hashing com custo configurável
    - Retorna uma string no formato: $2b$12$<salt><hash>

    Exemplo:
        hash_senha("minhasenha123")
        → "$2b$12$N9qo8uLOickgx2ZMRZoMyeIjZAgcfl7p92ldGxad68LJZdL17lhWy"
    """
    return pwd_context.hash(senha)


def verificar_senha(senha_plain: str, senha_hash: str) -> bool:
    """
    Compara a senha digitada com o hash salvo no banco.

    Internamente o bcrypt extrai o salt do hash e aplica
    o mesmo processo — se o resultado bater, as senhas são iguais.

    NUNCA comparamos as senhas diretamente (==).
    Sempre usamos esta função.
    """
    return pwd_context.verify(senha_plain, senha_hash)


# ============================================================
# FUNÇÕES JWT
# ============================================================

def criar_token(data: dict) -> str:
    """
    Gera um token JWT assinado com a SECRET_KEY.

    JWT tem 3 partes separadas por ponto (.):
      - Header: algoritmo usado (HS256)
      - Payload: dados do usuário (sub, role, exp)
      - Signature: hash do header+payload com a SECRET_KEY

    O payload NÃO é criptografado — qualquer um pode lê-lo.
    A assinatura garante que o conteúdo não foi alterado.

    Parâmetros:
        data: dicionário com os dados a embutir no token
              Ex: {"sub": "user@email.com", "role": "admin"}
    """
    payload = data.copy()

    # Define quando o token expira
    # timezone.utc garante que a comparação seja sempre em UTC
    expira = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expira})

    # jwt.encode assina e serializa o token em uma string Base64url
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


def decodificar_token(token: str) -> dict:
    """
    Valida e decodifica um token JWT.

    O jose/jwt verifica automaticamente:
    - Se a assinatura é válida (SECRET_KEY correta)
    - Se o token não está expirado (campo "exp")

    Lança JWTError se qualquer verificação falhar.
    """
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    return payload


# ============================================================
# DEPENDÊNCIA FASTAPI — leitura do usuário logado
# ============================================================

def get_usuario_logado(request: Request) -> dict:
    """
    Dependência do FastAPI para rotas protegidas.

    Lê o token JWT do cookie HttpOnly enviado automaticamente
    pelo browser a cada requisição.

    Cookie HttpOnly = JavaScript da página NÃO consegue lê-lo,
    o que protege contra ataques XSS.

    Uso na rota:
        @router.get("/protegida")
        def rota(usuario = Depends(get_usuario_logado)):
            return {"email": usuario["sub"]}

    Lança HTTPException 401 se:
    - Cookie não existe (usuário não logado)
    - Token inválido ou expirado
    """
    token = request.cookies.get("access_token")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado"
        )

    try:
        payload = decodificar_token(token)
        email: str = payload.get("sub")

        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido"
            )

        return payload  # retorna o payload completo {sub, role, exp}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado"
        )


def get_usuario_opcional(request: Request) -> dict | None:
    """
    Versão 'suave' — não lança erro se não houver token.
    Útil para páginas públicas que exibem conteúdo diferente
    dependendo de o usuário estar logado ou não.
    """
    try:
        return get_usuario_logado(request)
    except HTTPException:
        return None
    
def get_admin(request: Request) -> dict:
    """
    Dependência que exige login E perfil admin.
    Usar em rotas exclusivas de administradores.
    
    Lança 403 se o usuário estiver logado mas não for admin.
    """
    usuario = get_usuario_logado(request)

    if usuario.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores."
        )

    return usuario