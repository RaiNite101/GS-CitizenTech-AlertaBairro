from datetime import datetime
from zoneinfo import ZoneInfo
from unittest.mock import patch
import requests
import pytest
from app.clima import consultar, ClimaIndisponivel


class RespostaFalsa:
    def raise_for_status(self):
        pass

    def json(self):
        return {'hourly': {
            'time': ['2026-11-09T15:00', '2026-11-09T16:00', '2026-11-09T17:00'],
            'precipitation_probability': [10, 70, 40],
            'precipitation': [0.1, 2.2, 1.3],
        }}


class SessaoFalsa:
    def get(self, _url, params=None, timeout=None):
        assert timeout == (3, 8)
        assert params['hourly'] == 'precipitation_probability,precipitation'
        return RespostaFalsa()


def test_api_previsao_json():
    agora = datetime(2026, 11, 9, 16, 0, tzinfo=ZoneInfo('America/Sao_Paulo'))
    dados = consultar(session=SessaoFalsa(), agora=agora)
    assert dados['periodo_horas'] == 2
    assert dados['probabilidade_maxima_chuva_pct'] == 70
    assert dados['precipitacao_prevista_mm'] == 3.5


def test_falha_externa_tratada(client):
    with patch('app.clima.consultar', side_effect=ClimaIndisponivel()):
        resp = client.get('/api/clima')
    assert resp.status_code == 503
    assert resp.json == {'erro': 'Dados meteorológicos indisponíveis.'}


def test_requisicao_externa_falha():
    class Falha:
        def get(self, *args, **kwargs):
            raise requests.Timeout('Sem resposta')
    with pytest.raises(ClimaIndisponivel):
        consultar(session=Falha())
