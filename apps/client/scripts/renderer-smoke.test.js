const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { JSDOM } = require('jsdom');

const renderer = path.join(__dirname, '..', 'renderer');
const tick = () => new Promise(resolve => setTimeout(resolve, 20));

test('regular and contest problems open focused statement and code workspace, then return', async () => {
  const html = fs.readFileSync(path.join(renderer, 'index.html'), 'utf8');
  const source = fs.readFileSync(path.join(renderer, 'app.js'), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'outside-only', url: 'file:///client/index.html' });
  const { window } = dom;
  window.katex = { render: (expression, target) => { target.dataset.rendered = expression; } };
  window.eval(fs.readFileSync(path.join(renderer, 'vendor', 'statement.bundle.js'), 'utf8'));
  let onInvalidate;
  let problemReads = 0;
  window.client = {
    account: async () => null,
    liveStatus: async () => false,
    onLiveStatus: () => () => {},
    onLiveInvalidate: callback => { onInvalidate = callback; return () => {}; },
    api: async ({ kind, key }) => {
      if (kind === 'languages') return { objects: [{ key: 'CPP17', name: 'C++17' }] };
      if (kind === 'problems') return { objects: [{ code: 'AP', name: 'A + B', points: 100 }], total_objects: 1, total_pages: 1 };
      if (kind === 'contests') return { objects: [
        { key: 'C1', name: 'Thi thử', status: 'ongoing', start_time: '2026-10-16T00:00:00Z', participant_count: 1 },
        { key: 'C2', name: 'Thi sắp tới', status: 'upcoming', start_time: '2026-10-20T00:00:00Z', participant_count: 0 },
        { key: 'C3', name: 'Thi đã kết thúc', status: 'ended', start_time: '2026-10-10T00:00:00Z', participant_count: 8 }
      ] };
      if (kind === 'contest' && key === 'C1') return { object: { key: 'C1', name: 'Thi thử', status: 'ongoing', problems: [{ code: 'AP', name: 'A + B', output_prefix: 'A' }] } };
      if (kind === 'problem' && key === 'AP') { problemReads++; return { object: { code: 'AP', name: 'A + B', description: 'Tính $A+B$.', points: 100, time_limit: 1, memory_limit: 65536 } }; }
      throw new Error(`Unexpected API request: ${kind}`);
    },
    getDraft: async () => '',
    setDraft: async () => {},
    openSite: () => {}
  };
  try {
    window.eval(source);
    await tick();
    assert.equal(window.document.getElementById('problem-list').hidden, false);
    assert.equal(window.document.getElementById('editor-area').hidden, true);
    window.document.querySelector('.problem-item').click();
    await tick();
    assert.equal(window.document.getElementById('problems-view').classList.contains('problem-focus'), true);
    assert.equal(window.document.getElementById('problem-list').hidden, true);
    assert.equal(window.document.getElementById('editor-area').hidden, false);
    assert.equal(window.document.getElementById('contest-context').hidden, false);
    assert.equal(window.document.getElementById('back-to-contest').textContent, '← Quay lại danh sách');
    assert.equal(window.document.getElementById('contest-context-name').textContent, 'A + B');
    window.document.getElementById('back-to-contest').click();
    assert.equal(window.document.getElementById('problems-view').classList.contains('problem-focus'), false);
    assert.equal(window.document.getElementById('problems-view').classList.contains('problem-browse'), true);
    assert.equal(window.document.getElementById('problem-list').hidden, false);
    assert.equal(window.document.getElementById('editor-area').hidden, true);
    window.document.getElementById('nav-contests').click();
    await tick();
    assert.equal(window.document.querySelectorAll('.contest-group').length, 3);
    assert.equal(window.document.getElementById('contest-count').textContent, '3 cuộc thi');
    const search = window.document.getElementById('contest-search');
    search.value = 'sắp tới';
    window.document.getElementById('contest-search-form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    assert.equal(window.document.querySelectorAll('.contest-card').length, 1);
    search.value = '';
    window.document.getElementById('contest-search-form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    window.document.querySelector('.contest-card').click();
    await tick();
    window.document.querySelector('.contest-problem').click();
    await tick();
    assert.equal(window.document.getElementById('problems-view').hidden, false);
    assert.equal(window.document.getElementById('problems-view').classList.contains('problem-focus'), true);
    assert.equal(window.document.getElementById('contest-context').hidden, false);
    assert.equal(window.document.getElementById('contest-context-name').textContent, 'Thi thử');
    assert.equal(window.document.querySelector('#statement-content .math-inline')?.dataset.rendered, 'A+B');
    assert.equal(window.document.getElementById('source-code').value.includes('int main()'), true);
    const sourceBeforeRefresh = window.document.getElementById('source-code').value;
    onInvalidate({ topics: ['problems'] });
    await new Promise(resolve => setTimeout(resolve, 300));
    assert.ok(problemReads >= 3, 'live update refreshes the selected statement');
    assert.equal(window.document.getElementById('source-code').value, sourceBeforeRefresh);

    window.document.getElementById('back-to-contest').click();
    await tick();
    assert.equal(window.document.getElementById('contests-view').hidden, false);
    assert.equal(window.document.getElementById('problems-view').classList.contains('problem-focus'), false);
    assert.equal(window.document.getElementById('editor-area').hidden, true);
    window.document.getElementById('nav-account').click();
    assert.equal(window.document.getElementById('profile-guest').hidden, false);
    assert.equal(window.document.getElementById('profile-content').hidden, true);
  } finally {
    window.close();
  }
});

test('statement renderer keeps examples and math readable while sanitizing HTML', () => {
  const dom = new JSDOM('<div id="statement"></div>', { runScripts: 'outside-only' });
  const { window } = dom;
  window.eval(fs.readFileSync(path.join(renderer, 'vendor', 'statement.bundle.js'), 'utf8'));
  const katex = { render: (expression, target) => { target.dataset.rendered = expression; } };
  try {
    const box = window.document.getElementById('statement');
    const aplus = fs.readFileSync(path.join(__dirname, '..', '..', '..', 'problem-data', 'problems', 'APLUS', 'statement', 'statement.md'), 'utf8');
    window.CodeProStatement.render(aplus, box, katex);
    assert.match(box.textContent, /Cho hai số nguyên/);
    assert.equal(box.querySelectorAll('pre code').length, 4);
    assert.equal(box.querySelector('.math-inline')?.dataset.rendered, 'A');
    window.CodeProStatement.render('## Mẫu\n\n- $a + b$\n\n`$raw$`\n\n<script>alert(1)</script><img src="x" onerror="alert(2)">', box, katex);
    assert.equal(box.querySelector('h2')?.textContent, 'Mẫu');
    assert.equal(box.querySelector('li .math-inline')?.dataset.rendered, 'a + b');
    assert.equal(box.querySelector('code')?.textContent, '$raw$');
    assert.equal(box.querySelector('script'), null);
    assert.equal(box.querySelector('img')?.getAttribute('onerror'), null);
  } finally { window.close(); }
});

test('all local problem statements render without dropping their content', () => {
  const dom = new JSDOM('<div id="statement"></div>', { runScripts: 'outside-only' });
  const { window } = dom;
  window.eval(fs.readFileSync(path.join(renderer, 'vendor', 'statement.bundle.js'), 'utf8'));
  const box = window.document.getElementById('statement');
  const katex = { render: (expression, target) => { target.dataset.rendered = expression; } };
  const root = path.join(__dirname, '..', '..', '..', 'problem-data', 'problems');
  let count = 0;
  try {
    for (const code of fs.readdirSync(root)) {
      const file = path.join(root, code, 'statement', 'statement.md');
      if (!fs.existsSync(file)) continue;
      const markdown = fs.readFileSync(file, 'utf8');
      window.CodeProStatement.render(markdown, box, katex);
      assert.ok(box.textContent.trim(), `${code}: empty statement after rendering`);
      count++;
    }
    assert.ok(count >= 300, `Expected the full local corpus, got ${count}`);
  } finally { window.close(); }
});

test('admin statement editor previews math and saves Markdown to statement API', async () => {
  const html = fs.readFileSync(path.join(renderer, 'index.html'), 'utf8');
  const source = fs.readFileSync(path.join(renderer, 'app.js'), 'utf8');
  const dom = new JSDOM(html, { runScripts: 'outside-only', url: 'file:///client/index.html' });
  const { window } = dom;
  const writes = [];
  window.HTMLDialogElement.prototype.showModal = function () { this.open = true; };
  window.HTMLDialogElement.prototype.close = function () { this.open = false; };
  window.katex = { render: (expression, target) => { target.dataset.rendered = expression; } };
  window.eval(fs.readFileSync(path.join(renderer, 'vendor', 'statement.bundle.js'), 'utf8'));
  window.client = {
    account: async () => ({ username: 'admin', role: 'admin', is_staff: true }),
    liveStatus: async () => false,
    onLiveStatus: () => () => {},
    onLiveInvalidate: () => () => {},
    api: async args => {
      if (args.method === 'PUT') { writes.push(args); return {}; }
      if (args.kind === 'languages') return { objects: [{ key: 'CPP17', name: 'C++17' }] };
      if (args.kind === 'problems') return { objects: [{ code: 'AP', name: 'A + B', is_public: true }], total_objects: 1, total_pages: 1, has_more: false };
      if (args.kind === 'problem') return { object: { code: 'AP', name: 'A + B', description: 'Cũ', points: 100 } };
      if (args.kind === 'problemStatement') return { markdown: '# Bản gốc\n$A+B$' };
      if (args.kind === 'userProfile') return { profile: { username: 'admin', display_name: 'Admin CodeProOJ', rank: 'Unrated', bio: 'Quản trị viên', is_verified: true }, statistics: { solved_problems: 7, attempted_problems: 8, contests: 2, total_submissions: 35, accepted_submissions: 22, ac_rate: 62.9 }, rating: { rating: 1200 }, recent_submissions: [{ problem_code: 'AP', problem_name: 'A + B', result: 'AC', date: 'Hôm nay' }] };
      throw new Error(`Unexpected API request: ${args.kind}`);
    },
    getDraft: async () => '',
    setDraft: async () => {},
    openSite: () => {}
  };
  try {
    window.eval(source);
    await tick();
    window.document.getElementById('nav-account').click();
    await tick();
    assert.equal(window.document.getElementById('account-view').hidden, false);
    assert.equal(window.document.getElementById('profile-name').textContent, 'Admin CodeProOJ');
    assert.equal(window.document.getElementById('profile-role').textContent, 'Quản trị viên');
    assert.equal(window.document.querySelectorAll('.profile-stat').length, 4);
    assert.match(window.document.getElementById('profile-recent').textContent, /A \+ B/);
    window.document.getElementById('nav-settings').click();
    const editorSize = window.document.getElementById('editor-font-size');
    editorSize.value = '16';
    editorSize.dispatchEvent(new window.Event('change'));
    assert.equal(window.document.documentElement.style.getPropertyValue('--editor-font-size'), '16px');
    window.document.getElementById('close-preferences').click();
    window.document.getElementById('nav-admin-problems').click();
    await tick();
    window.document.querySelector('#admin-problem-items button').click();
    await tick();
    const description = window.document.getElementById('edit-description');
    assert.equal(description.value, '# Bản gốc\n$A+B$');
    description.value = '# Đề mới\nTính $A+B$.';
    description.dispatchEvent(new window.Event('input', { bubbles: true }));
    assert.equal(window.document.querySelector('.statement-preview .math-inline')?.dataset.rendered, 'A+B');
    window.document.getElementById('edit-form').dispatchEvent(new window.Event('submit', { bubbles: true, cancelable: true }));
    await tick();
    assert.equal(writes[0].kind, 'problemStatement');
    assert.equal(writes[0].body.markdown, '# Đề mới\nTính $A+B$.');
    assert.equal(writes[1].kind, 'problem');
    assert.equal(Object.hasOwn(writes[1].body, 'description'), false);
    window.document.getElementById('close-edit').click();
    window.document.getElementById('new-contest').click();
    assert.deepEqual(
      [...window.document.querySelectorAll('#edit-display_target option')].map(option => option.value),
      ['both', 'client', 'web']
    );
  } finally {
    window.close();
  }
});
