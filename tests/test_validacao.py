import pytest
from app.validacao import EntradaInvalida, validar_ocorrencia, validar_atualizacao, validar_id, validar_filtro_status


@pytest.mark.parametrize('entrada', [
    {'regiao': 'centro', 'tipo': 'alagamento', 'intensidade': 'baixa', 'nome': 'Pessoa'},
    {'regiao': 'centro', 'tipo': "' OR 1=1 --", 'intensidade': 'baixa'},
    {'regiao': '<script>', 'tipo': 'alagamento', 'intensidade': 'baixa'},
    {'regiao': 'centro', 'tipo': 'alagamento'},
    ['centro', 'alagamento', 'alta'],
])
def test_rejeita_campos_indevidos(entrada):
    with pytest.raises(EntradaInvalida):
        validar_ocorrencia(entrada)


def test_aceita_ocorrencia_valida():
    dado = {'regiao': 'zona_sul', 'tipo': 'bueiro_obstruido', 'intensidade': 'alta'}
    assert validar_ocorrencia(dado) == dado


def test_nao_permite_status_no_cadastro():
    with pytest.raises(EntradaInvalida):
        validar_ocorrencia({'regiao': 'centro', 'tipo': 'alagamento', 'intensidade': 'alta', 'status': 'resolvido'})


def test_status_permitidos():
    assert validar_atualizacao({'status': 'resolvido'}) == 'resolvido'
    with pytest.raises(EntradaInvalida):
        validar_atualizacao({'status': 'apagado'})


def test_identificador():
    assert validar_id(5) == 5
    with pytest.raises(EntradaInvalida):
        validar_id(0)


def test_filtro():
    assert validar_filtro_status(None) is None
    with pytest.raises(EntradaInvalida):
        validar_filtro_status('invalido')
