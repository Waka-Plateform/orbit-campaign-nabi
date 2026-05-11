import { api, toast } from './sse.js';

const defaultColumns = ['identity', 'audiences', 'runtime_status', 'communications'];
let state = { page: Number(new URLSearchParams(location.search).get('page') || 1), perPage: 50, total: 0, items: [], sourceFields: [], columns: loadColumns() };

function loadColumns() {
  try { return JSON.parse(localStorage.getItem('orbit.base.columns') || 'null') || defaultColumns; } catch { return defaultColumns; }
}

function saveColumns() { localStorage.setItem('orbit.base.columns', JSON.stringify(state.columns)); }

async function loadBase() {
  const q = document.getElementById('base-search')?.value || '';
  const audience = document.getElementById('base-audience')?.value || '';
  const params = new URLSearchParams({ page: state.page, per_page: state.perPage, q, audience });
  try {
    const data = await api(`/api/console/base?${params.toString()}`);
    state.items = data.items || [];
    state.total = Number(data.total || state.items.length);
    state.page = Number(data.page || state.page);
    state.sourceFields = Array.from(new Set([...(data.source_fields || []), ...state.items.flatMap((item) => Object.keys(item.source_fields || {}))]));
    renderAudienceFilter(data.audiences || []);
    renderTable();
    renderPagination();
    renderColumnsModal();
  } catch (error) {
    document.getElementById('base-table-body').innerHTML = `<tr><td colspan="8" class="orbit-error">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderAudienceFilter(audiences) {
  const select = document.getElementById('base-audience');
  if (!select || select.dataset.ready === 'true') return;
  audiences.forEach((audience) => {
    const option = document.createElement('option');
    option.value = audience.id || audience.label;
    option.textContent = audience.label || audience.id;
    select.appendChild(option);
  });
  select.dataset.ready = 'true';
}

function columnLabel(column) {
  return ({ identity: 'Identité', audiences: 'Audience(s)', runtime_status: 'Suivi', communications: 'Communications' }[column] || column);
}

function renderTable() {
  const head = document.getElementById('base-table-head');
  const body = document.getElementById('base-table-body');
  head.innerHTML = state.columns.map((column) => `<th>${escapeHtml(columnLabel(column))}</th>`).join('');
  if (!state.items.length) {
    body.innerHTML = `<tr><td colspan="${state.columns.length}" class="orbit-empty">Aucun contact</td></tr>`;
    return;
  }
  body.innerHTML = state.items.map((contact) => `<tr>${state.columns.map((column) => `<td>${renderCell(contact, column)}</td>`).join('')}</tr>`).join('');
  document.getElementById('base-count').textContent = `${state.total.toLocaleString('fr-FR')} contacts`;
}

function renderCell(contact, column) {
  if (column === 'identity') {
    const name = contact.full_name || contact.name || contact.source_fields?.['Full Name'] || 'Contact';
    const email = contact.email || contact.source_fields?.['Email Address'] || '';
    const phone = contact.phone || contact.source_fields?.['Phone Number'] || '';
    const initials = name.split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'C';
    return `<div class="console-identity"><span class="console-avatar">${escapeHtml(initials)}</span><span><strong>${escapeHtml(name)}</strong><br><span class="console-muted">${escapeHtml(email || phone)}</span></span></div>`;
  }
  if (column === 'audiences') return (contact.audiences || contact.audience_ids || ['aud_all_prospects']).map((aud) => `<span class="orbit-chip">${escapeHtml(aud)}</span>`).join(' ');
  if (column === 'runtime_status') return `<span class="orbit-badge ${contact.runtime_status === 'failed' ? 'error' : 'info'}">${escapeHtml(contact.runtime_status || contact.status || 'pending')}</span>`;
  if (column === 'communications') return `<div class="console-comms">${(contact.communications || []).map(renderCommunication).join('')}</div>`;
  return escapeHtml(contact[column] ?? contact.source_fields?.[column] ?? '');
}

function renderCommunication(comm) {
  const status = comm.status || 'pending';
  const icon = comm.channel === 'sms' ? 'bi-chat-dots' : comm.direction === 'in' ? 'bi-inbox' : 'bi-envelope';
  const klass = status === 'failed' || status === 'bounce' ? 'failed' : status === 'delivered' || status === 'read' ? 'delivered' : comm.direction === 'in' ? 'inbound' : 'pending';
  return `<button class="console-comm ${klass}" type="button" title="${escapeHtml(comm.preview || status)}"><i class="bi ${icon}" aria-hidden="true"></i></button>`;
}

function renderPagination() {
  const maxPage = Math.max(1, Math.ceil(state.total / state.perPage));
  document.getElementById('base-page-label').textContent = `Page ${state.page} / ${maxPage}`;
  history.replaceState(null, '', `${location.pathname}?page=${state.page}`);
}

function renderColumnsModal() {
  const list = document.getElementById('base-columns-list');
  const all = [...defaultColumns, ...state.sourceFields.filter((field) => !defaultColumns.includes(field))];
  list.innerHTML = all.map((column) => `<label class="orbit-field"><span><input type="checkbox" value="${escapeHtml(column)}" ${state.columns.includes(column) ? 'checked' : ''}> ${escapeHtml(columnLabel(column))}</span></label>`).join('');
  list.querySelectorAll('input').forEach((input) => input.addEventListener('change', () => {
    state.columns = Array.from(list.querySelectorAll('input:checked')).map((item) => item.value);
    if (!state.columns.length) state.columns = defaultColumns;
    saveColumns();
    renderTable();
  }));
}

function bindEvents() {
  document.getElementById('base-filters')?.addEventListener('submit', (event) => { event.preventDefault(); state.page = 1; loadBase(); });
  document.getElementById('base-search')?.addEventListener('input', debounce(() => { state.page = 1; loadBase(); }, 350));
  document.getElementById('base-audience')?.addEventListener('change', () => { state.page = 1; loadBase(); });
  document.getElementById('base-export')?.addEventListener('click', (event) => {
    const q = document.getElementById('base-search').value;
    const audience = document.getElementById('base-audience').value;
    event.currentTarget.href = `/api/console/base/export?${new URLSearchParams({ q, audience }).toString()}`;
  });
  document.getElementById('base-columns-open')?.addEventListener('click', () => openModal('base-columns-modal'));
  document.getElementById('base-columns-reset')?.addEventListener('click', () => { state.columns = defaultColumns; saveColumns(); renderTable(); renderColumnsModal(); });
  document.querySelectorAll('[data-modal-close]').forEach((button) => button.addEventListener('click', () => closeModal(button.dataset.modalClose)));
  document.getElementById('base-first')?.addEventListener('click', () => goPage(1));
  document.getElementById('base-prev')?.addEventListener('click', () => goPage(state.page - 1));
  document.getElementById('base-next')?.addEventListener('click', () => goPage(state.page + 1));
  document.getElementById('base-last')?.addEventListener('click', () => goPage(Math.ceil(state.total / state.perPage)));
  window.addEventListener('keydown', (event) => {
    if (!document.querySelector('[data-console-section="base"]')) return;
    if (event.key === 'ArrowLeft') goPage(state.page - 1);
    if (event.key === 'ArrowRight') goPage(state.page + 1);
    if (event.key === 'Home') goPage(1);
    if (event.key === 'End') goPage(Math.ceil(state.total / state.perPage));
  });
}

function goPage(page) {
  const maxPage = Math.max(1, Math.ceil(state.total / state.perPage));
  state.page = Math.min(maxPage, Math.max(1, page));
  loadBase();
}

function openModal(id) { const modal = document.getElementById(id); modal?.classList.add('open'); modal?.setAttribute('aria-hidden', 'false'); }
function closeModal(id) { const modal = document.getElementById(id); modal?.classList.remove('open'); modal?.setAttribute('aria-hidden', 'true'); }
function debounce(fn, delay) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); }; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

bindEvents();
loadBase().catch((error) => toast(error.message, 'error'));
