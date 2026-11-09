# AlertaBairro — Global Solution CitizenTech

**Coding for Security | FIAP | 2026**  
**Tema:** monitoramento colaborativo de ocorrências associadas à chuva, em São Paulo.  
**ODS:** 9 (inovação e infraestrutura), 11 (cidades sustentáveis) e 13 (ação climática).

> **ATENÇÃO:** projeto acadêmico. Registros de cidadãos são **não verificados**. A previsão da Open-Meteo é meteorológica, **não é um cálculo de risco de alagamento** e não equivale a aviso da Defesa Civil. Para emergências, consulte os canais oficiais (Defesa Civil 199 e Bombeiros 193).

## 1. Problema e cidadão

Moradores e pessoas que se deslocam em São Paulo precisam de informações fáceis de encontrar sobre problemas causados por chuvas nas regiões da cidade. O Cemaden publicou **2.505 alertas geo-hidrológicos no país em 2025**, dos quais **49 foram direcionados ao município de São Paulo**. A proposta aplica os eixos **“Cidades mais inteligentes”** e **“Dados para decisões reais”** da página Experience FIAP CitizenTech a um problema concreto de chuva e mobilidade, com evidência pública e **relatos fictícios** para a demonstração. É uma adaptação acadêmica do tema geral, não uma ideia específica afirmada pela página.

O AlertaBairro permite cadastrar relatos **sem nomes, telefone, e-mail, endereço específico ou coordenadas pessoais**. Coleta apenas região ampla, tipo, intensidade e situação. Os registros são informações comunitárias, não comprovações oficiais.

## 2. Funcionalidades

- **Flask REST:** GET (lista e detalha), POST (insere), PUT (atualiza situação), DELETE (exclui); status HTTP adequados.
- **MySQL 8.4:** CRUD com **SQL escrito em Python + PyMySQL**, sem ORM; parâmetros `%s` em operações com valores.
- **Fonte externa:** requisição HTTPS usando `requests` à Open-Meteo; retorna maior probabilidade horária de chuva e soma de milímetros previstos nas próximas 24 horas.
- **Frontend:** HTML, CSS e JavaScript com `fetch`, com formulário, filtros, indicadores e moderação.
- **Logs:** `logs/acoes.log` registra data/hora, método, tipo de rota, código HTTP e SUCESSO/FALHA; não salva IPs ou tokens.
- **Redes:** servidor **TCP** local, porta 9099, que responde ao comando `STATUS` com contagem dos registros.
- **Segurança:** credenciais em `.env`, validação restrita por lista, limite de requisições POST, autenticação administrativa para PUT/DELETE, cabeçalhos HTTP de segurança, mensagens de erro genéricas e proteção contra exposição de dados.
- **Testes:** `pytest` para rotas, status HTTP, regras de entrada, respostas de erros e mock de previsão climática.

## 3. Arquitetura

```text
 [Navegador - HTML/CSS/JS]
             |
        HTTP / fetch
             v
      [API Flask] ----------------> [Open-Meteo /v1/forecast]
        |     |                            | HTTPS + requests/JSON
        |     +--> [Logs de ações]
        |
        +--> [PyMySQL + SQL parametrizado] --> [Banco MySQL]
        ^
        |
 [Servidor TCP local] <---- [Cliente TCP: STATUS]
```

**Tabela `ocorrencias`:**

| Campo | Tipo MySQL | Observação |
| --- | --- | --- |
| `id` | INT UNSIGNED | PK autoincremento |
| `regiao` | VARCHAR(20) | 5 regiões amplas possíveis |
| `tipo` | VARCHAR(24) | alagamento, bueiro obstruído, via prejudicada |
| `intensidade` | VARCHAR(10) | baixa, moderada, alta |
| `status` | VARCHAR(12) | aberto, em_analise, resolvido |
| `origem` | VARCHAR(12) | `demo` ou `comunidade` |
| `criado_em`, `atualizado_em` | TIMESTAMP | armazenamento em UTC |

A API retorna no máximo **100 relatos recentes** por consulta; não existe paginação nesta versão.

## 4. Instalação do zero

Pré-requisitos: **Python 3.10+**, **Docker Desktop** (com Docker Compose), internet para baixar dependências e obter a previsão meteorológica. Todo o procedimento a seguir é local, no próprio computador.

### 4.1 Preparar o diretório

Abra um terminal na pasta `AlertaBairro_GS`.

**Windows / PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

**Linux / macOS:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

