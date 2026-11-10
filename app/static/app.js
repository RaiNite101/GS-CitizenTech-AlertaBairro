'use strict';

const $ = (id) => document.getElementById(id);
const regioes = {centro: 'Centro', zona_norte: 'Zona Norte', zona_sul: 'Zona Sul', zona_leste: 'Zona Leste', zona_oeste: 'Zona Oeste'};
const tipos = {alagamento: 'Alagamento', bueiro_obstruido: 'Bueiro obstruído', via_intransitavel: 'Via prejudicada'};
const situacoes = {aberto: 'Em aberto', em_analise: 'Em análise', resolvido: 'Resolvido'};
const niveis = {baixa: 'Baixa', moderada: 'Moderada', alta: 'Alta'};

async function api(url, options = {}) {
  const resposta = await fetch(url, {cache: 'no-store', ...options});
  if (resposta.status === 204) return null;
  let dados;
  try { dados = await resposta.json(); }
  catch { throw new Error('Resposta inválida do servidor.'); }
  if (!resposta.ok) throw new Error(dados.erro || `Erro ${resposta.status}`);
  return dados;
}

function informar(id, mensagem, tipo = '') {
  const div = $(id);
  div.textContent = mensagem;
  div.className = `feedback ${tipo}`;
}

function elemento(tag, texto = '', classe = '') {
  const el = document.createElement(tag);
  el.textContent = texto;  // Sem innerHTML de dados externos ou enviados por usuário.
  if (classe) el.className = classe;
  return el;
}

function formatoData(data) {
  const d = new Date(data);
  return Number.isNaN(d.getTime()) ? 'Data indisponível' : d.toLocaleString('pt-BR', {dateStyle: 'short', timeStyle: 'short'});
}

function cabecalhoAdmin() {
  return {'Content-Type': 'application/json', 'X-Admin-Key': $('admin-key').value};
}

function montarRelato(item) {
  const card = elemento('article', '', 'incident');
  if (item.origem === 'demo') card.dataset.demo = 'true';
  const texto = elemento('div');
  texto.append(elemento('h3', tipos[item.tipo] || 'Ocorrência'));
  const meta = elemento('div', '', 'incident-meta');
  meta.append(elemento('span', regioes[item.regiao] || 'Região desconhecida'));
  meta.append(elemento('span', `Intensidade: ${niveis[item.intensidade] || '—'}`));
  meta.append(elemento('span', formatoData(item.criado_em)));
  texto.append(meta);
  if (item.origem === 'demo') texto.append(elemento('span', 'DADO FICTÍCIO DE DEMONSTRAÇÃO', 'demo'));
  card.append(texto, elemento('span', situacoes[item.status] || '—', `pill ${item.status}`));

  const controles = elemento('div', '', 'incident-controls');
  const select = elemento('select');
  select.setAttribute('aria-label', `Nova situação para ocorrência ${item.id}`);
  for (const [valor, rotulo] of Object.entries(situacoes)) {
    const option = elemento('option', rotulo);
    option.value = valor;
    select.append(option);
  }
  select.value = item.status;
  const salvar = elemento('button', 'Salvar situação', 'small-btn');
  salvar.type = 'button';
  salvar.addEventListener('click', async () => {
    if (!$('admin-key').value) return informar('mensagem-lista', 'Informe a chave administrativa no final da página.', 'error');
    salvar.disabled = true;
    try {
      await api(`/api/ocorrencias/${item.id}`, {method: 'PUT', headers: cabecalhoAdmin(), body: JSON.stringify({status: select.value})});
      informar('mensagem-lista', 'Situação atualizada.', 'success');
      await atualizarDados();
    } catch (erro) { informar('mensagem-lista', erro.message, 'error'); }
    finally { salvar.disabled = false; }
  });
  const apagar = elemento('button', 'Excluir', 'small-btn delete');
  apagar.type = 'button';
  apagar.addEventListener('click', async () => {
    if (!$('admin-key').value) return informar('mensagem-lista', 'Informe a chave administrativa no final da página.', 'error');
    if (!window.confirm('Confirma a exclusão definitiva deste registro?')) return;
    apagar.disabled = true;
    try {
      await api(`/api/ocorrencias/${item.id}`, {method: 'DELETE', headers: {'X-Admin-Key': $('admin-key').value}});
      informar('mensagem-lista', 'Registro excluído.', 'success');
      await atualizarDados();
    } catch (erro) { informar('mensagem-lista', erro.message, 'error'); }
    finally { apagar.disabled = false; }
  });
  controles.append(select, salvar, apagar);
  card.append(controles);
  return card;
}

