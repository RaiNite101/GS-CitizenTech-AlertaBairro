"""Módulo de redes: socket TCP local somente-leitura para resumo de ocorrências.

Protocolo: cliente envia STATUS\n; servidor devolve uma linha JSON UTF-8.
Não há acesso pela rede externa (bind em 127.0.0.1).
"""
import json
import socketserver
from . import db
from .config import Config


class Handler(socketserver.StreamRequestHandler):
    def handle(self):
        self.request.settimeout(4)
        comando = self.rfile.readline(32).strip()
        if comando != b'STATUS':
            resposta = {'erro': 'Comando inválido.'}
        else:
            try:
                config = {
                    'MYSQL_HOST': Config.MYSQL_HOST, 'MYSQL_PORT': Config.MYSQL_PORT,
                    'MYSQL_USER': Config.MYSQL_USER, 'MYSQL_PASSWORD': Config.MYSQL_PASSWORD,
                    'MYSQL_DATABASE': Config.MYSQL_DATABASE,
                }
                resposta = {'servico': 'AlertaBairro', **db.resumo(config)}
            except db.BancoIndisponivel:
                resposta = {'erro': 'Banco indisponível.'}
        self.wfile.write((json.dumps(resposta, ensure_ascii=False) + '\n').encode('utf-8'))


class Servidor(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main():
    with Servidor(('127.0.0.1', 9099), Handler) as servidor:
        print('TCP local ativo em 127.0.0.1:9099 (comando STATUS)')
        try:
            servidor.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            print('\nEncerrado.')


if __name__ == '__main__':
    main()
