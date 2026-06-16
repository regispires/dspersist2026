# Imagem oficial da Astral com uv + Python 3.12 já instalados
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Compila bytecode na build e copia os pacotes (em vez de symlink) para
# que a camada de dependências funcione bem com o cache do Docker.
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Instala as dependências primeiro, usando apenas os arquivos de lock,
# para aproveitar o cache quando só o código da aplicação muda.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copia o restante do código e finaliza a instalação do projeto
COPY . .
RUN uv sync --frozen --no-dev

# Coloca o venv no PATH
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# Servidor de produção do FastAPI (incluído em fastapi[standard])
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
