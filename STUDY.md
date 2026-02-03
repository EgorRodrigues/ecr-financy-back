# Estudo de Arquitetura do Projeto

## Visão Geral
O projeto implementa uma **Arquitetura em Camadas (Layered Architecture)** com o uso explícito do **Padrão Repository (Repository Pattern)**. A aplicação é construída utilizando **FastAPI** e **SQLAlchemy**.

## Estrutura de Diretórios e Responsabilidades

A estrutura do projeto segue uma separação clara de responsabilidades:

```
app/
├── routers/          # Camada de Apresentação (Controllers)
├── repositories/     # Camada de Acesso a Dados e Regra de Negócio
├── models/           # Definição de Dados (Pydantic Schemas/DTOs)
├── db/               # Definição de Tabelas (SQLAlchemy Core) e Conexão
├── core/             # Configurações globais e Segurança
└── schemas/          # (Uso incipiente) Schemas adicionais
```

### Detalhamento das Camadas

1.  **Routers (`app/routers/`)**:
    *   Atuam como a camada de entrada (Controllers).
    *   Responsáveis por definir os endpoints HTTP, validação de entrada (via Pydantic) e injeção de dependências.
    *   Divididos semanticamente em:
        *   `management/`: Operações CRUD (Create, Read, Update, Delete).
        *   `reports/`: Endpoints de leitura agregada e relatórios.
    *   **Padrão Observado**: Os routers delegam a execução lógica diretamente para as funções da camada de `repositories`.

2.  **Repositories (`app/repositories/`)**:
    *   Centralizam a lógica de interação com o banco de dados.
    *   Utilizam **SQLAlchemy Core** (construtores de query explícitos como `insert`, `select`, `update`) em vez do ORM de alto nível (Session.add).
    *   Realizam a conversão dos resultados do banco (Row objects) para os modelos Pydantic de saída.

3.  **Models (`app/models/`)**:
    *   Contém as definições de **Pydantic Models** (ex: `AccountCreate`, `AccountOut`).
    *   *Nota*: Apesar do nome `models`, estes arquivos atuam como **Schemas** ou **DTOs** (Data Transfer Objects), definindo a estrutura de dados trafegada na API, e não as tabelas do banco de dados.

4.  **Database (`app/db/`)**:
    *   Define a estrutura real do banco de dados (Tabelas) usando metadados do SQLAlchemy.

## Fluxo de Dados

O fluxo típico de uma requisição é:
1.  **Request** chega ao `Router`.
2.  `Router` valida os dados usando um modelo de entrada (`app/models`).
3.  `Router` chama uma função no `Repository`, passando a sessão do banco.
4.  `Repository` constrói a query SQL e a executa no banco.
5.  `Repository` mapeia o resultado bruto para um modelo de saída (`app/models`).
6.  **Response** é devolvida ao cliente.

## Pontos de Atenção e Oportunidades de Melhoria

Durante a análise, foram identificados os seguintes pontos para potenciais melhorias:

1.  **Nomenclatura de Pastas (Models vs Schemas)**:
    *   A pasta `app/models/` contém classes Pydantic, que convencionalmente são chamadas de "schemas" em projetos FastAPI.
    *   Existe uma pasta `app/schemas/` contendo apenas `bank_statement.py`.
    *   **Sugestão**: Padronizar. Mover tudo para `app/schemas/` ou decidir explicitamente que `models` refere-se aos modelos de domínio/API.

2.  **Service Layer (Ausente/Misturada)**:
    *   Atualmente, a regra de negócio reside dentro dos `repositories`.
    *   Para operações simples (CRUD), isso é eficiente.
    *   Para regras de negócio complexas que não envolvem apenas banco de dados (ex: envio de email, cálculos complexos, chamadas a APIs externas), o padrão Repository pode ficar sobrecarregado.
    *   **Sugestão**: Avaliar a necessidade de uma camada de `services` se a complexidade aumentar.

3.  **Inconsistência na Localização de Schemas**:
    *   O arquivo `app/schemas/bank_statement.py` está isolado. O ideal seria que todos os schemas estivessem agrupados.

4.  **SQLAlchemy Core vs ORM**:
    *   O uso do Core (`insert(table)`) é performático, mas exige mapeamento manual para objetos Pydantic no retorno. Isso gera código repetitivo nos repositórios (ex: instanciar `AccountOut` campo a campo).
    *   **Sugestão**: Avaliar o uso de `row_mapping` ou ferramentas como SQLModel para reduzir o boilerplate de mapeamento.
