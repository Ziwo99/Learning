let cm = null;

function initEditor(mode) {
  const textarea = document.getElementById('code-editor');
  if (typeof CodeMirror !== 'undefined' && textarea) {
    cm = CodeMirror.fromTextArea(textarea, {
      mode: mode,
      theme: 'dracula',
      lineNumbers: true,
      indentWithTabs: false,
      tabSize: 4,
      indentUnit: 4,
      lineWrapping: true,
      autofocus: true,
    });
    cm.setSize(null, 'auto');
  }
}

function getCode() {
  if (cm) return cm.getValue();
  const ta = document.getElementById('code-editor');
  return ta ? ta.value : '';
}

function showResult(data) {
  const area = document.getElementById('result-area');
  area.classList.remove('hidden');

  if (data.error) {
    area.innerHTML = `<div class="result-error">${escHtml(data.error)}</div>`;
    return;
  }

  if (data.scalar !== undefined) {
    area.innerHTML = `<div class="q-desc"><strong>Résultat :</strong> ${escHtml(String(data.scalar))}</div>`;
    return;
  }

  const cols = data.columns || [];
  const rows = data.rows || [];

  let html = `<div class="result-table-wrap"><table class="result-table"><thead><tr>`;
  cols.forEach(c => { html += `<th>${escHtml(String(c))}</th>`; });
  html += `</tr></thead><tbody>`;

  rows.slice(0, 200).forEach(row => {
    html += '<tr>';
    row.forEach(cell => {
      html += `<td>${cell === null ? '<em style="color:#475569">NULL</em>' : escHtml(String(cell))}</td>`;
    });
    html += '</tr>';
  });

  html += `</tbody></table></div>`;
  html += `<div class="result-meta">${rows.length} ligne(s)${rows.length > 200 ? ' (200 affichées)' : ''}</div>`;
  area.innerHTML = html;
}

async function runCode() {
  const code = getCode();
  const btn = document.querySelector('.btn-run');
  btn.textContent = 'Exécution...';
  btn.disabled = true;

  try {
    const resp = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category: CATEGORY, code }),
    });
    const data = await resp.json();
    showResult(data);
  } catch (e) {
    document.getElementById('result-area').innerHTML = `<div class="result-error">Erreur réseau : ${e}</div>`;
    document.getElementById('result-area').classList.remove('hidden');
  } finally {
    btn.textContent = 'Exécuter';
    btn.disabled = false;
  }
}

async function checkAnswer() {
  const code = getCode();
  const banner = document.getElementById('check-banner');
  const btn = document.querySelector('.btn-check');
  btn.textContent = 'Vérification...';
  btn.disabled = true;

  try {
    const resp = await fetch('/check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category: CATEGORY, question_id: QUESTION_ID, code }),
    });
    const data = await resp.json();
    banner.classList.remove('hidden', 'check-pass', 'check-fail');

    if (data.passed) {
      banner.classList.add('check-pass');
      banner.textContent = '✓ ' + (data.message || 'Résultat correct !');
    } else {
      banner.classList.add('check-fail');
      banner.textContent = '✗ ' + (data.message || 'Résultat incorrect.');
    }
  } catch (e) {
    banner.classList.remove('hidden');
    banner.classList.add('check-fail');
    banner.textContent = 'Erreur : ' + e;
  } finally {
    btn.textContent = 'Vérifier';
    btn.disabled = false;
  }
}

async function toggleSolution() {
  const panel = document.getElementById('solution-panel');
  if (!panel.classList.contains('hidden')) {
    panel.classList.add('hidden');
    return;
  }

  const resp = await fetch(`/solution/${CATEGORY}/${QUESTION_ID}`);
  const data = await resp.json();

  document.getElementById('solution-code').textContent = data.solution_code || '';
  document.getElementById('solution-explanation').textContent = data.explanation || '';
  panel.classList.remove('hidden');
}

function setStatus(status) {
  fetch('/progress', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: QUESTION_ID, category: CATEGORY, status }),
  }).then(() => window.location.reload());
}

function escHtml(str) {
  return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
