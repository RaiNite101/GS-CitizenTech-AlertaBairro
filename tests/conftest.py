import pytest
from app import create_app


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'TESTING': True,
        'LOG_DIR': tmp_path / 'logs',
        'APP_ADMIN_KEY': 'chave_ficticia_de_testes_super_longa_123',
    })
    yield app
    for handler in app.extensions['acoes_logger'].handlers:
        handler.close()


@pytest.fixture
def client(app):
    return app.test_client()
