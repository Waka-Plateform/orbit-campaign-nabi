import { api, toast, subscribe } from './sse.js';

let state = { channel: 'email', folder: 'inbox', q: '', selected: null };

async function loadInbox() {
  state.folder = document.getElementById('inbox-folder').value;
  state.q = document.getElementById('inbox-search').value;
  document.getElementById('inbox-export').href = `/api/console/inbox.csv?channel=${encodeURIComponent(state.channel)}`;
  await Promise.all([loadDirection('in'), loadDirection('out')]);
}

async function loadDirection(direction) {
  const params = new URLSearchParams({ channel: state.channel, direction, folder: state.folder, q: state.q, page: 1 });
  const list = document.getElementById(`inbox-${direction}-list`);
  list.innerHTML = '<div class="orbit-loading">Chargement</div>';
  try {
    const endpoint = state.channel === 'email' ? `/api/console/inbox/email?${params.toString()}` : `/api/console/inbox?${params.toString()}`;
    const data = await api(endpoint);
    const items = data.items || data.messages || [];
    document.getElementById(`inbox-${direction}-count`).textContent = String(data.total || items.length);
    list.innerHTML = items.map(renderMessage).join('') || '<div class="orbit-empty">Aucun message</div>';
    list.querySelectorAll('[data-message-id]').forEach((button) => button.addEventListener('click', () => openMessage(button.dataset.messageId)));
  } catch (error) { list.innerHTML = `<div class="orbit-error">${escapeHtml(error.message)}</div>`; }
}

function renderMessage(message) {
  const title = message.subject || message.from || message.to || message.contact_name || message.id;
  const preview = message.preview || message.body_preview || message.text || '';
  return `<button class="console-message ${message.status === 'unread' ? 'unread' : ''}" type="button" data-message-id="${escapeHtml(message.id || message.message_id)}"><span class="orbit-row-between"><strong>${escapeHtml(title)}</strong><span class="console-muted">${escapeHtml(relative(message.created_at || message.received_at || message.sent_at))}</span></span><span class="console-muted">${escapeHtml(preview).slice(0, 200)}</span><br><span class="orbit-badge">${escapeHtml(message.status || 'read')}</span></button>`;
}

async function openMessage(id) {
  state.selected = id;
  const drawer = document.getElementById('inbox-detail-drawer');
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
  document.getElementById('inbox-detail-title').textContent = 'Chargement';
  document.getElementById('inbox-detail-body').innerHTML = '<div class="orbit-loading">Chargement</div>';
  try {
    const data = await api(`/api/console/inbox/${encodeURIComponent(id)}`);
    document.getElementById('inbox-detail-title').textContent = data.subject || data.from || data.to || id;
    document.getElementById('inbox-detail-body').innerHTML = `<article class="orbit-stack"><p><strong>Canal</strong> ${escapeHtml(data.channel || state.channel)}</p><p><strong>Provider ID</strong> ${escapeHtml(data.provider_message_id || '')}</p><div>${data.html_body || `<pre>${escapeHtml(data.body || data.text || '')}</pre>`}</div></article>`;
    document.getElementById('inbox-reply-body').value = '';
  } catch (error) { document.getElementById('inbox-detail-body').innerHTML = `<div class="orbit-error">${escapeHtml(error.message)}</div>`; }
}

async function reply() {
  if (!state.selected) return;
  const body = document.getElementById('inbox-reply-body').value.trim();
  if (!body || !window.confirm('Envoyer cette réponse via le même sender campagne ?')) return;
  try {
    await api(`/api/console/inbox/${encodeURIComponent(state.selected)}/reply`, { method: 'POST', body: JSON.stringify({ body }) });
    toast('Réponse envoyée');
    await loadInbox();
  } catch (error) { toast(error.message, 'error'); }
}

async function patchSelected(payload) {
  if (!state.selected) return;
  try {
    await api(`/api/console/inbox/${encodeURIComponent(state.selected)}`, { method: 'PATCH', body: JSON.stringify(payload) });
    toast('Interaction mise à jour');
    await loadInbox();
  } catch (error) { toast(error.message, 'error'); }
}

function bind() {
  document.querySelectorAll('[data-inbox-channel]').forEach((tab) => tab.addEventListener('click', () => {
    state.channel = tab.dataset.inboxChannel;
    document.querySelectorAll('[data-inbox-channel]').forEach((item) => item.setAttribute('aria-selected', String(item === tab)));
    loadInbox();
  }));
  document.getElementById('inbox-folder')?.addEventListener('change', loadInbox);
  document.getElementById('inbox-search')?.addEventListener('input', debounce(loadInbox, 350));
  document.getElementById('inbox-reply-send')?.addEventListener('click', reply);
  document.getElementById('inbox-archive')?.addEventListener('click', () => patchSelected({ folder: 'archive', status: 'archived' }));
  document.getElementById('inbox-toggle-read')?.addEventListener('click', () => patchSelected({ toggle_read: true }));
  document.getElementById('inbox-mark-read')?.addEventListener('click', () => patchSelected({ all: true, status: 'read', channel: state.channel }));
  document.querySelectorAll('[data-close-drawer]').forEach((button) => button.addEventListener('click', () => {
    const drawer = document.getElementById(button.dataset.closeDrawer);
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
  }));
  ['sms', 'whatsapp', 'voice', 'webhook'].forEach((channel) => subscribe(`inbox.${channel}.new`, () => { if (state.channel === channel) loadInbox(); else toast(`Nouvelle interaction ${channel}`); }));
}

function relative(value) {
  if (!value) return '';
  const diff = Date.now() - new Date(value).getTime();
  const minutes = Math.max(0, Math.round(diff / 60000));
  if (minutes < 60) return `il y a ${minutes} min`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `il y a ${hours} h`;
  return new Date(value).toLocaleDateString('fr-FR');
}

function debounce(fn, delay) { let timer; return (...args) => { clearTimeout(timer); timer = setTimeout(() => fn(...args), delay); }; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

bind();
loadInbox();
