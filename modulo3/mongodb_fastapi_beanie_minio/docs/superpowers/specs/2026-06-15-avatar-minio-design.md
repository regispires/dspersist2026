# Design: Upload de foto (avatar) do usuário via MinIO

Data: 2026-06-15
Projeto: `modulo3/mongodb_fastapi_beanie_minio` (FastAPI + Beanie + MongoDB, assíncrono)

## Objetivo

Permitir enviar, recuperar e remover a foto (avatar) de um usuário via API.
Os bytes da imagem ficam armazenados no MinIO (acessado de forma assíncrona com
`aioboto3`); os metadados ficam embutidos no documento `User` no MongoDB.

## Decisões

- **Cardinalidade:** um avatar por usuário, substituível. Um novo upload
  sobrescreve o objeto anterior no MinIO.
- **Recuperação:** streaming pela API (proxy). O MinIO permanece privado atrás
  da API; o cliente nunca fala direto com o MinIO.
- **Metadados:** embutidos no documento `User` (modelo `Avatar`), não em coleção
  separada.
- **Validação:** apenas content-types de imagem (`image/jpeg`, `image/png`,
  `image/webp`) e tamanho máximo de 5 MB.
- **MinIO:** já existe um servidor rodando no ambiente; configuração via `.env`.
  O bucket é criado automaticamente na inicialização se não existir.
- **Arquitetura:** em camadas — rota → serviço de storage (`storage.py`) →
  MinIO. A rota não conhece detalhes de S3.
- **Retorno do POST:** o documento `User` completo atualizado.
- **Testes:** incluídos (pytest + httpx.AsyncClient, com o storage mockado).

## Modelo de dados (`modelos.py`)

Novo modelo embutido (Pydantic `BaseModel`, não é `Document`):

```python
class Avatar(BaseModel):
    object_key: str        # ex.: "avatars/<user_id>.jpg"
    content_type: str      # ex.: "image/jpeg"
    size: int              # bytes
    original_filename: str | None = None
    uploaded_at: datetime  # UTC
```

No `User`, novo campo opcional:

```python
avatar: Avatar | None = None
```

A `object_key` é derivada do `user_id` mais a extensão correspondente ao
content-type. Assim, um novo upload sobrescreve o objeto anterior no MinIO,
coerente com o avatar substituível.

## Configuração (`.env` / `.env-exemplo`)

Novas variáveis de ambiente:

```
MINIO_ENDPOINT_URL="http://localhost:9000"
MINIO_ACCESS_KEY="..."
MINIO_SECRET_KEY="..."
MINIO_BUCKET="avatars"
MINIO_REGION="us-east-1"
```

Nova dependência em `pyproject.toml`: `aioboto3`.
Dependência de teste: `pytest`, `pytest-asyncio`, `httpx`.

## Camada de storage (`storage.py`)

Módulo dedicado com uma `aioboto3.Session()` única. Cada operação abre o client
via `async with session.client("s3", endpoint_url=..., ...)`.

Funções assíncronas:

- `ensure_bucket()` — cria o bucket se não existir. Chamada no startup.
- `upload_avatar(object_key, file_bytes, content_type)` — envia os bytes.
- `download_avatar(object_key)` — retorna o corpo (stream) e o content-type para
  o proxy de download.
- `delete_avatar(object_key)` — remove o objeto.

Configuração lida via `os.getenv`, no mesmo estilo de `database.py`.

## Inicialização (`main.py`)

No `lifespan`, após `init_db()`, chamar `await ensure_bucket()` para garantir o
bucket. Nenhum client é mantido aberto globalmente — cada operação usa
`async with`.

## Endpoints (`rotas/users.py`)

- `POST /users/{user_id}/avatar`
  - Recebe `UploadFile` (multipart/form-data).
  - Valida content-type (senão `400`) e tamanho ≤ 5 MB (senão `413`).
  - Verifica existência do usuário (senão `404`).
  - Faz upload ao MinIO e grava o `Avatar` no `User`.
  - Retorna o `User` completo atualizado.

- `GET /users/{user_id}/avatar`
  - `404` se usuário inexistente ou sem avatar.
  - Lê o objeto do MinIO e devolve `StreamingResponse` com o content-type
    correto.

- `DELETE /users/{user_id}/avatar`
  - `404` se usuário inexistente ou sem avatar.
  - Remove o objeto do MinIO e zera `user.avatar`.

## Tratamento de erros

- `404` — usuário inexistente ou sem avatar.
- `400` — tipo de arquivo não suportado.
- `413` — arquivo acima de 5 MB.
- Falhas de comunicação com o MinIO → `502` (ou `500`) com mensagem clara e log
  via `logging` já configurado no projeto.

## Testes

Suite mínima com `pytest` + `httpx.AsyncClient`, com a camada de storage
mockada (sem MinIO real):

- upload válido grava metadados e retorna `User` atualizado;
- upload com content-type inválido → `400`;
- upload acima do limite de tamanho → `413`;
- download retorna os bytes com content-type correto;
- delete remove o avatar e zera o campo no `User`;
- download/delete sem avatar → `404`.

## Fora de escopo (YAGNI)

- Galeria de múltiplas fotos por usuário.
- URLs pré-assinadas.
- Geração de thumbnails / redimensionamento.
- Autenticação/autorização nos endpoints.