Edite o arquivo **`.env`**, troque as duas senhas de banco e a chave de administração. Para gerar uma chave aleatória:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Cole o resultado em `APP_ADMIN_KEY=`. A chave precisa ter pelo menos **24 caracteres**. Mantenha `.env` fora do GitHub (já listado em `.gitignore`).

### 4.2 Iniciar o MySQL

```bash
docker compose up -d
docker compose ps
```

Espere o MySQL aparecer como **healthy**. Em seguida:

```bash
python -m scripts.init_db
```

O script cria a tabela necessária, mas **não cria contas de banco**: a conta MySQL é criada pelo Docker Compose na primeira inicialização do volume.

> Caso altere as credenciais do MySQL após já ter criado o volume, a imagem Docker não as modifica automaticamente. Reconfigure a conta de forma adequada ou inicialize um novo ambiente de testes; `docker compose down -v` **apaga todos os dados**.

### 4.3 Inserir exemplos fictícios (opcional)

```bash
python -m scripts.seed_demo
```

Cria **3 registros fictícios** identificados na tela com a etiqueta "DADO FICTÍCIO DE DEMONSTRAÇÃO". Cada execução adiciona mais 3 registros. Não use relatos simulados como informação verdadeira.

### 4.4 Executar a aplicação

```bash
python run.py
```

Abra no navegador: **http://127.0.0.1:5000**.

A senha administrativa só é exigida para **editar situação** e **excluir** um registro. Para registrar um novo relato, selecione as três categorias do formulário e envie.

### 4.5 Testar o módulo TCP

Abra um **segundo terminal** com o ambiente Python ativado:

```bash
python -m app.tcp_server
```

Em um **terceiro terminal** execute:

```bash
python -m app.tcp_client
```

Exemplo de resposta (`total` varia conforme o banco):

```json
{"servico":"AlertaBairro","total":3,"por_status":{"aberto":3,"em_analise":0,"resolvido":0}}
```

A porta **9099** escuta exclusivamente em `127.0.0.1`. TCP é um módulo adicional independente da API Flask.

## 5. Endpoints REST

| Método | Rota | Função | Sucesso | Erros típicos |
|---|---|---|---|---|
| GET | `/api/ocorrencias` | Listar (filtro opcional `?status=aberto`) | 200 | 422, 503 |
| GET | `/api/ocorrencias/7` | Detalhar um registro | 200 | 404, 503 |
| POST | `/api/ocorrencias` | Criar relato | 201 + Location | 400, 415, 422, 429 |
| PUT | `/api/ocorrencias/7` | Mudar status (chave admin) | 200 | 403, 404, 422 |
| DELETE | `/api/ocorrencias/7` | Excluir (chave admin) | 204 | 403, 404 |
| GET | `/api/clima` | Consultar previsão da Open-Meteo | 200 | 503 |
| GET | `/api/resumo` | Contagens por situação | 200 | 503 |
| GET | `/api/saude` | Verifica funcionamento HTTP | 200 | — |

### Exemplo de requisição POST

**PowerShell (Windows):**

```powershell
$corpo = @{regiao='zona_leste'; tipo='alagamento'; intensidade='alta'} | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/ocorrencias -Method Post -ContentType 'application/json' -Body $corpo
```

**Bash:**

```bash
curl -i -X POST http://127.0.0.1:5000/api/ocorrencias \
  -H 'Content-Type: application/json' \
  -d '{"regiao":"zona_leste","tipo":"alagamento","intensidade":"alta"}'
```

**Atualização de situação (exemplo usando shell Bash):**

```bash
curl -i -X PUT http://127.0.0.1:5000/api/ocorrencias/1 \
  -H 'Content-Type: application/json' \
  -H "X-Admin-Key: $APP_ADMIN_KEY" \
  -d '{"status":"resolvido"}'
```

No PowerShell, é mais fácil usar a própria interface web: cole a chave no campo de moderação. A chave nunca deve ser colocada diretamente em código, prints ou repositórios.

## 6. Testes

```bash
python -m pytest -q
python -m compileall -q app scripts tests run.py
```

Os testes de API utilizam mocks e **não requerem um banco real nem internet**. Para verificar a integração completa, execute Docker, inicialize a tabela e teste o fluxo GET/POST/PUT/DELETE no navegador. Para validar o clima real, o computador deve ter acesso à Open-Meteo.

O GitHub Actions em `.github/workflows/testes.yml` realiza os testes automaticamente em pushes e pull requests (**recurso complementar** à disciplina).

## 7. Segurança, LGPD e limites

