"""Limite simples de cadastros por IP em memória, sem persistência nem logs de IP."""
from collections import defaultdict, deque
from threading import Lock
from time import monotonic


class Limitador:
    def __init__(self, limite=5, janela=60):
        self.limite = limite
        self.janela = janela
        self.historico = defaultdict(deque)
        self.lock = Lock()

    def permitir(self, chave):
        instante = monotonic()
        with self.lock:
            fila = self.historico[chave]
            while fila and fila[0] <= instante - self.janela:
                fila.popleft()
            if len(fila) >= self.limite:
                return False
            fila.append(instante)
            return True
