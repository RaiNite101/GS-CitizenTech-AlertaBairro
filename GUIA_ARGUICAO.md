# Guia de estudo para a arguição individual

Este guia é para **compreender e testar** o projeto. Leia os arquivos antes de apresentar: as regras da GS exigem explicar o código. Não memorize frases sem conhecer as funções.

## Entendendo cada parte

1. **Por que este problema?** Alagamentos prejudicam o deslocamento e a segurança das pessoas. A fonte de evidência é o relatório do Cemaden (2.505 alertas em 2025 no Brasil, incluindo 49 em São Paulo). A FIAP propôs os eixos cidades inteligentes e dados para decisões reais; adaptamos isso ao problema de alagamentos, sem afirmar que a página apresenta esse projeto específico.
2. **Por que Flask?** É um framework Python para mapear rotas HTTP, ler JSON, retornar JSON e códigos como 201, 404 e 503.
3. **Onde está o CRUD?** Em `app/db.py`: `listar/obter` = SELECT, `criar` = INSERT, `atualizar_status` = UPDATE, `excluir` = DELETE.
4. **Por que SQL parametrizado?** A consulta tem `%s` e os valores são enviados separadamente para o driver; isso impede que entradas sejam tratadas como instruções SQL.
5. **Quais dados ficam no banco?** ID, região ampla, categoria, intensidade, situação, origem e datas; não existem nomes, telefones ou endereços.
6. **De onde vêm os dados de chuva?** `app/clima.py` envia `requests.get` para Open-Meteo; `response.json()` converte o retorno em dicionários e listas.
7. **O que significam 3.5 mm e 70%?** São, respectivamente, a soma prevista da precipitação nas próximas horas e o maior percentual horário de probabilidade de chuva; **não** indicam chance de inundação.
8. **Qual é o socket TCP?** `tcp_server.py` recebe `STATUS\n` em 127.0.0.1:9099 e devolve JSON agregado; `tcp_client.py` demonstra o cliente.
9. **O que aparece no log?** Data e hora, método e rota genérica, status HTTP e sucesso/falha. Nunca se grava a chave administrativa nem conteúdo do cidadão.
10. **Quais 3 ameaças?** Injeção SQL, alteração não autorizada, spam/falsos relatos. Mitigações: parâmetros, segredo + compare_digest, campos fixos + limitação de POST.
11. **Por que `.env` e `.env.example`?** `.env` contém segredos reais locais e é ignorado pelo Git; `.env.example` é somente um modelo, sem segredos reais.
12. **Como demonstrar 4 métodos?** Crie via formulário (POST 201), atualize a lista (GET 200), informe a chave e altere o status (PUT 200), depois exclua (DELETE 204).

## Perguntas difíceis que podem aparecer

**O sistema prevê enchentes?** Não. Ele apresenta previsão meteorológica da Open-Meteo e relatos colaborativos ainda não verificados. Não calcula risco hidrológico nem realiza alerta oficial.

**Por que não permitir que qualquer usuário edite e exclua?** Alterações exigem chave de moderação. Qualquer cidadão pode registrar, mas não alterar dados de terceiros.

**E se alguém inserir SQL malicioso?** A validação aceita somente categorias pré-definidas e o driver faz parametrização nas queries que recebem dados.

**Isso já está pronto para produção?** Não. Precisaria de autenticação individual, HTTPS, moderação/verificação, rate limit persistente, monitoramento e governança de dados.

**Qual é o bônus?** Testes automáticos com pytest no GitHub Actions, cabeçalhos de segurança e Docker Compose simplificam validação/reprodutibilidade; explique apenas o que você entendeu e realmente testou.

## Checklist para demonstração

- [ ] `.env` preenchido com senhas e chave alteradas.
- [ ] `docker compose ps` mostra MySQL saudável.
- [ ] `python -m scripts.init_db` executado.
- [ ] `python run.py` rodando; página abre em 127.0.0.1:5000.
- [ ] Formulário salva e indicadores mudam.
- [ ] Dados da Open-Meteo carregam quando há internet.
- [ ] Filtros e funções de administrador funcionam.
- [ ] `python -m app.tcp_server` e `python -m app.tcp_client` exibem JSON.
- [ ] `python -m pytest -q` executado na máquina com dependências.
- [ ] `logs/acoes.log` contém ações sem dados pessoais.
- [ ] Relatório em PDF e link do GitHub preparados.