| Ameaça | Mitigação implementada | Limitação |
|---|---|---|
| Injeção SQL | SQL com placeholders `%s` no PyMySQL + listas de valores permitidos | O servidor e o MySQL devem ser atualizados |
| Acesso indevido e alteração de relatos | PUT/DELETE exigem chave longa em `X-Admin-Key` verificada com `hmac.compare_digest` | Uma chave compartilhada não substitui login e perfis de produção |
| Spam, dados falsos e abuso de formulário | Campos fixos sem dados pessoais + limite de 5 POST/minuto por IP em memória | Relatos não são verificados; limitação reinicia ao reiniciar app |

**Medidas adicionais:** credenciais no `.env`, não versionado; servidor Flask em 127.0.0.1 com debug desativado; MySQL publicado apenas em 127.0.0.1; CSP e cabeçalhos anti-clickjacking; logs sem payloads ou tokens; limite de JSON em 8 KB; nenhuma coleta de nome, contato, GPS ou endereço exato; frontend com `textContent` para não renderizar HTML injetado.

**Limitações assumidas:**

1. Os relatos comunitários **não possuem checagem oficial** e não são alertas de emergência.
2. O clima usa coordenadas fixas próximas ao centro de São Paulo; não representa microclimas de cada região.
3. Não há implantação pública, HTTPS, autenticação com usuários, paginação, moderação automática, persistência de rate limit ou proteção completa contra abuso; seriam requisitos para produção.
4. A API externa pode ficar indisponível. O sistema retorna **503** sem expor detalhes de rede.
5. O recurso TCP entrega somente uma contagem local (sem transmissão de dados privados).

## 8. Publicação no GitHub

1. Crie um repositório **vazio** no GitHub (por exemplo, `alertabairro-gs`).
2. Na pasta do projeto, execute:

```bash
git init
git add .
git commit -m "Global Solution - AlertaBairro CitizenTech"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/alertabairro-gs.git
git push -u origin main
```

3. Confirme que `.env`, `.venv/`, `logs/acoes.log` e `__pycache__/` não foram enviados. O `.env.example` deve ser enviado.
4. Se quiser mudar o histórico antes de enviar, verifique `git status` e `git ls-files`.

**Não há repositório remoto criado automaticamente com este ZIP.** O link do GitHub deve ser preenchido pelo estudante após a publicação.

## 9. Créditos e uso de IA

- **Inspiração:** [Experience FIAP — CitizenTech](https://experience.fiap.com.br/global-solution-citizen-tech).
- **Evidência:** [Cemaden, Relatório Estado do Clima no Brasil 2025, publicado em fev. 2026, pp. 31–32](https://www.gov.br/cemaden/pt-br/assuntos/monitoramento/estado-do-clima-extremos-de-clima-e-desastres-no-brasil/estado-do-clima-extremos-de-clima-e-desastres-no-brasil-02-2026/relatorioclimaextremosdesastresbrasil2025.pdf).
- **Serviço de dados:** [Open-Meteo Weather Forecast API](https://open-meteo.com/en/docs) (ver termos e atribuição do serviço).
- **Bibliotecas:** Flask, PyMySQL, Requests, python-dotenv, pytest, tzdata; versões em `requirements.txt`.
- **IA generativa:** este protótipo, sua estrutura, documentação e a proposta de relatório foram preparados **com assistência de ChatGPT (OpenAI)**. O estudante deve revisar, compreender, executar, adaptar e declarar essa assistência na entrega, conforme as regras da disciplina. Nunca apresente código de IA como autoria humana exclusiva.

## 10. Estrutura de arquivos

```text
AlertaBairro_GS/
├── app/
│   ├── __init__.py          # endpoints Flask, logging, segurança
│   ├── config.py            # variáveis de ambiente
│   ├── db.py                # SQL parametrizado e CRUD MySQL
│   ├── validacao.py         # regras de entrada
│   ├── clima.py             # requests + JSON externo
│   ├── limite.py            # proteção simples contra spam
│   ├── tcp_server.py       # servidor socket TCP local
│   ├── tcp_client.py       # cliente TCP de demonstração
│   ├── templates/index.html
│   └── static/style.css, app.js
├── scripts/init_db.py      # criação da tabela
├── scripts/seed_demo.py    # exemplos explicitamente fictícios
├── tests/                  # testes automatizados
├── docs/                   # relatório em PDF
├── .github/workflows/      # GitHub Actions, recurso extra
├── .env.example            # modelo de credenciais (sem segredos reais)
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── run.py
```

**Roteiro de apresentação:** veja `GUIA_ARGUICAO.md`.
