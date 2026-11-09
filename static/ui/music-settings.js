import { api } from './api.js';
import { bindDialog } from './dialog.js';

export function musicSettings(onSaved, onOpen = () => {}) {
  const dialog = document.createElement('dialog');
  dialog.id = 'musicSettings'; dialog.className = 'update-dialog music-settings';
  dialog.innerHTML = `<form id="musicSettingsForm"><h2 id="musicSettingsTitle">Music collections and privacy</h2>
    <p>Choose up to 12 Civitai collections. Each gets a video queue and a creator feed. Removing a feed keeps its collection on Civitai.</p>
    <div id="musicCollectionRows"></div><button type="button" id="musicCollectionAdd">Add collection</button>
    <fieldset><legend>Optional hosted services</legend>
    <label><input type="checkbox" id="musicCommunityEnabled"> Enable hosted Community</label>
    <p>This shares your public Civitai identity with the original author's Community service. Sign in or reconnect Community after enabling. Your Civitai access token is not shared.</p>
    <label><input type="checkbox" id="musicRegistryEnabled"> Share app activity with that service</label>
    <p>Optional activity includes your account identity, app version, platform and last-use time. Requires Community. Turning either option off stops new requests; it does not delete records already held by the service.</p></fieldset>
    <p id="musicSettingsError" role="alert"></p><div class="update-actions"><button type="submit" id="musicSettingsSave">Save settings</button><button type="button" id="musicSettingsCancel">Cancel</button></div></form>`;
  document.body.append(dialog);
  const get = id => dialog.querySelector('#' + id);
  const rows = get('musicCollectionRows');
  bindDialog(dialog, { labelledBy: 'musicSettingsTitle', closeButtons: [get('musicSettingsCancel')] });
  function add(item = {}) {
    if (rows.children.length >= 12) return;
    const row = document.createElement('fieldset'); row.className = 'music-collection-row';
    const input = (label, field, value, max) => {
      const wrap = document.createElement('label'); wrap.textContent = label;
      const control = document.createElement(field === 'comment' ? 'textarea' : 'input');
      control.dataset.field = field; control.value = value || ''; control.maxLength = max;
      if (field !== 'comment') control.required = true;
      wrap.append(control); row.append(wrap);
    };
    input('Collection ID or Civitai link', 'collectionId', String(item.collectionId || ''), 200);
    input('Display name', 'name', item.name, 80);
    input('Optional comment when saving a video (blank means no comment)', 'comment', item.comment, 2000);
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Remove feed';
    remove.addEventListener('click', () => row.remove()); row.append(remove); rows.append(row);
  }
  get('musicCollectionAdd').addEventListener('click', () => add());
  get('musicCommunityEnabled').addEventListener('change', () => {
    if (!get('musicCommunityEnabled').checked) get('musicRegistryEnabled').checked = false;
    get('musicRegistryEnabled').disabled = !get('musicCommunityEnabled').checked;
  });
  function identifier(value) {
    if (/^\d+$/.test(value.trim())) return Number(value.trim());
    const url = new URL(value);
    if (url.protocol !== 'https:' || !['civitai.com', 'civitai.red'].includes(url.hostname) || url.username || url.password || url.port) throw new Error('Use a Civitai collection link or its numeric ID.');
    const match = url.pathname.match(/^\/collections\/(\d+)\/?$/);
    if (!match) throw new Error('Use a Civitai collection link or its numeric ID.');
    return Number(match[1]);
  }
  get('musicSettingsForm').addEventListener('submit', async event => {
    event.preventDefault(); get('musicSettingsSave').disabled = true; get('musicSettingsError').textContent = '';
    try {
      const musicCollections = [...rows.children].map(row => {
        const value = name => row.querySelector(`[data-field="${name}"]`).value;
        return { collectionId: identifier(value('collectionId')), name: value('name'), icon: '♫', comment: value('comment') };
      });
      await api('/api/settings', { method: 'POST', body: JSON.stringify({ musicCollections,
        communityEnabled: get('musicCommunityEnabled').checked, registryEnabled: get('musicRegistryEnabled').checked }) });
      await onSaved(); dialog.close();
    } catch (error) { get('musicSettingsError').textContent = error.message; }
    finally { get('musicSettingsSave').disabled = false; }
  });
  const button = document.createElement('button'); button.type = 'button'; button.id = 'musicSettingsOpen'; button.textContent = 'Collections & privacy';
  button.addEventListener('click', async () => {
    onOpen(); rows.replaceChildren(); get('musicSettingsError').textContent = ''; dialog.showModal();
    get('musicSettingsSave').disabled = true;
    try {
      const settings = await api('/api/settings');
      for (const item of settings.musicCollections || []) add(item);
      get('musicCommunityEnabled').checked = !!settings.communityEnabled;
      get('musicRegistryEnabled').checked = !!settings.registryEnabled;
      get('musicRegistryEnabled').disabled = !settings.communityEnabled;
      get('musicSettingsSave').disabled = false;
    } catch (error) { get('musicSettingsError').textContent = error.message; }
  });
  return button;
}
