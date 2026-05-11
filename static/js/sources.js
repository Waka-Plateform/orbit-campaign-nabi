import { api, toast } from './sse.js';

let artifacts = [];
let current = null;

async function loadSources() {
  try {
    const data = await api('/api/console/sources');
    artifacts = data.items || data.sources || [];
    renderTable();
    openFromHash();
  } catch (error) {
    document.getElementById('sources-table-body').innerHTML = `<tr><td colspan="6" class="orbit-error">${escapeHtml(error.message)}</td></tr>`;
  }
}

function renderTable() {
  const body = document.getElementById('sources-table-body');
  if (!artifacts.length) {
    body.innerHTML = '<tr><td colspan="6" class="orbit-empty">Aucune source éditable</td></tr>';
    return;
  }
  body.innerHTML = artifacts.map((item) => `<tr id="source-row-${escapeHtml(item.artifact_id || item.id)}"><td><span class="orbit-badge ${item.mode === 'generated' ? 'info' : ''}">${escapeHtml(item.mode || item.type || 'source')}</span></td><td><i class="bi ${iconFor(item.channel)}" aria-hidden="true"></i> ${escapeHtml(item.channel || '')}</td><td><strong>${escapeHtml(item.label || item.action_id || item.id)}</strong><br><span class="console-muted">${escapeHtml(item.artifact_id || item.id)}</span></td><td><span class="orbit-badge ${item.status === 'ready' ? 'success' : 'warning'}">${escapeHtml(item.status || 'ready')}</span></td><td>${escapeHtml(formatDate(item.updated_at) || item.updated_by || '')}</td><td><div class="orbit-toolbar"><button class="orbit-btn small" type="button" data-source-open="${escapeHtml(item.artifact_id || item.id)}">Ouvrir</button><button class="orbit-btn small" type="button" data-source-test="${escapeHtml(item.artifact_id || item.id)}">Tester</button><button class="orbit-btn small" type="button" data-source-regenerate="${escapeHtml(item.artifact_id || item.id)}">Régénérer IA</button><button class="orbit-btn small" type="button" data-source-history="${escapeHtml(item.artifact_id || item.id)}">Historique</button></div></td></tr>`).join('');
  body.querySelectorAll('[data-source-open]').forEach((button) => button.addEventListener('click', () => openEditor(button.dataset.sourceOpen)));
  body.querySelectorAll('[data-source-test]').forEach((button) => button.addEventListener('click', () => testSource(button.dataset.sourceTest)));
  body.querySelectorAll('[data-source-regenerate]').forEach((button) => button.addEventListener('click', () => openRegenerate(button.dataset.sourceRegenerate)));
  body.querySelectorAll('[data-source-history]').forEach((button) => button.addEventListener('click', () => loadHistory(button.dataset.sourceHistory)));
}

async function openEditor(id) {
  try {
    const data = await api(`/api/console/sources/${encodeURIComponent(id)}`);
    current = { id, ...data };
    document.getElementById('sources-editor-title').textContent = data.label || id;
    document.getElementById('sources-editor-meta').innerHTML = `<span class="orbit-badge">${escapeHtml(data.channel || '')}</span><span class="orbit-badge info">${escapeHtml(data.mode || data.kind || '')}</span>`;
    document.getElementById('sources-editor-content').value = data.content || data.body || data.prompt || '';
    renderPreview();
    openDrawer('sources-editor-drawer');
  } catch (error) { toast(error.message, 'error'); }
}

function renderPreview() {
  const frame = document.getElementById('sources-preview');
  const content = document.getElementById('sources-editor-content').value;
  if ((current?.channel || '').includes('email') || /<html|<body|<p|<div/i.test(content)) frame.srcdoc = content;
  else frame.srcdoc = `<pre>${escapeHtml(content)}</pre>`;
}

