"""Application factory: Flask + rotas + segurança + logging."""
import hmac
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from flask import Flask, jsonify, render_template, request
from werkzeug.exceptions import HTTPException
from .config import Config, ROOT
from . import db
from . import clima
from .validacao import EntradaInvalida, validar_ocorrencia, validar_atualizacao, validar_id, validar_filtro_status
from .limite import Limitador


def create_app(test_config=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    # Apenas ações e resultados: não registra IP, headers, tokens, corpo ou dados de cidadãos.
    log_dir = Path(app.config.get('LOG_DIR', ROOT / 'logs'))
    log_dir.mkdir(exist_ok=True, parents=True)
    logger = logging.getLogger(f'alertabairro.{id(app)}')
    logger.setLevel(logging.INFO)
    logger.propagate = False
    handler = RotatingFileHandler(log_dir / 'acoes.log', maxBytes=1_000_000,
                                  backupCount=3, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s'))
    logger.addHandler(handler)
    app.extensions['acoes_logger'] = logger
    limitador = Limitador(limite=5, janela=60)

    def somente_administrador():
        segredo = app.config['APP_ADMIN_KEY']
        recebido = request.headers.get('X-Admin-Key', '')
        # Nunca aceitar uma chave administrativa vazia ou curta.
        if not segredo or len(segredo) < 24:
            return jsonify({'erro': 'Administração não configurada.'}), 503
        if not hmac.compare_digest(segredo, recebido):
            return jsonify({'erro': 'Acesso não autorizado.'}), 403
        return None

    def corpo_json():
        if not request.is_json:
            return None, (jsonify({'erro': 'Use Content-Type: application/json.'}), 415)
        dados = request.get_json(silent=True)
        if not isinstance(dados, dict):
            return None, (jsonify({'erro': 'JSON inválido.'}), 400)
        return dados, None

    @app.after_request
    def cabecalhos_e_logs(resp):
        resp.headers['Content-Security-Policy'] = (
            "default-src 'self'; img-src 'self' data:; script-src 'self'; "
            "style-src 'self'; connect-src 'self'; object-src 'none'; "
            "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        )
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['Referrer-Policy'] = 'no-referrer'
        resp.headers['X-Frame-Options'] = 'DENY'
        if request.path.startswith('/api/'):
            resultado = 'SUCESSO' if resp.status_code < 400 else 'FALHA'
            # Usa o PADRÃO de rota, não o caminho enviado. Evita registrar
            # IDs e segmentos arbitrários de URL nos logs.
            rota = request.url_rule.rule if request.url_rule is not None else '/api/[rota_desconhecida]'
            logger.info('%s %s | HTTP %s | %s',
                        request.method, rota, resp.status_code, resultado)
            resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.errorhandler(EntradaInvalida)
    def erro_validacao(_erro):
        return jsonify({'erro': str(_erro)}), 422

    @app.errorhandler(db.BancoIndisponivel)
    def erro_banco(_erro):
        return jsonify({'erro': 'Banco temporariamente indisponível.'}), 503

    @app.errorhandler(clima.ClimaIndisponivel)
    def erro_clima(_erro):
        return jsonify({'erro': 'Dados meteorológicos indisponíveis.'}), 503

    @app.errorhandler(HTTPException)
    def erro_http(erro):
        if erro.code == 413:
            return jsonify({'erro': 'Dados maiores que o permitido.'}), 413
        return jsonify({'erro': 'Requisição não atendida.'}), erro.code

    @app.errorhandler(Exception)
    def erro_inesperado(_erro):
        logger.error('Falha inesperada | detalhe omitido por segurança')
        return jsonify({'erro': 'Erro interno. Tente novamente mais tarde.'}), 500

    @app.get('/')
    def inicio():
        return render_template('index.html')

    @app.get('/api/saude')
    def saude():
        return jsonify({'servico': 'AlertaBairro', 'status': 'online'})

    @app.get('/api/ocorrencias')
    def listar():
        filtro = validar_filtro_status(request.args.get('status'))
        if set(request.args) - {'status'}:
            raise EntradaInvalida('Filtro desconhecido.')
        dados = db.listar(app.config, filtro)
        return jsonify({'total_retornado': len(dados), 'ocorrencias': dados})

    @app.get('/api/ocorrencias/<int:identificador>')
    def detalhar(identificador):
        encontrado = db.obter(app.config, validar_id(identificador))
        if encontrado is None:
            return jsonify({'erro': 'Ocorrência não encontrada.'}), 404
        return jsonify(encontrado)

    @app.post('/api/ocorrencias')
    def cadastrar():
        dados, erro = corpo_json()
        if erro:
            return erro
        entrada = validar_ocorrencia(dados)
        if not app.config['TESTING'] and not limitador.permitir(request.remote_addr or 'desconhecido'):
            return jsonify({'erro': 'Limite temporário de registros atingido.'}), 429
        criado = db.criar(app.config, entrada)
        response = jsonify(criado)
        response.status_code = 201
        response.headers['Location'] = f"/api/ocorrencias/{criado['id']}"
        return response

    @app.put('/api/ocorrencias/<int:identificador>')
    def editar(identificador):
        nao_autorizado = somente_administrador()
        if nao_autorizado:
            return nao_autorizado
        dados, erro = corpo_json()
        if erro:
            return erro
        status = validar_atualizacao(dados)
        atualizado = db.atualizar_status(app.config, validar_id(identificador), status)
        if atualizado is None:
            return jsonify({'erro': 'Ocorrência não encontrada.'}), 404
        return jsonify(atualizado)

    @app.delete('/api/ocorrencias/<int:identificador>')
    def apagar(identificador):
        nao_autorizado = somente_administrador()
        if nao_autorizado:
            return nao_autorizado
        if not db.excluir(app.config, validar_id(identificador)):
            return jsonify({'erro': 'Ocorrência não encontrada.'}), 404
        return '', 204

    @app.get('/api/resumo')
    def resumo():
        return jsonify(db.resumo(app.config))

    @app.get('/api/clima')
    def previsao():
        return jsonify(clima.consultar())

    return app