async function carregarOcorrencias() {
  try {
    const status = $('filtro').value;
    const url = status ? `/api/ocorrencias?status=${encodeURIComponent(status)}` : '/api/ocorrencias';
    const dados = await api(url);
    const lista = $('lista');
    lista.replaceChildren();
    if (!dados.ocorrencias.length) {
      lista.append(elemento('p', 'Nenhum relato encontrado para este filtro.', 'empty-state'));
    } else {
      dados.ocorrencias.forEach(item => lista.append(montarRelato(item)));
    }
  } catch (erro) {
    $('lista').replaceChildren(elemento('p', 'Não foi possível carregar os registros.', 'empty-state'));
    informar('mensagem-lista', erro.message, 'error');
  }
}

async function carregarResumo() {
  try {
    const dado = await api('/api/resumo');
    $('total').textContent = dado.total;
    $('abertos').textContent = dado.por_status.aberto;
    $('resolvidos').textContent = dado.por_status.resolvido;
  } catch {
    ['total', 'abertos', 'resolvidos'].forEach(id => $(id).textContent = '—');
  }
}

async function carregarClima() {
  try {
    const dado = await api('/api/clima');
    $('chuva-mm').textContent = dado.precipitacao_prevista_mm.toLocaleString('pt-BR');
    $('chuva-prob').textContent = dado.probabilidade_maxima_chuva_pct === null ? 'Indisponível' : `${dado.probabilidade_maxima_chuva_pct}%`;
    $('clima-atualizado').textContent = `Dados Open-Meteo • consulta ${formatoData(dado.consultado_em)}`;
  } catch {
    $('chuva-mm').textContent = '—';
    $('chuva-prob').textContent = '—';
    $('clima-atualizado').textContent = 'Não foi possível consultar a previsão agora.';
  }
}

async function atualizarDados() {
  await Promise.all([carregarOcorrencias(), carregarResumo()]);
}

$('form-ocorrencia').addEventListener('submit', async (evento) => {
  evento.preventDefault();
  const formulario = $('form-ocorrencia');
  if (!formulario.reportValidity()) return;
  const payload = {
    regiao: $('regiao').value,
    tipo: $('tipo').value,
    intensidade: $('intensidade').value,
  };
  $('enviar').disabled = true;
  try {
    await api('/api/ocorrencias', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
    formulario.reset();
    $('filtro').value = '';
    informar('mensagem-form', 'Relato registrado! Ele ainda não foi verificado.', 'success');
    await atualizarDados();
  } catch (erro) { informar('mensagem-form', erro.message, 'error'); }
  finally { $('enviar').disabled = false; }
});
$('atualizar').addEventListener('click', atualizarDados);
$('filtro').addEventListener('change', carregarOcorrencias);
Promise.all([atualizarDados(), carregarClima()]);

// Atalhos visuais para os filtros, mantendo a API e o seletor originais.
const filtrosRapidos = document.querySelectorAll('.filter-chip');
function sincronizarFiltros() {
  const atual = $('filtro').value;
  filtrosRapidos.forEach(botao => {
    const ativo = botao.dataset.status === atual;
    botao.classList.toggle('active', ativo);
    botao.setAttribute('aria-pressed', String(ativo));
  });
}
filtrosRapidos.forEach(botao => botao.addEventListener('click', () => {
  $('filtro').value = botao.dataset.status;
  sincronizarFiltros();
  carregarOcorrencias();
}));
$('filtro').addEventListener('change', sincronizarFiltros);
sincronizarFiltros();
