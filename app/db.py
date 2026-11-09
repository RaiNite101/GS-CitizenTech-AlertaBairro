"""CRUD em MySQL com PyMySQL e SQL parametrizado, SEM ORM."""
from contextlib import contextmanager
from datetime import datetime, timezone
import pymysql
from pymysql.cursors import DictCursor


class BancoIndisponivel(Exception):
    pass


@contextmanager
def conexao(config):
    try:
        conn = pymysql.connect(
            host=config['MYSQL_HOST'], port=config['MYSQL_PORT'],
            user=config['MYSQL_USER'], password=config['MYSQL_PASSWORD'],
            database=config['MYSQL_DATABASE'], charset='utf8mb4',
            cursorclass=DictCursor, connect_timeout=4,
            read_timeout=5, write_timeout=5,
            init_command="SET time_zone = '+00:00'",
            autocommit=False,
        )
    except (pymysql.MySQLError, OSError) as exc:
        raise BancoIndisponivel('Conexão indisponível.') from exc
    try:
        yield conn
    except pymysql.MySQLError as exc:
        conn.rollback()
        raise BancoIndisponivel('Operação indisponível.') from exc
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def inicializar(config):
    instrucao = '''
    CREATE TABLE IF NOT EXISTS ocorrencias (
        id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
        regiao VARCHAR(20) NOT NULL,
        tipo VARCHAR(24) NOT NULL,
        intensidade VARCHAR(10) NOT NULL,
        status VARCHAR(12) NOT NULL DEFAULT 'aberto',
        origem VARCHAR(12) NOT NULL DEFAULT 'comunidade',
        criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        atualizado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        INDEX idx_status_criacao (status, criado_em),
        INDEX idx_regiao (regiao)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    '''
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(instrucao)
        conn.commit()


def _formatar(row):
    if row is None:
        return None
    retorno = dict(row)
    for campo in ('criado_em', 'atualizado_em'):
        instante = retorno.get(campo)
        if isinstance(instante, datetime):
            retorno[campo] = instante.replace(tzinfo=timezone.utc).isoformat().replace('+00:00', 'Z')
    return retorno


def listar(config, status=None):
    sql = '''SELECT id, regiao, tipo, intensidade, status, origem, criado_em, atualizado_em
             FROM ocorrencias'''
    parametros = ()
    if status is not None:
        sql += ' WHERE status = %s'
        parametros = (status,)
    sql += ' ORDER BY criado_em DESC, id DESC LIMIT 100'
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, parametros)
            return [_formatar(row) for row in cursor.fetchall()]


def obter(config, identificador):
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute('''SELECT id, regiao, tipo, intensidade, status, origem,
                                     criado_em, atualizado_em
                              FROM ocorrencias WHERE id = %s''', (identificador,))
            return _formatar(cursor.fetchone())


def criar(config, dados, origem='comunidade'):
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute('''INSERT INTO ocorrencias (regiao, tipo, intensidade, status, origem)
                              VALUES (%s, %s, %s, %s, %s)''',
                           (dados['regiao'], dados['tipo'], dados['intensidade'], 'aberto', origem))
            identificador = cursor.lastrowid
        conn.commit()
    return obter(config, identificador)


def atualizar_status(config, identificador, status):
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute('UPDATE ocorrencias SET status = %s WHERE id = %s',
                           (status, identificador))
        conn.commit()
    # PUT é idempotente: atualizar para o status já existente também deve
    # retornar HTTP 200, não 404. Consultar a existência após o UPDATE.
    return obter(config, identificador)


def excluir(config, identificador):
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute('DELETE FROM ocorrencias WHERE id = %s', (identificador,))
            existia = cursor.rowcount > 0
        conn.commit()
    return existia


def resumo(config):
    contagem = {status: 0 for status in ('aberto', 'em_analise', 'resolvido')}
    with conexao(config) as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT status, COUNT(*) AS quantidade FROM ocorrencias GROUP BY status')
            for linha in cursor.fetchall():
                if linha['status'] in contagem:
                    contagem[linha['status']] = linha['quantidade']
    return {'total': sum(contagem.values()), 'por_status': contagem}
