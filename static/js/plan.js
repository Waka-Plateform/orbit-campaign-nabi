import { api, toast, subscribe } from './sse.js';

let plan = { allowed_windows: [] };

async function loadPlan() {
  try {
    plan = await api('/api/console/plan');
    hydrateForm(plan);
    renderWindows(plan.allowed_windows || []);
    renderRuntime(plan);
    renderTimeline(plan.occurrences || plan.timeline || []);
  } catch (error) {
    toast(`Plan: ${error.message}`, 'error');
  }
}

function hydrateForm(data) {
  setValue('start_at', toLocal(data.start_at));
  setValue('end_at', toLocal(data.end_at));
  setValue('timezone', data.timezone || 'Europe/Paris');
  setValue('batch_size', data.batch_size || 50);
  setValue('max_per_minute', data.throttle?.max_per_minute || data.max_per_minute || 0);
  setValue('max_per_hour', data.throttle?.max_per_hour || data.max_per_hour || 0);
  setValue('max_per_day', data.throttle?.max_per_day || data.max_per_day || 0);
}

function renderRuntime(data) {
  const status = data.runtime_status || data.status || 'scheduled';
  const badge = document.getElementById('plan-runtime-status');
  badge.textContent = status;
  badge.className = `orbit-badge ${status === 'running' ? 'success' : status === 'error' ? 'error' : 'info'}`;
  document.getElementById('plan-deferred-count').textContent = Number(data.deferred_count || data.counters?.deferred || 0).toLocaleString('fr-FR');
  document.getElementById('plan-throttled-count').textContent = Number(data.throttled_count || data.counters?.throttled || 0).toLocaleString('fr-FR');
  document.getElementById('plan-next-run').textContent = data.next_run_at ? new Date(data.next_run_at).toLocaleString('fr-FR') : '—';
}

function renderWindows(windows) {
  const container = document.getElementById('plan-windows');
  container.innerHTML = '';
  if (!windows.length) windows.push({ days: ['1', '2', '3', '4', '5'], start_hour: '09:00', end_hour: '19:00' });
  windows.forEach((windowDef, index) => {
    const row = document.createElement('div');
    row.className = 'console-window-row';
    row.innerHTML = `<label class="orbit-field"><span class="orbit-label">Jours</span><input class="orbit-input" data-window-field="days" data-index="${index}" value="${escapeHtml((windowDef.days || []).join(','))}" placeholder="1,2,3,4,5"></label><label class="orbit-field"><span class="orbit-label">Début</span><input class="orbit-input" data-window-field="start_hour" data-index="${index}" value="${escapeHtml(windowDef.start_hour || '09:00')}" placeholder="09:00"></label><label class="orbit-field"><span class="orbit-label">Fin</span><input class="orbit-input" data-window-field="end_hour" data-index="${index}" value="${escapeHtml(windowDef.end_hour || '19:00')}" placeholder="19:00"></label><button class="orbit-btn danger" type="button" data-remove-window="${index}">Supprimer</button>`;
    container.appendChild(row);
  });
  container.querySelectorAll('[data-remove-window]').forEach((button) => button.addEventListener('click', () => {
    plan.allowed_windows.splice(Number(button.dataset.removeWindow), 1);
    renderWindows(plan.allowed_windows);
  }));
}

function collectPlan() {
  return {
    start_at: fromLocal(getValue('start_at')),
    end_at: fromLocal(getValue('end_at')),
    timezone: getValue('timezone'),
    batch_size: Number(getValue('batch_size') || 0),
    throttle: {
      max_per_minute: Number(getValue('max_per_minute') || 0),
      max_per_hour: Number(getValue('max_per_hour') || 0),
      max_per_day: Number(getValue('max_per_day') || 0),
    },
    allowed_windows: Array.from(document.querySelectorAll('.console-window-row')).map((row) => ({
      days: row.querySelector('[data-window-field="days"]').value.split(',').map((item) => item.trim()).filter(Boolean),
      start_hour: row.querySelector('[data-window-field="start_hour"]').value,
      end_hour: row.querySelector('[data-window-field="end_hour"]').value,
    })),
  };
}

function renderTimeline(items) {
  const container = document.getElementById('plan-timeline');
  if (!items.length) {
    container.innerHTML = '<div class="orbit-empty">Aucune occurrence calculée pour le moment</div>';
    return;
  }
  container.innerHTML = items.map((item) => `<article class="console-rule-row"><strong>${escapeHtml(item.label || item.action_id || 'Envoi')}</strong><span>${escapeHtml(item.channel || '')} · ${escapeHtml(item.audience || item.audience_id || 'audience')}</span><span>${item.run_at ? new Date(item.run_at).toLocaleString('fr-FR') : escapeHtml(item.next_occurrence || '')}</span><a href="#sources:${encodeURIComponent(item.action_id || '')}">Source</a></article>`).join('');
}

function bind() {
  document.getElementById('plan-add-window')?.addEventListener('click', () => {
    plan.allowed_windows = collectPlan().allowed_windows;
    plan.allowed_windows.push({ days: ['1', '2', '3', '4', '5'], start_hour: '09:00', end_hour: '19:00' });
    renderWindows(plan.allowed_windows);
  });
  document.getElementById('plan-form')?.addEventListener('submit', async (event) => {
    event.preventDefault();
    try {
      await api('/api/console/plan', { method: 'POST', body: JSON.stringify(collectPlan()) });
      toast('Plan enregistré');
      await loadPlan();
    } catch (error) { toast(error.message, 'error'); }
  });
  document.querySelectorAll('[data-plan-action]').forEach((button) => button.addEventListener('click', async () => {
    const action = button.dataset.planAction;
    if (!window.confirm(`Confirmer ${action} ?`)) return;
    try {
      await api(`/api/console/plan/${action}`, { method: 'POST', body: JSON.stringify({ action }) });
      toast('Action appliquée');
      await loadPlan();
    } catch (error) { toast(error.message, 'error'); }
  }));
  subscribe('plan.updated', loadPlan);
  subscribe('scheduler.tick', loadPlan);
}

function setValue(id, value) { const el = document.getElementById(id); if (el) el.value = value || ''; }
function getValue(id) { return document.getElementById(id)?.value || ''; }
function toLocal(value) { if (!value) return ''; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : date.toISOString().slice(0, 16); }
function fromLocal(value) { return value ? new Date(value).toISOString() : null; }
function escapeHtml(value) { return String(value ?? '').replace(/[&<>'"]/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[char])); }

bind();
loadPlan();
