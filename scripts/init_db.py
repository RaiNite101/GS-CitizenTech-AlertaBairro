"""Inicializa tabela MySQL depois de docker compose up -d."""
from app import db
from app.config import Config

if __name__ == '__main__':
    cfg = {chave: getattr(Config, chave) for chave in (
        'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE')}
    try:
        db.inicializar(cfg)
        print('Tabela ocorrencias pronta.')
    except db.BancoIndisponivel:
        raise SystemExit('MySQL indisponível. Verifique docker compose e .env.')
