## 📊 Projeto de Coleta e Análise de Índices Financeiros

### 🏦 Sobre o Projeto

Este projeto tem como objetivo coletar, armazenar e analisar índices financeiros dos mercados do Brasil, China e Estados Unidos a partir do site Investing.com. Ele segue um fluxo ETL (Extract, Transform, Load) para garantir a correta manipulação e análise dos dados.



### 🔍 1️⃣ Extração (Extract)

O script acessa o site Investing.com.

Coleta os dados financeiros relevantes, incluindo:

- Nome do Índice
- Valor Atual
- Valor Máximo
- Valor Mínimo
- Variação Percentual

Identifica o país de origem e classifica automaticamente o setor econômico (Primário, Secundário ou Terciário).

### 🔄 2️⃣ Transformação (Transform)

Os dados brutos extraídos são processados e normalizados:

- Conversão de formatos numéricos (pontos e vírgulas ajustados para float).

- Padronização dos nomes dos índices.

- Classificação automática do setor econômico conforme o país.

### 🏦 3️⃣ Carregamento (Load)

Os dados são armazenados em um banco de dados PostgreSQL, estruturado em três tabelas:

- pais (Brasil, China, EUA)

- setor (Primário, Secundário, Terciário)

- indice_financeiro (Valores e variações dos índices)

Caso um país ou setor ainda não exista, ele é criado dinamicamente no banco.

### 📊 4️⃣ Análise e Consulta

Um relatório pode ser gerado diretamente do banco de dados.

O sistema permite consultas avançadas, como os 10 índices mais altos dos setores primário, secundário e terciário.

Exemplo de consulta SQL:

```SELECT nome, pais, setor, maxima
FROM indice_financeiro
JOIN pais ON indice_financeiro.pais_id = pais.id
JOIN setor ON indice_financeiro.setor_id = setor.id
WHERE pais IN ('China', 'EUA')
ORDER BY maxima DESC
LIMIT 10;
```

#### 📂 Estrutura do Projeto

main.py ➝ Contém o código principal do fluxo ETL.

Observação: a estrutura será refatorada.


### 🛠️ Tecnologias Utilizadas

- Python 🐍 (Requests, BeautifulSoup, Pandas, SQLAlchemy)
- PostgreSQL 🗄️ (Banco de Dados Relacional)
- Git & GitHub 🛠️ (Controle de Versão)
- Dotenv (Armazenamento de variáveis de ambiente)
- SQLAlchemy (Conexão com banco de dados e Modelagem de Dados)



Clone o repositório:

git clone https://github.com/seu-usuario/nome-do-repositorio.git

Instale as dependências:

``pip install -r requirements.txt``

Configure as variáveis de ambiente no arquivo .env.

Execute o pipeline ETL:

`python etl.py`

Acesse os resultados no banco de dados e gere relatórios.

