"""Consulta apenas leitura da Open-Meteo; previsão de chuva não mede risco de inundação."""
from datetime import datetime
from zoneinfo import ZoneInfo
import requests

URL = 'https://api.open-meteo.com/v1/forecast'
LOCALIDADE = 'São Paulo (referência central)'
LATITUDE = -23.5505
LONGITUDE = -46.6333
FUSO = 'America/Sao_Paulo'


class ClimaIndisponivel(Exception):
    pass


def consultar(session=None, agora=None):
    requisitante = session if session is not None else requests
    agora = agora if agora is not None else datetime.now(ZoneInfo(FUSO))
    parametros = {
        'latitude': LATITUDE, 'longitude': LONGITUDE,
        'hourly': 'precipitation_probability,precipitation',
        'forecast_days': 2, 'timezone': FUSO,
    }
    try:
        resposta = requisitante.get(URL, params=parametros, timeout=(3, 8))
        resposta.raise_for_status()
        payload = resposta.json()
        hourly = payload['hourly']
        tempos = hourly['time']
        probabilidades = hourly['precipitation_probability']
        precipitacoes = hourly['precipitation']
        if not (len(tempos) == len(probabilidades) == len(precipitacoes)):
            raise ValueError('Séries incompatíveis')
        registros = []
        for tempo, prob, mm in zip(tempos, probabilidades, precipitacoes):
            data = datetime.fromisoformat(tempo)
            if data >= agora.replace(tzinfo=None):
                registros.append({'hora': tempo, 'probabilidade': prob, 'precipitacao_mm': mm})
                if len(registros) == 24:
                    break
        if not registros:
            raise ValueError('Sem horas futuras')
        max_prob = max((p['probabilidade'] for p in registros if isinstance(p['probabilidade'], (int, float))), default=None)
        mm_total = round(sum(p['precipitacao_mm'] or 0 for p in registros), 1)
        return {
            'localidade': LOCALIDADE,
            'fonte': 'Open-Meteo',
            'consultado_em': agora.isoformat(timespec='seconds'),
            'periodo_horas': len(registros),
            'probabilidade_maxima_chuva_pct': max_prob,
            'precipitacao_prevista_mm': mm_total,
            'horas': registros,
            'aviso': 'Previsão meteorológica, não é alerta oficial de alagamento.',
        }
    except (requests.RequestException, ValueError, KeyError, TypeError, IndexError) as exc:
        raise ClimaIndisponivel('Previsão temporariamente indisponível.') from exc
