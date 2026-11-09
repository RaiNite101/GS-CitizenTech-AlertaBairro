"""Insere três ocorrências MARCADAS COMO FICTÍCIAS para apresentação."""
from app import db
from app.config import Config

EXEMPLOS = [
    {'regiao': 'zona_leste', 'tipo': 'alagamento', 'intensidade': 'alta'},
    {'regiao': 'centro', 'tipo': 'bueiro_obstruido', 'intensidade': 'moderada'},
    {'regiao': 'zona_sul', 'tipo': 'via_intransitavel', 'intensidade': 'baixa'},
]

if __name__ == '__main__':
    cfg = {chave: getattr(Config, chave) for chave in (
        'MYSQL_HOST', 'MYSQL_PORT', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DATABASE')}
    try:
        for item in EXEMPLOS:
            registro = db.criar(cfg, item, origem='demo')
            print('Ocorrência fictícia criada:', registro['id'])
    except db.BancoIndisponivel:
        raise SystemExit('Banco indisponível. Execute scripts/init_db.py antes.')
