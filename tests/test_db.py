"""Testes de SQL parametrizado e PUT idempotente sem banco real."""
from contextlib import contextmanager
from unittest.mock import patch
from app import db


class CursorFalso:
    def __init__(self):
        self.sql = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def execute(self, sql, params):
        self.sql = sql
        self.params = params

    def fetchone(self):
        return {'id': 123456, 'regiao': 'centro', 'tipo': 'alagamento',
                'intensidade': 'alta', 'status': 'resolvido'}


class ConexaoFalsa:
    def __init__(self):
        self.c = CursorFalso()
        self.commits = 0

    def cursor(self):
        return self.c

    def commit(self):
        self.commits += 1


def test_select_parametrizado():
    conexao = ConexaoFalsa()

    @contextmanager
    def fake_conexao(_config):
        yield conexao

    with patch('app.db.conexao', new=fake_conexao):
        registro = db.obter({}, 123456)

    assert registro['id'] == 123456
    assert 'WHERE id = %s' in conexao.c.sql
    assert conexao.c.params == (123456,)
    assert '123456' not in conexao.c.sql


def test_put_repetido_retorna_registro_existente():
    conexao = ConexaoFalsa()

    @contextmanager
    def fake_conexao(_config):
        yield conexao

    with patch('app.db.conexao', new=fake_conexao), \
         patch('app.db.obter', return_value={'id': 7, 'status': 'resolvido'}):
        registro = db.atualizar_status({}, 7, 'resolvido')

    assert registro == {'id': 7, 'status': 'resolvido'}
    assert conexao.c.params == ('resolvido', 7)
    assert conexao.commits == 1
