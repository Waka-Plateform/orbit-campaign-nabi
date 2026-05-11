import { api, toast } from './sse.js';

let currentData = null;

async function loadDashboard() {
  const metric = document.getElementById('dashboard-metric').value;
  const period = document.getElementById('dashboard-period').value;
  try {
    currentData = await api(`/api/console/dashboard?${new URLSearchParams({ metric, period }).toString()}`);
    renderKpis(currentData.kpis || currentData.totals || {});
    renderTimeseries(currentData.timeseries || []);
    renderBreakdown('dashboard-channel-breakdown', currentData.breakdowns?.channel || currentData.by_channel || []);
    renderBreakdown('dashboard-step-breakdown', currentData.breakdowns?.step || currentData.by_step || []);
    renderBreakdown('dashboard-audience-breakdown', currentData.breakdowns?.audience || currentData.by_audience || []);
  } catch (error) { toast(`Dashboard: ${error.message}`, 'error'); }
}

function renderKpis(kpis) {
  const defs = [
    ['sent', 'Envois'], ['delivered', 'Délivrés'], ['opens', 'Ouvertures'], ['clicks', 'Clics'], ['bounces', 'Bounces'], ['replies', 'Réponses'],
  ];
  const container = document.getElementById('dashboard-kpis');
  container.innerHTML = defs.map(([key, label]) => {
    const value = Number(kpis[key]?.total ?? kpis[key] ?? 0);
    const rate = kpis[key]?.rate != null ? ` · ${Math.round(Number(kpis[key].rate) * 100)}%` : '';
    return `<article class="console-stat"><span class="console-stat-value">${value.toLocaleString('fr-FR')}</span><span class="console-stat-label">${label}${rate}</span></article>`;
  }).join('');
}

function renderTimeseries(items) {
  const container = document.getElementById('dashboard-timeseries');
  if (!items.length) { container.innerHTML = '<div class="orbit-empty">Aucune série temporelle</div>'; return; }
  const width = 720;
  const height = 260;
  const pad = 32;
  const max = Math.max(...items.map((item) => Number(item.value || item.count || 0)), 1);
  const points = items.map((item, index) => {
    const x = pad + (index / Math.max(1, items.length - 1)) * (width - pad * 2);
    const y = height - pad - (Number(item.value || item.count || 0) / max) * (height - pad * 2);
    return { x, y, item };
  });
  const path = points.map((point, index) => `${index ? 'L' : 'M'} ${point.x} ${point.y}`).join(' ');
  container.innerHTML = `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Série temporelle"><path d="${path}" fill="none" stroke="var(--accent-2)" stroke-width="3"></path>${points.map((point) => `<button data-drilldown="${escapeHtml(point.item.cell || point.item.date || '')}" aria-label="Drill-down"><circle cx="${point.x}" cy="${point.y}" r="5" fill="var(--accent)"></circle></button>`).join('')}</svg>`;
  container.querySelectorAll('[data-drilldown]').forEach((node) => node.addEventListener('click', () => openDrilldown(node.dataset.drilldown)));
}

function renderBreakdown(id, rows) {
  const container = document.getElementById(id);
  if (!rows.length) { container.innerHTML = '<div class="orbit-empty">Aucune donnée</div>'; return; }
  const total = rows.reduce((sum, row) => sum + Number(row.count || row.value || 0), 0) || 1;
  container.innerHTML = rows.map((row) => {
    const count = Number(row.count || row.value || 0);
    const pct = Math.round((count / total) * 100);
    const label = row.label || row.id || row.channel || row.action_id || row.audience_id || 'Segment';
    return `<button class="console-bar-row" type="button" data-drilldown="${escapeHtml(label)}"><span class="console-bar-meta"><span>${escapeHtml(label)}</span><span>${count.toLocaleString('fr-FR')} · ${pct}%</span></span><span class="console-bar-track"><span class="console-bar-fill" style="--value:${pct}%"></span></span></button>`;
  }).join('');
  container.querySelectorAll('[data-drilldown]').forEach((button) => button.addEventListener('click', () => openDrilldown(button.dataset.drilldown)));
}

async function openDrilldown(cell) {
  const drawer = document.getElementById('dashboard-drilldown-drawer');
  const body = document.getElementById('dashboard-drilldown-body');
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
  body.innerHTML = '<div class="orbit-loading">Chargement</div>';
  try {
    const data = await api(`/api/console/dashboard?${new URLSearchParams({ metric: 'drilldown', period: document.getElementById('dashboard-period').value, cell }).toString()}`);
    const items = data.items || data.contacts || [];
    body.innerHTML = items.map((item) => `<article class="orbit-panel"><strong>${escapeHtml(item.full_name || item.name || item.contact_id)}</strong><p>${escapeHtml(item.email || item.phone || '')}</p><a href="#base?q=${encodeURIComponent(item.email || item.phone || item.contact_id || '')}">Voir dans Base</a></article>`).join('') || '<div class="orbit-empty">Aucun contact</div>';
  } catch (error) { body.innerHTML = `<div class="orbit-error">${escapeHtml(error.message)}</div>`; }
}

function bind() {
  document.getElementById('dashboard-filters')?.addEventListener('change', loadDashboard);
  document.querySelectorAll('[data-close-drawer]').forEach((button) => button.addEventListener('click', () => {
    const drawer = document.getElementById(button.dataset.closeDrawer);
    drawer.classList.remove('open');
    drawer.setAttribute('aria-hidden', 'true');
  }));
}

function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

bind();
loadDashboard();
