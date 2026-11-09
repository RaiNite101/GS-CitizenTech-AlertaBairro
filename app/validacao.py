"""Validação centralizada: dados estruturados, mínimos e sem identificação pessoal."""

REGIOES = ('centro', 'zona_norte', 'zona_sul', 'zona_leste', 'zona_oeste')
TIPOS = ('alagamento', 'bueiro_obstruido', 'via_intransitavel')
INTENSIDADES = ('baixa', 'moderada', 'alta')
STATUS = ('aberto', 'em_analise', 'resolvido')


class EntradaInvalida(ValueError):
    pass


def validar_ocorrencia(dados):
    if not isinstance(dados, dict):
        raise EntradaInvalida('Envie um objeto JSON válido.')
    esperados = {'regiao', 'tipo', 'intensidade'}
    if set(dados) != esperados:
        raise EntradaInvalida('Envie somente regiao, tipo e intensidade.')
    limites = {'regiao': REGIOES, 'tipo': TIPOS, 'intensidade': INTENSIDADES}
    for campo, valores in limites.items():
        if not isinstance(dados[campo], str) or dados[campo] not in valores:
            raise EntradaInvalida(f'Valor inválido para {campo}.')
    return {campo: dados[campo] for campo in ('regiao', 'tipo', 'intensidade')}


def validar_atualizacao(dados):
    if not isinstance(dados, dict) or set(dados) != {'status'}:
        raise EntradaInvalida('Envie somente o campo status.')
    if not isinstance(dados['status'], str) or dados['status'] not in STATUS:
        raise EntradaInvalida('Status inválido.')
    return dados['status']


def validar_id(valor):
    try:
        numero = int(valor)
    except (TypeError, ValueError) as exc:
        raise EntradaInvalida('Identificador inválido.') from exc
    if numero <= 0 or numero > 4294967295:
        raise EntradaInvalida('Identificador inválido.')
    return numero


def validar_filtro_status(valor):
    if valor is None:
        return None
    if valor not in STATUS:
        raise EntradaInvalida('Filtro status inválido.')
    return valor