async function saveCurrent() {
  if (!current?.id) return;
  try {
    await api(`/api/console/sources/${encodeURIComponent(current.id)}`, { method: 'PATCH', body: JSON.stringify({ content: document.getElementById('sources-editor-content').value }) });
    toast('Source sauvegardée. Les prochains envois utiliseront cette version.');
    await loadSources();
  } catch (error) { toast(error.message, 'error'); }
}

async function testSource(id) {
  try { await api(`/api/console/sources/${encodeURIComponent(id)}/test`, { method: 'POST', body: JSON.stringify({ recipient: 'current_user' }) }); toast('Test envoyé à l’utilisateur courant'); } catch (error) { toast(error.message, 'error'); }
}

function openRegenerate(id) {
  current = { id, ...(artifacts.find((item) => (item.artifact_id || item.id) === id) || {}) };
  openModal('sources-regenerate-modal');
}

async function regenerate() {
  if (!current?.id) return;
  try {
    const payload = { instruction: document.getElementById('sources-regenerate-instruction').value, mode: document.getElementById('sources-regenerate-mode').value };
    const data = await api(`/api/console/sources/${encodeURIComponent(current.id)}/regenerate`, { method: 'POST', body: JSON.stringify(payload) });
    closeModal('sources-regenerate-modal');
    toast('Régénération terminée');
    if (data.content || data.body || data.prompt) {
      await openEditor(current.id);
      document.getElementById('sources-editor-content').value = data.content || data.body || data.prompt;
      renderPreview();
    }
  } catch (error) { toast(error.message, 'error'); }
}

async function loadHistory(id) {
  try {
    const data = await api(`/api/console/sources/${encodeURIComponent(id)}/history`);
    if (!current || current.id !== id) await openEditor(id);
    document.getElementById('sources-history-list').innerHTML = (data.items || data.history || []).map((version) => `<article class="orbit-panel"><strong>${escapeHtml(version.version_id || version.id || 'Version')}</strong><p>${escapeHtml(formatDate(version.updated_at) || '')} · ${escapeHtml(version.updated_by || '')}</p></article>`).join('') || '<div class="orbit-empty">Aucun historique</div>';
  } catch (error) { toast(error.message, 'error'); }
}

function bind() {
  document.getElementById('sources-editor-content')?.addEventListener('input', renderPreview);
  document.getElementById('sources-save')?.addEventListener('click', saveCurrent);
  document.getElementById('sources-test')?.addEventListener('click', () => current?.id && testSource(current.id));
  document.getElementById('sources-regenerate')?.addEventListener('click', () => current?.id && openRegenerate(current.id));
  document.getElementById('sources-history')?.addEventListener('click', () => current?.id && loadHistory(current.id));
  document.getElementById('sources-regenerate-confirm')?.addEventListener('click', regenerate);
  document.querySelectorAll('[data-close-drawer]').forEach((button) => button.addEventListener('click', () => closeDrawer(button.dataset.closeDrawer)));
  document.querySelectorAll('[data-modal-close]').forEach((button) => button.addEventListener('click', () => closeModal(button.dataset.modalClose)));
  window.addEventListener('hashchange', openFromHash);
}

function openFromHash() { const match = location.hash.match(/^#sources:(.+)$/); if (match) openEditor(decodeURIComponent(match[1])); }
function iconFor(channel) { return channel === 'sms' ? 'bi-chat-dots' : channel === 'voice' ? 'bi-telephone' : channel === 'whatsapp' ? 'bi-whatsapp' : 'bi-envelope'; }
function openDrawer(id) { const el = document.getElementById(id); el.classList.add('open'); el.setAttribute('aria-hidden', 'false'); }
function closeDrawer(id) { const el = document.getElementById(id); el.classList.remove('open'); el.setAttribute('aria-hidden', 'true'); }
function openModal(id) { const el = document.getElementById(id); el.classList.add('open'); el.setAttribute('aria-hidden', 'false'); }
function closeModal(id) { const el = document.getElementById(id); el.classList.remove('open'); el.setAttribute('aria-hidden', 'true'); }
function formatDate(value) { return value ? new Date(value).toLocaleString('fr-FR') : ''; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

bind();
loadSources();
