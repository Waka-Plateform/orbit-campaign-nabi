import { api, toast } from './sse.js';

const channelVariables = {
  email: ['email_subscription_id', 'email_resource_group', 'email_communication_service_id', 'email_domain', 'email_sender_username', 'email_display_name', 'email_reply_to'],
  sms: ['sms_subscription_id', 'sms_resource_group', 'sms_communication_service_id', 'sms_phone_number', 'sms_phone_number_kind'],
  whatsapp: ['whatsapp_subscription_id', 'whatsapp_resource_group', 'whatsapp_messages_service_id', 'whatsapp_channel_id'],
  voice: ['voice_provider', 'voice_compeak_account_id', 'voice_inbound_number', 'voice_trunk_id', 'voice_kv_credentials_ref'],
  agents: ['agent_text_id', 'agent_voice_id', 'agent_avatar_id'],
};

const cascades = {
  email: [
    { id: 'email_subscription_id', url: () => '/api/channels/email/subscriptions' },
    { id: 'email_resource_group', url: () => `/api/channels/email/resource-groups?subscription_id=${v('email_subscription_id')}` },
    { id: 'email_communication_service_id', url: () => `/api/channels/email/email-services?subscription_id=${v('email_subscription_id')}&resource_group=${v('email_resource_group')}` },
    { id: 'email_domain', url: () => `/api/channels/email/domains?subscription_id=${v('email_subscription_id')}&resource_group=${v('email_resource_group')}&email_service_id=${v('email_communication_service_id')}` },
    { id: 'email_sender_username', url: () => `/api/channels/email/senders?subscription_id=${v('email_subscription_id')}&resource_group=${v('email_resource_group')}&email_service_id=${v('email_communication_service_id')}&domain=${v('email_domain')}` },
  ],
  sms: [
    { id: 'sms_subscription_id', url: () => '/api/channels/sms/subscriptions' },
    { id: 'sms_resource_group', url: () => `/api/channels/sms/resource-groups?subscription_id=${v('sms_subscription_id')}` },
    { id: 'sms_communication_service_id', url: () => `/api/channels/sms/communication-services?subscription_id=${v('sms_subscription_id')}&resource_group=${v('sms_resource_group')}` },
    { id: 'sms_phone_number', url: () => `/api/channels/sms/phone-numbers?subscription_id=${v('sms_subscription_id')}&resource_group=${v('sms_resource_group')}&communication_service_id=${v('sms_communication_service_id')}` },
  ],
  whatsapp: [
    { id: 'whatsapp_subscription_id', url: () => '/api/channels/whatsapp/subscriptions' },
    { id: 'whatsapp_resource_group', url: () => `/api/channels/whatsapp/resource-groups?subscription_id=${v('whatsapp_subscription_id')}` },
    { id: 'whatsapp_messages_service_id', url: () => `/api/channels/whatsapp/messages-services?subscription_id=${v('whatsapp_subscription_id')}&resource_group=${v('whatsapp_resource_group')}` },
    { id: 'whatsapp_channel_id', url: () => `/api/channels/whatsapp/channels?subscription_id=${v('whatsapp_subscription_id')}&resource_group=${v('whatsapp_resource_group')}&messages_service_id=${v('whatsapp_messages_service_id')}` },
  ],
  voice: [
    { id: 'voice_compeak_account_id', url: () => '/api/channels/voice/accounts' },
    { id: 'voice_inbound_number', url: () => `/api/channels/voice/numbers?account_id=${v('voice_compeak_account_id')}` },
    { id: 'voice_trunk_id', url: () => `/api/channels/voice/trunks?account_id=${v('voice_compeak_account_id')}&number=${v('voice_inbound_number')}` },
  ],
  agents: [
    { id: 'agent_text_id', url: () => '/api/channels/agents/text' },
    { id: 'agent_voice_id', url: () => '/api/channels/agents/voice' },
    { id: 'agent_avatar_id', url: () => '/api/channels/agents/avatar' },
  ],
};

let existingConfig = {};
let createTarget = null;

async function boot() {
  validateFields();
  bindTabs();
  bindSaves();
  bindCreate();
  try {
    const data = await api('/api/console/channels');
    existingConfig = data.channels || data || {};
    hydrateExisting();
    await Promise.all(Object.keys(cascades).map((channel) => loadCascade(channel, 0)));
    hydrateExisting();
    updateBadges();
  } catch (error) { toast(`Channels: ${error.message}`, 'error'); }
}

function validateFields() {
  Object.values(channelVariables).flat().forEach((id) => {
    if (!document.getElementById(id)) throw new Error(`Champ UI Channels manquant: ${id}`);
  });
}

function hydrateExisting() {
  Object.entries(channelVariables).forEach(([channel, fields]) => {
    const config = existingConfig[channel]?.config || existingConfig[channel] || {};
    fields.forEach((id) => { const el = document.getElementById(id); if (el && config[id] != null) el.value = config[id]; });
  });
}

async function loadCascade(channel, startIndex) {
  const steps = cascades[channel] || [];
  for (let index = startIndex; index < steps.length; index += 1) {
    const step = steps[index];
    const select = document.getElementById(step.id);
    if (!select) continue;
    if (index > 0 && !dependencyReady(channel, index)) { setOptions(select, []); continue; }
    try {
      const data = await api(step.url());
      setOptions(select, data.items || data.resources || data.agents || data || []);
      const config = existingConfig[channel]?.config || existingConfig[channel] || {};
      if (config[step.id]) select.value = config[step.id];
    } catch (error) { setOptions(select, []); }
  }
}

