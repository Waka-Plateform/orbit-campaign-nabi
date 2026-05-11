const listeners = new Map();

export function toast(message, type = 'success') {
  const region = document.getElementById('orbit-toast-region') || createToastRegion();
  const item = document.createElement('div');
  item.className = `orbit-toast ${type}`;
  item.textContent = message;
  region.appendChild(item);
  window.setTimeout(() => item.remove(), 4200);
}

function createToastRegion() {
  const region = document.createElement('div');
  region.id = 'orbit-toast-region';
  region.className = 'orbit-toast-region';
  region.setAttribute('aria-live', 'polite');
  document.body.appendChild(region);
  return region;
}

export function subscribe(topic, handler) {
  if (!listeners.has(topic)) listeners.set(topic, new Set());
  listeners.get(topic).add(handler);
  return () => listeners.get(topic)?.delete(handler);
}

function emit(topic, payload) {
  listeners.get(topic)?.forEach((handler) => handler(payload));
}

export async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    credentials: 'same-origin',
    ...options,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }
  const contentType = response.headers.get('content-type') || '';
  return contentType.includes('application/json') ? response.json() : response.text();
}

function startSse() {
  if (!('EventSource' in window)) return;
  const source = new EventSource('/events');
  source.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data);
      if (payload.topic) emit(payload.topic, payload);
      if (payload.type) emit(payload.type, payload);
    } catch (error) {
      emit('events.raw', { data: event.data });
    }
  };
  source.addEventListener('error', () => emit('events.error', {}));
}

function statusClass(status) {
  if (status === 'running') return 'success';
  if (status === 'paused' || status === 'scheduled') return 'warning';
  if (status === 'error') return 'error';
  return 'info';
}

function renderBars(container, rows = [], total = 0) {
  container.innerHTML = '';
  if (!rows.length) {
    container.innerHTML = '<div class="orbit-empty">Aucune donnée disponible</div>';
    return;
  }
  rows.forEach((row) => {
    const count = Number(row.count || row.value || 0);
    const pct = total ? Math.round((count / total) * 100) : Number(row.percent || 0);
    const item = document.createElement('div');
    item.className = 'console-bar-row';
    item.innerHTML = `<div class="console-bar-meta"><span>${escapeHtml(row.label || row.id || 'Segment')}</span><span>${count} · ${pct}%</span></div><div class="console-bar-track"><div class="console-bar-fill" style="--value:${Math.min(100, pct)}%"></div></div>`;
    container.appendChild(item);
  });
}

function renderMetrics(metrics = []) {
  const container = document.getElementById('main-metrics');
  if (!container) return;
  container.innerHTML = '';
  metrics.forEach((metric) => {
    const current = Number(metric.current_value || metric.current || 0);
    const targetRaw = String(metric.target || '100%');
    const target = Number(targetRaw.replace('%', '')) || 100;
    const pct = Math.min(100, Math.round((current / target) * 100));
    const card = document.createElement('article');
    card.className = 'orbit-panel orbit-stack';
    card.innerHTML = `<h3>${escapeHtml(metric.label || metric.id)}</h3><div class="orbit-progress" aria-label="Progression ${pct}%"><span style="--value:${pct}%"></span></div><p><strong>${current}</strong> / ${escapeHtml(targetRaw)}</p><p class="console-muted">${escapeHtml(metric.window || 'Fenêtre campagne')}</p>`;
    container.appendChild(card);
  });
}

async function loadMain() {
  if (!document.querySelector('[data-console-section="main"]')) return;
  try {
    const data = await api('/api/console/main');
    document.getElementById('main-campaign-name').textContent = data.name || 'nabi';
    document.getElementById('main-objective').textContent = data.objective || data.tagline || '';
    document.getElementById('main-owner').textContent = data.owner || data.owner_id || 'Orbit';
    document.getElementById('main-go-live').textContent = data.go_live_at ? `Go-live ${new Date(data.go_live_at).toLocaleString()}` : 'Go-live non planifié';
    const status = document.getElementById('main-status');
    const runtimeStatus = data.runtime_status || data.status || 'scheduled';
    status.className = `orbit-badge ${statusClass(runtimeStatus)}`;
    status.innerHTML = `<i class="bi bi-activity" aria-hidden="true"></i> ${runtimeStatus}`;
    const contacts = Number(data.contacts_count || data.base_summary?.total || 3484);
    document.getElementById('main-contact-count').textContent = contacts.toLocaleString('fr-FR');
    renderBars(document.getElementById('main-audience-bars'), data.audience_breakdown || data.base_summary?.audiences || [{ label: 'Toute la base prospects', count: contacts }], contacts);
    const legend = document.getElementById('main-source-legend');
    const sources = data.source_breakdown || data.base_summary?.sources || [{ label: 'Upload', count: contacts }];
    legend.innerHTML = sources.map((row) => `<span class="orbit-chip">${escapeHtml(row.label || row.source || 'Source')} · ${Number(row.count || 0).toLocaleString('fr-FR')}</span>`).join('');
    const version = data.flow_version || Date.now();
    document.getElementById('main-flow-version').textContent = `Version ${version}`;
    document.getElementById('main-flow-object').data = `/api/console/flow.svg?mode=runtime&v=${encodeURIComponent(version)}`;
    renderMetrics(data.success_metrics || data.metrics || []);
  } catch (error) {
    toast(`Main: ${error.message}`, 'error');
  }
}

function bindMainActions() {
  document.querySelectorAll('[data-main-action]').forEach((button) => {
    button.addEventListener('click', async () => {
      const action = button.dataset.mainAction;
      if (!window.confirm(`Confirmer l’action ${action} sur la campagne ?`)) return;
      try {
        await api(`/api/console/main/${action}`, { method: 'POST', body: JSON.stringify({ action }) });
        toast('Cycle de vie mis à jour');
        await loadMain();
      } catch (error) {
        toast(error.message, 'error');
      }
    });
  });
}

function bindDrawers() {
  document.querySelectorAll('[data-close-drawer]').forEach((button) => {
    button.addEventListener('click', () => {
      const drawer = document.getElementById(button.dataset.closeDrawer);
      drawer?.classList.remove('open');
      drawer?.setAttribute('aria-hidden', 'true');
    });
  });
  const object = document.getElementById('main-flow-object');
  object?.addEventListener('load', () => {
    const svgDoc = object.contentDocument;
    svgDoc?.addEventListener('click', (event) => {
      const node = event.target.closest('[data-node-id], [id]');
      const nodeId = node?.dataset?.nodeId || node?.id;
      if (!nodeId) return;
      const drawer = document.getElementById('main-flow-drawer');
      document.getElementById('main-flow-drawer-title').textContent = `Nœud ${nodeId}`;
      document.getElementById('main-flow-drawer-body').innerHTML = `<p>Ouvrir la source liée à ce nœud dans la section Sources.</p><a class="orbit-btn primary" href="#sources:${encodeURIComponent(nodeId)}">Voir la source</a>`;
      drawer.classList.add('open');
      drawer.setAttribute('aria-hidden', 'false');
    });
  });
}

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char]));
}

bindDrawers();
bindMainActions();
loadMain();
startSse();
