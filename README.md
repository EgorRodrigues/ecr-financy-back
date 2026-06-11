# Financy Back

Backend FastAPI para Controle Financeiro com arquitetura multi-tenant.

## Pré-requisitos

- Python ≥ 3.11
- UV (gerenciador de pacotes e ambiente)
- Docker e Docker Compose (opcional, para execução containerizada)

## Instalação

### 1. Instalar o UV

Se ainda não tiver o UV instalado:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ou siga as instruções oficiais em https://docs.astral.sh/uv/getting-started/installation

### 2. Clonar e instalar dependências

```bash
cd ecr-financy-back
uv sync
```

Isso criará o ambiente virtual e instalará todas as dependências (incluindo as de desenvolvimento).

## Configuração

Copie o arquivo de exemplo de variáveis de ambiente:

```bash
cp .env-example .env
```

Edite o arquivo `.env` conforme necessário (as configurações padrão já funcionam para desenvolvimento local com Docker).

## Execução

### Com Docker Compose (recomendado para desenvolvimento)

Inicia o banco de dados PostgreSQL e a aplicação:

```bash
docker-compose up
```

A aplicação estará disponível em http://localhost:8000

A documentação da API (Swagger UI) está em http://localhost:8000/docs

### Sem Docker (direto no host)

Primeiro, certifique-se de ter um PostgreSQL rodando localmente com as configurações do `.env`.

Para iniciar a aplicação:

```bash
uv run task run
```

Ou:

```bash
uv run task runserver
```

## Comandos Disponíveis (Taskipy)

Usamos o Taskipy para definir tarefas comuns. Todos os comandos são executados com `uv run task <nome-da-tarefa>`:

| Comando | Descrição |
|---------|-----------|
| `lint` | Verifica o código com Ruff |
| `lint-fix` | Corrige automaticamente problemas de lint |
| `format` | Formata o código com Ruff |
| `run` | Inicia o servidor com Uvicorn (modo reload) |
| `runserver` | Inicia o servidor com FastAPI CLI |
| `test` | Executa os testes (modo quiet) |
| `test-all` | Executa todos os testes com coverage |
| `clean` | Limpa arquivos de cache e relatórios |
| `makemigrations` | Cria uma nova migração Alembic (adicione uma mensagem) |
| `migrate` | Aplica migrações pendentes |

Exemplos:
```bash
uv run task lint
uv run task makemigrations "adiciona_campo_x"
uv run task test
```

## Migrações de Banco de Dados (Multi-tenant)

Este projeto usa uma arquitetura multi-tenant onde cada tenant tem seu próprio schema (ex: `tenant_uuid`).

### Criar uma Nova Migração

```bash
uv run task makemigrations "sua_mensagem_de_migracao"
```

Ou diretamente com Alembic:
```bash
uv run alembic revision --autogenerate -m "sua_mensagem_de_migracao"
```

### Aplicar Migrações a Todos os Tenants

Para aplicar as migrações a todos os schemas de tenants:

```bash
uv run python app/scripts/migrate_tenants.py
```

Este script irá:
1. Descobrir todos os schemas que começam com `tenant_`
2. Aplicar `alembic upgrade head` individualmente em cada um
