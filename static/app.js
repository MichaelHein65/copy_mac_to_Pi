const fileInput = document.getElementById('file-input');
const dirInput = document.getElementById('dir-input');
const pickFiles = document.getElementById('pick-files');
const pickDir = document.getElementById('pick-dir');
const fileList = document.getElementById('file-list');
const remoteList = document.getElementById('remote-list');
const remotePath = document.getElementById('remote-path');
const refresh = document.getElementById('refresh');
const currentPath = document.getElementById('current-path');
const start = document.getElementById('start');
const status = document.getElementById('status');
const log = document.getElementById('log');
const mkdirBtn = document.getElementById('mkdir');
const openSettings = document.getElementById('open-settings');
const settings = document.getElementById('settings');
const saveSettings = document.getElementById('save-settings');

let selectedFiles = [];

function renderFiles() {
  fileList.innerHTML = '';
  if (selectedFiles.length === 0) {
    fileList.textContent = 'Keine Dateien ausgewählt.';
    return;
  }
  selectedFiles.forEach((f) => {
    const div = document.createElement('div');
    div.className = 'item';
    div.textContent = f.name;
    fileList.appendChild(div);
  });
}

function setStatus(text) {
  status.textContent = text;
}

function setLog(text) {
  log.textContent = text;
}

async function loadRemote(path) {
  setStatus('Lade Ziel...');
  setLog(`Anfrage: ${path}`);
  const res = await fetch(`/api/remote/list?path=${encodeURIComponent(path)}`);
  const data = await res.json();
  if (!data.ok) {
    setStatus('Fehler');
    setLog(data.error || 'Fehler beim Laden');
    currentPath.textContent = '';
    return;
  }
  remotePath.value = data.path;
  const shown = data.resolved || data.path;
  currentPath.textContent = `Du siehst: ${shown}`;
  remoteList.innerHTML = '';
  data.items.forEach((item) => {
    const div = document.createElement('div');
    div.className = `item ${item.type}`;
    div.textContent = item.name + (item.type === 'dir' ? '/' : '');
    if (item.type === 'dir') {
      div.addEventListener('click', () => {
        const next = data.path.replace(/\/$/, '') + '/' + item.name;
        loadRemote(next);
      });
    }
    remoteList.appendChild(div);
  });
  setStatus('Bereit');
}

pickFiles.addEventListener('click', () => fileInput.click());
pickDir.addEventListener('click', () => dirInput.click());

fileInput.addEventListener('change', (e) => {
  selectedFiles = Array.from(e.target.files || []);
  renderFiles();
});

dirInput.addEventListener('change', (e) => {
  selectedFiles = Array.from(e.target.files || []);
  renderFiles();
});

refresh.addEventListener('click', () => loadRemote(remotePath.value));

mkdirBtn.addEventListener('click', async () => {
  const path = remotePath.value.trim();
  if (!path) return;
  setStatus('Lege Ordner an...');
  const res = await fetch('/api/mkdir', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  const data = await res.json();
  if (!data.ok) {
    setStatus('Fehler');
    setLog(data.error || 'Fehler beim Anlegen');
    return;
  }
  setStatus('Ordner angelegt');
  loadRemote(path);
});

start.addEventListener('click', async () => {
  if (selectedFiles.length === 0) {
    setStatus('Bitte Dateien auswählen');
    return;
  }
  const target = remotePath.value.trim();
  if (!target) {
    setStatus('Ziel fehlt');
    return;
  }

  const form = new FormData();
  selectedFiles.forEach((f) => form.append('files', f));
  form.append('remote_path', target);

  setStatus('Kopiere...');
  setLog('');
  const res = await fetch('/api/upload', { method: 'POST', body: form });
  const data = await res.json();
  if (!data.ok) {
    setStatus('Fehler');
    setLog(data.error || 'Fehler beim Kopieren');
    return;
  }
  setStatus('Fertig');
  setLog(data.results?.map(r => r.output).join('\n') || '');
});

openSettings.addEventListener('click', () => settings.showModal());

saveSettings.addEventListener('click', async (e) => {
  e.preventDefault();
  const payload = {
    ssh_host: document.getElementById('ssh-host').value.trim(),
    ssh_port: parseInt(document.getElementById('ssh-port').value, 10) || 22,
    remote_base: document.getElementById('remote-base').value.trim()
  };
  const res = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  if (data.ok) {
    settings.close();
    remotePath.value = data.config.remote_base;
    loadRemote(remotePath.value);
  } else {
    setLog(data.error || 'Fehler beim Speichern');
  }
});

loadRemote(remotePath.value);
renderFiles();
