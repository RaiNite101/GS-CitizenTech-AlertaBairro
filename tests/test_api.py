from unittest.mock import patch
from app import db

DADO = {'id': 7, 'regiao': 'centro', 'tipo': 'alagamento', 'intensidade': 'alta',
        'status': 'aberto', 'origem': 'comunidade', 'criado_em': '2026-11-09T10:00:00Z',
        'atualizado_em': '2026-11-09T10:00:00Z'}
CHAVE = {'X-Admin-Key': 'chave_ficticia_de_testes_super_longa_123'}


def test_web_e_cabecalhos(client):
    resposta = client.get('/')
    assert resposta.status_code == 200
    assert b'AlertaBairro' in resposta.data
    assert "script-src 'self'" in resposta.headers['Content-Security-Policy']
    assert resposta.headers['X-Frame-Options'] == 'DENY'


def test_saude(client):
    assert client.get('/api/saude').json['status'] == 'online'


def test_get_lista(client):
    with patch('app.db.listar', return_value=[DADO]) as mock:
        resp = client.get('/api/ocorrencias?status=aberto')
    assert resp.status_code == 200
    assert resp.json['total_retornado'] == 1
    mock.assert_called_once()
    assert mock.call_args.args[1] == 'aberto'


def test_get_filtro_invalido(client):
    assert client.get('/api/ocorrencias?status=invalido').status_code == 422
    assert client.get('/api/ocorrencias?debug=1').status_code == 422


def test_get_individual_404(client):
    with patch('app.db.obter', return_value=None):
        assert client.get('/api/ocorrencias/90').status_code == 404


def test_post_cria_201(client):
    with patch('app.db.criar', return_value=DADO) as mock:
        resp = client.post('/api/ocorrencias', json={
            'regiao': 'centro', 'tipo': 'alagamento', 'intensidade': 'alta'})
    assert resp.status_code == 201
    assert resp.headers['Location'] == '/api/ocorrencias/7'
    assert resp.json['id'] == 7
    assert mock.call_args.args[1] == {'regiao': 'centro', 'tipo': 'alagamento', 'intensidade': 'alta'}


def test_post_valida_entrada(client):
    resp = client.post('/api/ocorrencias', json={'regiao': 'centro'})
    assert resp.status_code == 422
    assert 'erro' in resp.json
    assert client.post('/api/ocorrencias', data='texto').status_code == 415
    assert client.post('/api/ocorrencias', data='{', content_type='application/json').status_code == 400


def test_put_exige_chave(client):
    assert client.put('/api/ocorrencias/7', json={'status': 'resolvido'}).status_code == 403
    assert client.put('/api/ocorrencias/7', headers={'X-Admin-Key':'errada'}, json={'status':'resolvido'}).status_code == 403


def test_put_atualiza(client):
    atualizado = {**DADO, 'status': 'resolvido'}
    with patch('app.db.atualizar_status', return_value=atualizado) as mock:
        resp = client.put('/api/ocorrencias/7', json={'status': 'resolvido'}, headers=CHAVE)
    assert resp.status_code == 200
    assert resp.json['status'] == 'resolvido'
    mock.assert_called_once()


def test_put_rejeita_campo_invalido(client):
    assert client.put('/api/ocorrencias/7', json={'status': 'resolvido', 'id': 12}, headers=CHAVE).status_code == 422


def test_delete_204(client):
    with patch('app.db.excluir', return_value=True):
        resp = client.delete('/api/ocorrencias/7', headers=CHAVE)
    assert resp.status_code == 204
    assert not resp.data


def test_delete_404(client):
    with patch('app.db.excluir', return_value=False):
        resp = client.delete('/api/ocorrencias/900', headers=CHAVE)
    assert resp.status_code == 404


def test_resumo(client):
    with patch('app.db.resumo', return_value={'total': 3, 'por_status': {'aberto': 1, 'em_analise': 1, 'resolvido': 1}}):
        resp = client.get('/api/resumo')
    assert resp.json['total'] == 3


def test_banco_indisponivel(client):
    with patch('app.db.listar', side_effect=db.BancoIndisponivel()):
        resp = client.get('/api/ocorrencias')
    assert resp.status_code == 503
    assert 'Banco temporariamente indisponível' in resp.json['erro']


def test_erro_interno_nao_expoe_detalhes(client):
    with patch('app.db.resumo', side_effect=Exception('senha_privada_ABC')):
        resp = client.get('/api/resumo')
    assert resp.status_code == 500
    assert 'senha_privada_ABC' not in resp.get_data(as_text=True)


def test_tamanho_maximo(client):
    resp = client.post('/api/ocorrencias', data='x'*9000, content_type='application/json')
    assert resp.status_code == 413


def test_log_nao_registra_caminho_arbitrario(client, app):
    from pathlib import Path
    client.get('/api/segredo_colocado_na_url')
    registro = (Path(app.config['LOG_DIR']) / 'acoes.log').read_text(encoding='utf-8')
    assert 'segredo_colocado_na_url' not in registro
    assert '/api/[rota_desconhecida]' in registro
