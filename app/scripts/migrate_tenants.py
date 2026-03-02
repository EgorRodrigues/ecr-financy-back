import logging
import os
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

# --- Configuração de Logging ---
# Configura o logging para exibir mensagens informativas durante a execução.
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Constantes ---
# Define o padrão de nome dos schemas dos tenants.
TENANT_SCHEMA_PREFIX = "tenant_"

# --- Funções ---

def get_project_root() -> Path:
    """Retorna o diretório raiz do projeto."""
    # Navega para cima a partir do diretório atual (__file__) até encontrar a raiz do projeto.
    return Path(__file__).parent.parent.parent

def get_alembic_config(project_root: Path) -> Config:
    """Carrega a configuração do Alembic a partir do arquivo alembic.ini."""
    alembic_ini_path = project_root / "alembic.ini"
    if not alembic_ini_path.exists():
        raise FileNotFoundError(f"Arquivo de configuração do Alembic não encontrado em: {alembic_ini_path}")
    
    # Cria um objeto de configuração do Alembic e define o local dos scripts de migração.
    config = Config(str(alembic_ini_path))
    config.set_main_option("script_location", str(project_root / "alembic"))
    return config

def get_database_url() -> str:
    """Constrói a URL do banco de dados a partir de variáveis de ambiente."""
    # Carrega as configurações do banco de dados de forma segura.
    # Substitua pela sua lógica de carregamento de configuração, se for diferente.
    from app.core.config import settings
    
    return (
        f"postgresql+psycopg://{settings.postgres_username}:{settings.postgres_password}@"
        f"{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_database}"
    )

def get_tenant_schemas(engine) -> list[str]:
    """Busca e retorna uma lista com os nomes de todos os schemas de tenants."""
    with engine.connect() as connection:
        # Executa uma consulta para encontrar todos os schemas que começam com o prefixo do tenant.
        query = text("SELECT schema_name FROM information_schema.schemata WHERE schema_name LIKE :prefix")
        result = connection.execute(query, {"prefix": f"{TENANT_SCHEMA_PREFIX}%"})
        schemas = [row[0] for row in result]
        logger.info(f"Encontrados {len(schemas)} tenants: {schemas}")
        return schemas

def run_migrations_for_all_tenants():
    """
    Orquestra o processo de migração para todos os tenants.
    """
    try:
        project_root = get_project_root()
        alembic_cfg = get_alembic_config(project_root)
        db_url = get_database_url()
        
        # Define a URL do banco de dados na configuração do Alembic.
        alembic_cfg.set_main_option("sqlalchemy.url", db_url)
        
        engine = create_engine(db_url)
        tenant_schemas = get_tenant_schemas(engine)

        if not tenant_schemas:
            logger.warning("Nenhum tenant encontrado para migrar.")
            return

        # Itera sobre cada tenant e aplica as migrações.
        for schema in tenant_schemas:
            logger.info(f"--- Iniciando migração para o tenant: {schema} ---")
            try:
                # Define o schema alvo para a execução do Alembic.
                # Isso garante que o Alembic crie a tabela alembic_version dentro do schema correto.
                alembic_cfg.attributes["target_schema"] = schema
                command.upgrade(alembic_cfg, "head")
                logger.info(f"Sucesso na migração do tenant: {schema}")
            except Exception as e:
                logger.error(f"Falha ao migrar o tenant {schema}: {e}", exc_info=True)
        
        logger.info("--- Todas as migrações foram concluídas. ---")

    except Exception as e:
        logger.error(f"Ocorreu um erro inesperado durante o processo de migração: {e}", exc_info=True)

# --- Ponto de Entrada ---

if __name__ == "__main__":
    # Permite que o script seja executado diretamente da linha de comando.
    run_migrations_for_all_tenants()