function dependencyReady(channel, index) {
  return cascades[channel].slice(0, index).every((step) => document.getElementById(step.id)?.value);
}

function setOptions(select, items) {
  const current = select.value;
  select.innerHTML = '<option value="">Sélectionner</option>';
  items.forEach((item) => {
    const option = document.createElement('option');
    option.value = item.id || item.value || item.name || item.phone_number || item.address || String(item);
    option.textContent = item.label || item.display_name || item.name || item.phone_number || item.address || option.value;
    select.appendChild(option);
  });
  if (current) select.value = current;
}

function bindTabs() {
  document.querySelectorAll('[data-channel-tab]').forEach((tab) => tab.addEventListener('click', () => {
    const channel = tab.dataset.channelTab;
    document.querySelectorAll('[data-channel-tab]').forEach((item) => item.setAttribute('aria-selected', String(item === tab)));
    document.querySelectorAll('[data-channel-panel]').forEach((panel) => panel.classList.toggle('console-hidden', panel.dataset.channelPanel !== channel));
  }));
  Object.entries(cascades).forEach(([channel, steps]) => steps.forEach((step, index) => {
    document.getElementById(step.id)?.addEventListener('change', () => loadCascade(channel, index + 1));
  }));
}

function bindSaves() {
  document.querySelectorAll('[data-channel-save]').forEach((button) => button.addEventListener('click', async () => {
    const channel = button.dataset.channelSave;
    const payload = collectPayload(channel);
    try {
      await api(`/api/channels/${channel}/select`, { method: 'POST', body: JSON.stringify(payload) });
      existingConfig[channel] = { config: payload, configured: true };
      updateBadges();
      toast(`${channel} configuré`);
    } catch (error) { toast(error.message, 'error'); }
  }));
}

function collectPayload(channel) {
  return Object.fromEntries(channelVariables[channel].map((id) => [id, document.getElementById(id).value]));
}

function updateBadges() {
  Object.keys(channelVariables).forEach((channel) => {
    const badge = document.getElementById(`${channel}-configured`);
    const config = existingConfig[channel]?.config || existingConfig[channel] || {};
    const configured = channelVariables[channel].some((id) => Boolean(config[id] || document.getElementById(id)?.value));
    badge.textContent = configured ? 'Configuré' : 'Non configuré';
    badge.className = `orbit-badge ${configured ? 'success' : ''}`;
  });
}

function bindCreate() {
  document.querySelectorAll('[data-create-resource]').forEach((button) => button.addEventListener('click', () => {
    createTarget = button.dataset.createResource;
    document.getElementById('channels-create-title').textContent = `Créer ${createTarget}`;
    document.getElementById('channels-create-body').innerHTML = createFields(createTarget);
    openModal('channels-create-modal');
  }));
  document.getElementById('channels-create-confirm')?.addEventListener('click', createResource);
  document.querySelectorAll('[data-modal-close]').forEach((button) => button.addEventListener('click', () => closeModal(button.dataset.modalClose)));
}

function createFields(target) {
  if (target === 'sms_phone_number') return '<label class="orbit-field"><span class="orbit-label">Pays</span><input class="orbit-input" name="country" value="FR"></label><label class="orbit-field"><span class="orbit-label">Type</span><input class="orbit-input" name="number_type" value="local"></label><label class="orbit-field"><span class="orbit-label">Capacités</span><input class="orbit-input" name="capabilities" value="sms_in,sms_out"></label>';
  if (target === 'email_domain') return '<label class="orbit-field"><span class="orbit-label">Domain</span><input class="orbit-input" name="domain"></label><label class="orbit-field"><span class="orbit-label">Mode</span><select class="orbit-select" name="mode"><option value="managed">Azure Managed</option><option value="custom">Custom</option></select></label>';
  return '<label class="orbit-field"><span class="orbit-label">Nom</span><input class="orbit-input" name="name"></label>';
}

async function createResource() {
  const formData = Object.fromEntries(Array.from(document.querySelectorAll('#channels-create-body input, #channels-create-body select')).map((el) => [el.name, el.value]));
  const endpointByTarget = {
    email_domain: '/api/channels/email/domains/create',
    email_sender: '/api/channels/email/senders/create',
    sms_phone_number: '/api/channels/sms/phone-numbers/purchase',
    whatsapp_channel: '/api/channels/whatsapp/channels/register',
    voice_number: '/api/channels/voice/numbers/purchase',
    voice_trunk: '/api/channels/voice/trunks/create',
  };
  try {
    const endpoint = endpointByTarget[createTarget];
    await api(endpoint, { method: 'POST', body: JSON.stringify({ ...formData, ...collectContext(createTarget) }) });
    toast('Ressource créée');
    closeModal('channels-create-modal');
    await loadCascade(channelFromTarget(createTarget), 0);
  } catch (error) { toast(error.message, 'error'); }
}

function collectContext(target) {
  const channel = channelFromTarget(target);
  return collectPayload(channel);
}

function channelFromTarget(target) {
  if (target.startsWith('email')) return 'email';
  if (target.startsWith('sms')) return 'sms';
  if (target.startsWith('whatsapp')) return 'whatsapp';
  return 'voice';
}

function v(id) { return encodeURIComponent(document.getElementById(id)?.value || ''); }
function openModal(id) { const el = document.getElementById(id); el.classList.add('open'); el.setAttribute('aria-hidden', 'false'); }
function closeModal(id) { const el = document.getElementById(id); el.classList.remove('open'); el.setAttribute('aria-hidden', 'true'); }

boot();
