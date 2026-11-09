# Situação da validação técnica

Este arquivo diferencia **o que foi checado nesta preparação** do que ainda precisa ser executado no computador do estudante. Nenhum resultado de integração deve ser inventado.

## Verificações realizadas

- Código Python submetido à compilação/sintaxe (`python -m compileall -q app scripts tests run.py`).
- JavaScript submetido à verificação de sintaxe (`node --check app/static/app.js`).
- Regras de entrada, limite de cadastros e transformação de JSON de clima foram executados localmente com entradas fictícias/mocks: **OK** (não é teste integrado da API).
- Relatório PDF renderizado e revisado: **3 páginas**, com fontes e declaração de IA.
- Fontes utilizadas para a justificativa checadas: FIAP Experience (eixos de cidades/dados), Cemaden (2025, p. 32) e Open-Meteo (documentação da Forecast API).

## Verificações pendentes de execução integrada

A execução de `pytest` **não foi concluída** durante a montagem inicial, pois o ambiente de criação não tinha Flask e PyMySQL instalados e não conseguia acessar o índice do pip. Por isso **não se declara que todos os testes passaram**.

Faça em seu computador após `pip install -r requirements.txt`:

```bash
python -m pytest -q
python -m compileall -q app scripts tests run.py
```

Com Docker Desktop instalado:

```bash
docker compose up -d
python -m scripts.init_db
python -m scripts.seed_demo
python run.py
```

No navegador, confira o GET, POST, PUT e DELETE. Execute também `python -m app.tcp_server` e `python -m app.tcp_client` em terminais separados e confirme o clima em `/api/clima` (internet necessária). Anote os resultados reais antes de apresentar e atualize esta seção e o relatório, se preciso.

## Regras da avaliação

O projeto utiliza assistência de IA declarada no relatório. O estudante deve compreender, modificar e justificar o código que apresentar. O campo de identificação do relatório precisa ser preenchido; a publicação no GitHub ainda não foi feita.
