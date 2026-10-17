const $ = id => document.getElementById(id);
const state = { page: 1, pages: 1, query: '', selected: null, problem: null, account: null, languages: [], view: 'problems', requestId: 0, contests: [], contestStatus: 'all', contestQuery: '', contest: null, contestKey: null, userPage: 1, userPages: 1, userQuery: '', twofaUser: null };
let draftTimer;
let pollTimer;
let currentDraftKey = '';
let codeEditor;
const sourceValue = () => codeEditor ? codeEditor.getValue() : $('source-code').value;
function setSourceValue(value) { if (codeEditor) codeEditor.setValue(value); else $('source-code').value = value; }
function ensureCodeEditor() {
  if (!codeEditor && window.CodeProEditor) codeEditor = window.CodeProEditor.mount({ parent: $('ide-editor'), textarea: $('source-code'), status: $('cursor-status'), language: $('language-select').value, onRun: runLocal, onSave: () => $('save-file').click() });
}
function updateFileTab() {
  const language = $('language-select').value;
  $('file-tab').textContent = /^PY/i.test(language) ? 'main.py' : 'main.cpp';
  codeEditor?.setLanguage(language);
}

function notice(message, error = false) {
  const box = $('notice');
  box.textContent = message;
  box.classList.toggle('error', error);
  box.hidden = false;
  clearTimeout(box.hideTimer);
  box.hideTimer = setTimeout(() => { box.hidden = true; }, 6500);
}
function errorText(err) {
  const message = err?.message || '';
  if (/fetch failed|ERR_NAME_NOT_RESOLVED|ENOTFOUND|ERR_CONNECTION_REFUSED/i.test(message)) return 'Không kết nối được CodeProOJ. Hãy kiểm tra kết nối mạng.';
  return message.replace(/^Error invoking remote method '[^']+': Error:\s*/, '') || 'Đã xảy ra lỗi. Vui lòng thử lại.';
}
function isAdmin() { return state.account?.role === 'admin' && !!(state.account?.is_staff || state.account?.is_superuser); }
function roleName(role) { return ({ admin: 'Quản trị viên', teacher: 'Giáo viên', setter: 'Người ra đề', user: 'Thí sinh' })[role] || 'Thí sinh'; }
async function logoutAccount() {
  await window.client.logout();
  state.account = null;
  updateAccount();
  if (state.view === 'account') loadProfile();
  notice('Đã đăng xuất.');
}
function setBusy(button, busy, label) {
  button.disabled = busy;
  button.textContent = busy ? 'Đang xử lý…' : label;
}
function draftKey() { return `${state.selected}:${$('language-select').value}`; }
function updateAccount() {
  $('login-btn').textContent = state.account ? state.account.username : 'Đăng nhập';
  document.body.classList.toggle('admin-mode', isAdmin());
  $('admin-nav').hidden = !isAdmin();
  document.querySelectorAll('.admin-only').forEach(item => { item.hidden = !isAdmin(); });
  if (!isAdmin() && state.view.startsWith('admin')) showView('problems');
  const box = $('account-panel');
  box.replaceChildren();
  if (!state.account) return;
  const name = document.createElement('div'); name.className = 'account-name'; name.textContent = state.account.username;
  const sub = document.createElement('div'); sub.className = 'account-sub'; sub.textContent = roleName(state.account.role);
  const logout = document.createElement('button'); logout.type = 'button'; logout.textContent = 'Đăng xuất';
  logout.addEventListener('click', logoutAccount);
  box.append(name, sub, logout);
}

async function loadProblems() {
  const requestId = ++state.requestId;
  $('problem-items').innerHTML = '<div class="placeholder">Đang tải bài tập…</div>';
  try {
    const data = await window.client.api({ kind: 'problems', query: { q: state.query, page: state.page, page_size: 30 } });
    if (requestId !== state.requestId) return;
    const items = data?.objects || [];
    state.pages = data?.total_pages || 1;
    $('problem-count').textContent = `${data?.total_objects || 0} bài công khai`;
    $('page-indicator').textContent = `${state.page} / ${state.pages}`;
    $('prev-page').disabled = state.page <= 1;
    $('next-page').disabled = state.page >= state.pages;
    const container = $('problem-items'); container.replaceChildren();
    if (!items.length) container.innerHTML = '<div class="placeholder">Không tìm thấy bài phù hợp.</div>';
    for (const item of items) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'problem-item';
      if (item.code === state.selected) button.classList.add('selected');
      const code = document.createElement('span'); code.className = 'item-code'; code.textContent = item.code;
      const title = document.createElement('strong'); title.textContent = item.name;
      const info = document.createElement('small'); info.textContent = `${item.points ?? 100} điểm · ${item.time_limit ?? 1}s`;
      button.append(code, title, info);
      button.addEventListener('click', () => { setContestFocus(null); selectProblem(item.code); });
      container.append(button);
    }
    $('connection-text').textContent = (await window.client.liveStatus()) ? 'Đã kết nối CodeProOJ · trực tiếp' : 'Đã kết nối CodeProOJ · đang nối lại';
    document.querySelector('.status-dot').classList.add('online');
  } catch (err) {
    $('problem-items').innerHTML = '<div class="placeholder">Không tải được danh sách bài.</div>';
    $('connection-text').textContent = 'Mất kết nối';
    document.querySelector('.status-dot').classList.remove('online');
    notice(errorText(err), true);
  }
}

async function refreshSelectedProblem() {
  const code = state.selected;
  if (!code) return;
  try {
    const data = await window.client.api({ kind: 'problem', key: code });
    if (state.selected !== code || !data?.object) return;
    state.problem = data.object;
    $('problem-name').textContent = data.object.name;
    $('problem-meta').textContent = `${data.object.points ?? 100} điểm · ${data.object.time_limit ?? 1}s · ${Math.round((data.object.memory_limit ?? 262144) / 1024)} MB`;
    if (state.contestKey) $('problem-meta').append(element('span', `· ${state.contest?.name || state.contestKey}`));
    renderStatement(data.object.description);
    updateProblemFocus();
  } catch { /* Keep the open statement while the connection recovers. */ }
}

async function loadLanguages() {
  try {
    const data = await window.client.api({ kind: 'languages' });
    state.languages = data?.objects || [];
  } catch { state.languages = [{ key: 'CPP17', name: 'C++17' }, { key: 'PY3', name: 'Python 3' }]; }
  const select = $('language-select'); select.replaceChildren();
  for (const lang of state.languages) {
    const option = document.createElement('option'); option.value = lang.key; option.textContent = lang.name || lang.key; select.append(option);
  }
  if (state.languages.some(x => x.key === 'CPP17')) select.value = 'CPP17';
  updateFileTab();
}

async function selectProblem(code) {
  if (draftTimer) { clearTimeout(draftTimer); draftTimer = null; await saveDraft(); }
  state.selected = code;
  state.problem = null;
  setProblemFocus(true);
  for (const button of document.querySelectorAll('.problem-item')) button.classList.toggle('selected', button.querySelector('.item-code')?.textContent === code);
  $('empty-state').hidden = true;
  $('problem-workspace').hidden = false;
  $('problem-code').textContent = code;
  $('problem-name').textContent = 'Đang tải…';
  $('statement-content').textContent = 'Đang tải đề bài…';
  $('submission-result').hidden = true;
  $('run-output').hidden = true;
  const selected = code;
  try {
    const data = await window.client.api({ kind: 'problem', key: code });
    if (state.selected !== selected) return;
    const problem = data?.object;
    if (!problem) throw new Error('Không tìm thấy bài tập.');
    state.problem = problem;
    $('problem-name').textContent = problem.name;
    updateProblemFocus();
    $('problem-meta').textContent = `${problem.points ?? 100} điểm · ${problem.time_limit ?? 1}s · ${Math.round((problem.memory_limit ?? 262144) / 1024)} MB`;
    if (state.contestKey) $('problem-meta').append(element('span', `· ${state.contest?.name || state.contestKey}`));
    renderStatement(problem.description);
    await loadDraft();
  } catch (err) { $('statement-content').textContent = 'Không tải được đề bài.'; notice(errorText(err), true); }
}

function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = String(text);
  if (className) node.className = className;
  return node;
}
function dateText(value) { return value ? new Date(value).toLocaleString('vi-VN') : 'Chưa xác định'; }
function statusText(value) { return ({ ongoing: 'Đang diễn ra', upcoming: 'Sắp tới', ended: 'Đã kết thúc' })[value] || value; }
function setContestFocus(contest) {
  state.contestKey = contest?.key || null;
  updateProblemFocus();
}
function setProblemFocus(active) {
  $('problems-view').classList.toggle('problem-focus', active);
  $('problems-view').classList.toggle('problem-browse', !active);
  $('problem-list').hidden = active;
  $('editor-area').hidden = !active;
  if (active) ensureCodeEditor();
  updateProblemFocus();
}
function updateProblemFocus() {
  const focused = $('problems-view').classList.contains('problem-focus');
  $('contest-context').hidden = !focused;
  $('back-to-contest').textContent = state.contestKey ? '← Quay lại cuộc thi' : '← Quay lại danh sách';
  $('contest-context-label').textContent = state.contestKey ? 'ĐANG LÀM BÀI THI' : 'ĐANG LÀM BÀI TẬP';
  $('contest-context-name').textContent = state.contestKey ? (state.contest?.name || '') : (state.problem?.name || '');
}
function renderStatement(value, box = $('statement-content')) {
  if (window.CodeProStatement) window.CodeProStatement.render(value, box, window.katex);
  else box.textContent = String(value || 'Đề bài chưa có nội dung.');
}

async function loadContests() {
  $('contest-items').replaceChildren(element('div', 'Đang tải cuộc thi…', 'placeholder'));
  try {
    const data = await window.client.api({ kind: 'contests', query: isAdmin() ? { all: 1 } : {} });
    state.contests = data?.objects || [];
    renderContests();
    if (state.contest && state.contests.some(item => item.key === state.contest.key)) await openContest(state.contest.key);
    else $('contest-detail').hidden = true;
  } catch (err) { $('contest-items').replaceChildren(element('div', 'Không tải được cuộc thi.', 'placeholder')); notice(errorText(err), true); }
}
function renderContests() {
  const box = $('contest-items'); box.replaceChildren();
  $('contest-count').textContent = `${state.contests.length} cuộc thi`;
  const query = state.contestQuery.toLocaleLowerCase('vi-VN');
  const items = state.contests.filter(item => (state.contestStatus === 'all' || item.status === state.contestStatus) && (!query || `${item.name} ${item.key}`.toLocaleLowerCase('vi-VN').includes(query)));
  if (!items.length) { box.append(element('div', state.contests.length ? 'Không tìm thấy cuộc thi phù hợp.' : 'Chưa có cuộc thi nào được công bố.', 'contest-empty')); return; }
  const groups = [
    ['ongoing', 'Đang diễn ra', 'Các cuộc thi đang mở để tham gia.'],
    ['upcoming', 'Sắp tới', 'Các cuộc thi chuẩn bị bắt đầu.'],
    ['ended', 'Đã kết thúc', 'Xem lại đề thi và kết quả.']
  ];
  for (const [status, label, description] of groups) {
    const groupItems = items.filter(item => item.status === status);
    if (!groupItems.length) continue;
    const section = element('section', '', `contest-group ${status}`);
    const heading = element('div', '', 'contest-group-head');
    heading.append(element('h3', `${label} (${groupItems.length})`), element('p', description));
    section.append(heading);
    for (const item of groupItems) {
      const button = element('button', '', 'contest-card'); button.type = 'button';
      if (item.key === state.contest?.key) button.classList.add('selected');
      const icon = element('span', '', 'contest-card-icon'); icon.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 3h8v3h4v3a4 4 0 0 1-4 4h-.2A5 5 0 0 1 13 15.8V19h3v2H8v-2h3v-3.2A5 5 0 0 1 8.2 13H8a4 4 0 0 1-4-4V6h4V3Z"/><path d="M8 6v4a3 3 0 0 0 3 3h2a3 3 0 0 0 3-3V6M4 8v1a2 2 0 0 0 2 2h2m12-3v1a2 2 0 0 1-2 2h-2"/></svg>';
      const info = element('span', '', 'contest-card-info');
      info.append(element('strong', item.name), element('small', `${dateText(item.start_time)} – ${dateText(item.end_time)}`), element('small', `${item.participant_count ?? 0} thí sinh · ${item.key}${isAdmin() ? ` · ${{ both: 'Web + client', web: 'Chỉ web', client: 'Chỉ client' }[item.display_target] || 'Web + client'}${item.is_visible ? '' : ' · Bản nháp'}` : ''}`));
      const action = element('span', item.status === 'ended' ? 'Xem kết quả' : 'Xem chi tiết', 'contest-card-action');
      button.append(icon, info, action);
      button.addEventListener('click', () => openContest(item.key, true)); section.append(button);
    }
    box.append(section);
  }
}
async function openContest(key, scrollToDetail = false) {
  $('contest-detail').hidden = false;
  $('contest-detail').replaceChildren(element('div', 'Đang tải chi tiết…', 'placeholder'));
  try {
    const data = await window.client.api({ kind: 'contest', key });
    state.contest = data?.object;
    const contest = state.contest;
    if (!contest) throw new Error('Không tìm thấy cuộc thi.');
    const box = $('contest-detail'); box.replaceChildren();
    const head = element('div', '', 'contest-detail-head');
    const back = element('button', '← Danh sách cuộc thi', 'button subtle contest-back'); back.type = 'button'; back.addEventListener('click', () => $('contest-items').scrollIntoView?.({ behavior: 'smooth', block: 'start' }));
    box.append(back);
    head.append(element('span', statusText(contest.status), `status-pill ${contest.status}`), element('h2', contest.name), element('p', contest.description || 'Chưa có mô tả.'), element('small', `${dateText(contest.start_time)} → ${dateText(contest.end_time)}`));
    box.append(head);
    const actions = element('div', '', 'contest-actions');
    if (state.account && contest.status !== 'ended') {
      const join = element('button', contest.is_registered ? 'Rời cuộc thi' : 'Tham gia cuộc thi', 'button secondary');
      join.addEventListener('click', async () => { try { await window.client.api({ kind: contest.is_registered ? 'contestLeave' : 'contestJoin', key, body: {} }); notice(contest.is_registered ? 'Đã rời cuộc thi.' : 'Đã tham gia cuộc thi.'); await openContest(key); } catch (err) { notice(errorText(err), true); } }); actions.append(join);
    }
    const score = element('button', 'Bảng xếp hạng', 'button subtle'); score.addEventListener('click', () => loadScoreboard(key)); actions.append(score);
    if (isAdmin()) { const edit = element('button', 'Chỉnh sửa', 'button secondary'); edit.addEventListener('click', () => editContest(contest)); actions.append(edit); }
    box.append(actions, element('h3', 'Bài thi'));
    const list = element('div', '', 'contest-problems');
    if (!contest.problems?.length) list.append(element('div', 'Chưa có bài thi.', 'placeholder'));
    for (const problem of contest.problems || []) {
      const button = element('button', `${problem.output_prefix || problem.order}. ${problem.name} · ${problem.points ?? 100} điểm`, 'contest-problem');
      button.addEventListener('click', async () => { showView('problems'); setContestFocus(contest); await selectProblem(problem.code); }); list.append(button);
    }
    box.append(list);
    renderContests();
    if (scrollToDetail) box.scrollIntoView?.({ behavior: 'smooth', block: 'start' });
  } catch (err) { $('contest-detail').replaceChildren(element('div', 'Không tải được chi tiết cuộc thi.', 'placeholder')); notice(errorText(err), true); }
}
async function loadScoreboard(key) {
  try {
    const data = await window.client.api({ kind: 'scoreboard', key });
    const old = $('scoreboard'); if (old) old.remove();
    const box = element('div', '', 'scoreboard'); box.id = 'scoreboard'; box.append(element('h3', 'Bảng xếp hạng'));
    if (!data?.standings?.length) box.append(element('div', 'Chưa có kết quả.', 'placeholder'));
    for (const row of data?.standings || []) box.append(element('div', `#${row.rank}  ${row.user}  ·  ${row.score} điểm`, 'score-row'));
    $('contest-detail').append(box);
  } catch (err) { notice(errorText(err), true); }
}

async function loadOverview() {
  $('admin-metrics').replaceChildren(element('div', 'Đang tải số liệu…', 'placeholder'));
  try {
    const data = await window.client.api({ kind: 'adminOverview' });
    const box = $('admin-metrics'); box.replaceChildren();
    for (const [label, key] of [['Người dùng', 'total_users'], ['Bài tập', 'total_problems'], ['Cuộc thi', 'total_contests'], ['Bài nộp', 'total_submissions'], ['Cuộc thi đang diễn ra', 'active_contests'], ['Bài nộp hôm nay', 'today_submissions']]) {
      const card = element('div', '', 'metric-card'); card.append(element('strong', data?.[key] ?? '—'), element('span', label)); box.append(card);
    }
  } catch (err) { $('admin-metrics').replaceChildren(element('div', 'Không tải được số liệu quản trị.', 'placeholder')); notice(errorText(err), true); }
}
async function loadAdminProblems() {
  $('admin-problem-items').replaceChildren(element('div', 'Đang tải bài tập…', 'placeholder'));
  try {
    const items = [];
    let page = 1;
    while (true) {
      const data = await window.client.api({ kind: 'problems', query: { all: 1, page, page_size: 1000 } });
      items.push(...(data?.objects || []));
      if (!data?.has_more || page >= 100) break;
      page++;
    }
    const box = $('admin-problem-items'); box.replaceChildren();
    if (!items.length) box.append(element('div', 'Chưa có bài tập.', 'placeholder'));
    for (const item of items) {
      const row = element('div', '', 'management-row'); row.append(element('strong', item.code), element('span', item.name), element('small', item.is_public ? 'Công khai' : 'Bản nháp'));
      const edit = element('button', 'Sửa', 'button subtle'); edit.addEventListener('click', async () => {
        try {
          const detail = await window.client.api({ kind: 'problem', key: item.code });
          let markdown = '';
          try { markdown = (await window.client.api({ kind: 'problemStatement', key: item.code }))?.markdown || ''; } catch { /* Older problems may have no statement package. */ }
          editProblem({ ...detail.object, description: markdown || detail.object.description });
        } catch (err) { notice(errorText(err), true); }
      }); row.append(edit); box.append(row);
    }
  } catch (err) { $('admin-problem-items').replaceChildren(element('div', 'Không tải được bài tập.', 'placeholder')); notice(errorText(err), true); }
}
async function loadUsers() {
  $('admin-user-items').replaceChildren(element('div', 'Đang tải người dùng…', 'placeholder'));
  try {
    const data = await window.client.api({ kind: 'users', query: { q: state.userQuery, page: state.userPage, page_size: 50 } });
    state.userPages = data?.total_pages || 1; $('user-page-indicator').textContent = `${state.userPage} / ${state.userPages}`;
    $('user-prev').disabled = state.userPage <= 1; $('user-next').disabled = state.userPage >= state.userPages;
    const box = $('admin-user-items'); box.replaceChildren();
    if (!data?.objects?.length) box.append(element('div', 'Không tìm thấy người dùng.', 'placeholder'));
    for (const user of data?.objects || []) {
      const row = element('div', '', 'management-row'); row.append(element('strong', user.username), element('span', user.email || '—'), element('small', roleName(user.role)));
      const edit = element('button', 'Vai trò', 'button subtle'); edit.addEventListener('click', () => editUser(user)); row.append(edit); box.append(row);
    }
  } catch (err) { $('admin-user-items').replaceChildren(element('div', 'Không tải được người dùng.', 'placeholder')); notice(errorText(err), true); }
}

let editAction = null;
function editForm(title, fields, action) {
  $('edit-title').textContent = title; $('edit-error').textContent = '';
  $('edit-dialog').classList.toggle('statement-edit', fields.some(field => field.key === 'description') && title.includes('bài tập'));
  const box = $('edit-fields'); box.replaceChildren();
  for (const field of fields) {
    const label = element('label', field.label); label.htmlFor = `edit-${field.key}`;
    let input;
    if (field.type === 'textarea') input = document.createElement('textarea');
    else if (field.type === 'select') {
      input = document.createElement('select');
      for (const [value, name] of field.options) { const option = element('option', name); option.value = value; input.append(option); }
    } else { input = document.createElement('input'); input.type = field.type || 'text'; }
    input.id = `edit-${field.key}`; input.name = field.key;
    if (field.type === 'checkbox') input.checked = !!field.value;
    else input.value = field.value ?? '';
    if (field.required) input.required = true;
    if (field.readOnly) input.readOnly = true;
    if (field.type === 'number') { input.step = field.step || 'any'; input.min = '0'; }
    box.append(label, input);
  }
  if ($('edit-dialog').classList.contains('statement-edit')) {
    const hint = element('p', 'Soạn đề bằng Markdown; công thức $...$ hiển thị trong bản xem trước. Nếu đề cũ đã mất biến, hãy đối chiếu nguồn gốc trước khi lưu.', 'edit-hint');
    const previewLabel = element('label', 'Xem trước đề bài');
    const preview = element('div', '', 'statement-content statement-preview');
    box.append(hint, previewLabel, preview);
    const description = $('edit-description');
    description.addEventListener('input', () => renderStatement(description.value, preview));
    renderStatement(description.value, preview);
  }
  editAction = action; $('edit-dialog').showModal();
}
function dateInput(value) { if (!value) return ''; const date = new Date(value); return Number.isNaN(date.getTime()) ? '' : new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16); }
function editContest(contest = null) {
  editForm(contest ? 'Chỉnh sửa cuộc thi' : 'Tạo cuộc thi', [
    { key: 'key', label: 'Mã cuộc thi', value: contest?.key, required: true, readOnly: !!contest },
    { key: 'name', label: 'Tên cuộc thi', value: contest?.name, required: true },
    { key: 'description', label: 'Mô tả', type: 'textarea', value: contest?.description },
    { key: 'start_time', label: 'Bắt đầu', type: 'datetime-local', value: dateInput(contest?.start_time), required: true },
    { key: 'end_time', label: 'Kết thúc', type: 'datetime-local', value: dateInput(contest?.end_time), required: true },
    { key: 'format_name', label: 'Hình thức', type: 'select', options: [['icpc', 'ICPC'], ['ioi', 'IOI']], value: contest?.format_name || 'icpc' },
    { key: 'problems', label: 'Mã bài thi (cách nhau bằng dấu phẩy)', value: contest?.problems?.map(item => item.code).join(', ') || '' },
    { key: 'display_target', label: 'Nơi hiển thị', type: 'select', options: [['both', 'Trên web và client'], ['client', 'Chỉ trên client'], ['web', 'Chỉ trên web']], value: contest?.display_target || 'both' },
    { key: 'is_visible', label: 'Công khai', type: 'checkbox', value: contest?.is_visible ?? true },
    { key: 'is_rated', label: 'Tính rating', type: 'checkbox', value: contest?.is_rated ?? false }
  ], async values => {
    const body = { ...values, start_time: new Date(values.start_time).toISOString(), end_time: new Date(values.end_time).toISOString(), problems: values.problems.split(',').map(x => x.trim().toUpperCase()).filter(Boolean) };
    if (new Date(body.end_time) <= new Date(body.start_time)) throw new Error('Thời gian kết thúc phải sau thời gian bắt đầu.');
    await window.client.api({ kind: contest ? 'contest' : 'contests', key: contest?.key, method: contest ? 'PUT' : 'POST', body });
    notice(contest ? 'Đã cập nhật cuộc thi.' : 'Đã tạo cuộc thi.'); await loadContests();
  });
}
function editProblem(problem = null) {
  editForm(problem ? 'Chỉnh sửa bài tập' : 'Tạo bài tập', [
    { key: 'code', label: 'Mã bài', value: problem?.code, required: true, readOnly: !!problem },
    { key: 'name', label: 'Tên bài', value: problem?.name, required: true },
    { key: 'description', label: 'Đề bài (Markdown + LaTeX)', type: 'textarea', value: problem?.description, required: true },
    { key: 'points', label: 'Điểm', type: 'number', value: problem?.points ?? 100 },
    { key: 'time_limit', label: 'Giới hạn thời gian (giây)', type: 'number', value: problem?.time_limit ?? 1 },
    { key: 'memory_limit', label: 'Giới hạn bộ nhớ (KB)', type: 'number', value: problem?.memory_limit ?? 262144, step: '1' },
    { key: 'is_public', label: 'Công khai', type: 'checkbox', value: problem?.is_public ?? false }
  ], async values => {
    const body = { ...values, code: values.code.toUpperCase(), points: Number(values.points), time_limit: Number(values.time_limit), memory_limit: Number(values.memory_limit) };
    const statement = { markdown: body.description, html: body.description };
    if (problem) {
      await window.client.api({ kind: 'problemStatement', key: problem.code, method: 'PUT', body: statement });
      const { description, code, ...metadata } = body;
      await window.client.api({ kind: 'problem', key: problem.code, method: 'PUT', body: metadata });
    } else {
      await window.client.api({ kind: 'problems', method: 'POST', body });
      await window.client.api({ kind: 'problemStatement', key: body.code, method: 'PUT', body: statement });
    }
    notice(problem ? 'Đã cập nhật bài tập.' : 'Đã tạo bài tập.'); await loadAdminProblems();
  });
}
function editUser(user) {
  editForm(`Vai trò: ${user.username}`, [
    { key: 'role', label: 'Vai trò', type: 'select', options: [['user', 'Thí sinh'], ['teacher', 'Giáo viên'], ['setter', 'Người ra đề'], ['admin', 'Quản trị viên']], value: user.role }
  ], async values => {
    if (user.username === state.account?.username) throw new Error('Không thể tự thay đổi vai trò trong client.');
    if (values.role === 'admin' && user.role !== 'admin' && !confirm(`Cấp quyền quản trị cho ${user.username}?`)) return false;
    await window.client.api({ kind: 'userRole', key: user.username, body: { role: values.role } });
    notice(`Đã cập nhật vai trò của ${user.username}.`); await loadUsers();
  });
}

async function loadDraft() {
  if (!state.selected) return;
  const key = draftKey();
  currentDraftKey = key;
  const source = await window.client.getDraft(key);
  if (key !== draftKey()) return;
  setSourceValue(source || (key.endsWith(':PY3') ? 'import sys\n\ndef main():\n    pass\n\nif __name__ == "__main__":\n    main()\n' : '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n\n    return 0;\n}\n'));
  $('draft-status').textContent = source ? 'Đã tải bản nháp' : 'Bản nháp tự lưu';
}

async function saveDraft() {
  if (!currentDraftKey) return;
  const key = currentDraftKey, source = sourceValue();
  try { await window.client.setDraft(key, source); $('draft-status').textContent = 'Đã lưu bản nháp'; }
  catch (err) { $('draft-status').textContent = 'Lưu bản nháp thất bại'; notice(errorText(err), true); }
}

async function runLocal() {
  const button = $('run-btn'); setBusy(button, true, '▶ Biên dịch & chạy');
  const output = $('run-output'); output.hidden = false; output.textContent = 'Đang biên dịch và chạy…';
  try {
    const result = await window.client.run({ language: $('language-select').value, source: sourceValue(), input: $('stdin').value });
    const prefix = result.stage === 'compile' ? 'Lỗi biên dịch' : result.timedOut ? 'Quá thời gian chạy thử' : `Mã thoát: ${result.code}`;
    output.textContent = `${prefix}\n\n${result.stdout || ''}${result.stderr || ''}`;
  } catch (err) { output.textContent = errorText(err); }
  finally { setBusy(button, false, '▶ Biên dịch & chạy'); }
}

async function submit() {
  if (!state.account) { $('login-dialog').showModal(); return; }
  const source = sourceValue().trim();
  if (!source) { notice('Hãy nhập mã nguồn trước khi nộp.', true); return; }
  const button = $('submit-btn'); setBusy(button, true, 'Nộp bài');
  try {
    await saveDraft();
    const result = await window.client.api({ kind: 'submit', body: { problem: state.selected, language: $('language-select').value, source, ...(state.contestKey ? { contest: state.contestKey } : {}) } });
    const box = $('submission-result'); box.hidden = false; box.textContent = `Đã nộp bài #${result.submission_id}. Kết quả: ${result.result || result.status || 'đang chấm'}`;
    notice(`Đã nộp bài #${result.submission_id}.`);
    clearInterval(pollTimer);
    if (!result.result || ['QU', 'P', 'G'].includes(result.status)) {
      let attempts = 0;
      pollTimer = setInterval(async () => {
        if (++attempts > 20) { clearInterval(pollTimer); return; }
        try {
          const data = await window.client.api({ kind: 'submission', key: String(result.submission_id) });
          const sub = data?.object;
          if (sub) box.textContent = `Bài nộp #${result.submission_id}: ${sub.result || sub.status || 'đang chấm'} · ${sub.points ?? 0} điểm`;
          if (sub?.result && !['QU', 'P', 'G'].includes(sub.status)) clearInterval(pollTimer);
        } catch { clearInterval(pollTimer); }
      }, 2500);
    }
  } catch (err) { notice(errorText(err), true); }
  finally { setBusy(button, false, 'Nộp bài'); }
}

async function showSubmissions() {
  if (!state.account) { $('submission-items').innerHTML = '<div class="placeholder">Đăng nhập để xem bài nộp của bạn.</div>'; return; }
  $('submission-items').innerHTML = '<div class="placeholder">Đang tải bài nộp…</div>';
  try {
    const data = await window.client.api({ kind: 'submissions', query: { user: state.account.username, page_size: 50 } });
    const box = $('submission-items'); box.replaceChildren();
    if (!data?.objects?.length) box.innerHTML = '<div class="placeholder">Bạn chưa có bài nộp.</div>';
    for (const sub of data?.objects || []) {
      const row = document.createElement('div'); row.className = 'submission-row';
      const id = document.createElement('strong'); id.textContent = `#${sub.id}`;
      const problem = document.createElement('span'); problem.textContent = sub.problem;
      const lang = document.createElement('small'); lang.textContent = sub.language;
      const verdict = document.createElement('span'); verdict.className = `verdict ${sub.result === 'AC' ? 'ac' : ''}`; verdict.textContent = sub.result || sub.status || 'Đang chấm';
      const date = document.createElement('small'); date.textContent = sub.date ? new Date(sub.date).toLocaleString('vi-VN') : '';
      row.append(id, problem, lang, verdict, date); box.append(row);
    }
  } catch (err) { $('submission-items').innerHTML = '<div class="placeholder">Không tải được bài nộp.</div>'; notice(errorText(err), true); }
}

async function loadProfile() {
  const username = state.account?.username;
  $('profile-loading').hidden = !username;
  $('profile-guest').hidden = !!username;
  $('profile-content').hidden = true;
  if (!username) return;
  $('profile-loading').textContent = 'Đang tải hồ sơ…';
  try {
    const data = await window.client.api({ kind: 'userProfile', key: username });
    if (state.account?.username !== username || state.view !== 'account') return;
    const profile = data?.profile || {};
    const stats = data?.statistics || {};
    const rating = data?.rating || {};
    $('profile-name').textContent = profile.display_name || username;
    $('profile-handle').textContent = `@${username}`;
    $('profile-avatar').textContent = (profile.display_name || username).trim().slice(0, 1).toUpperCase();
    $('profile-rank').textContent = profile.rank || rating.rank || 'Unrated';
    $('profile-role').textContent = roleName(state.account.role);
    $('profile-verified').hidden = !profile.is_verified;
    $('profile-bio').textContent = profile.bio || '';
    $('profile-bio').hidden = !profile.bio;

    const meta = $('profile-meta'); meta.replaceChildren();
    for (const value of [profile.country, profile.school, profile.organization]) {
      if (value) meta.append(element('span', value));
    }
    if (profile.created_at) meta.append(element('span', `Tham gia ${new Date(profile.created_at).toLocaleDateString('vi-VN')}`));

    const cards = [
      ['Bài đã giải', stats.solved_problems ?? profile.solved_count ?? 0],
      ['Bài đã thử', stats.attempted_problems ?? 0],
      ['Cuộc thi', stats.contests ?? rating.contest_count ?? 0],
      ['Rating', rating.rating ?? profile.rating ?? 0]
    ];
    const cardBox = $('profile-stats'); cardBox.replaceChildren();
    for (const [label, value] of cards) {
      const card = element('div', undefined, 'profile-stat panel');
      card.append(element('strong', value), element('span', label));
      cardBox.append(card);
    }

    const activity = $('profile-activity'); activity.replaceChildren();
    const accepted = Number(stats.accepted_submissions || 0);
    const total = Number(stats.total_submissions || 0);
    const rate = Math.max(0, Math.min(100, Number(stats.ac_rate || 0)));
    const track = element('div', undefined, 'profile-progress');
    const fill = element('span'); fill.style.width = `${rate}%`; track.append(fill);
    activity.append(element('div', `${rate}% chấp nhận`, 'profile-rate'), track);
    for (const [label, value] of [['Tổng bài nộp', total], ['Được chấp nhận', accepted], ['Sai kết quả', stats.wrong_answers ?? 0]]) {
      const row = element('div', undefined, 'profile-activity-row');
      row.append(element('span', label), element('strong', value)); activity.append(row);
    }

    const recent = $('profile-recent'); recent.replaceChildren();
    const submissions = data?.recent_submissions || [];
    if (!submissions.length) recent.append(element('p', 'Bạn chưa có bài nộp.', 'placeholder'));
    for (const sub of submissions) {
      const row = element('div', undefined, 'profile-submission');
      const info = element('div');
      info.append(element('strong', sub.problem_name || sub.problem_code || 'Bài tập'), element('small', `${sub.problem_code || ''} · ${sub.date || ''}`));
      const verdict = element('span', sub.result || 'Đang chấm', `verdict ${sub.result === 'AC' ? 'ac' : ''}`);
      row.append(info, verdict); recent.append(row);
    }
    $('profile-loading').hidden = true;
    $('profile-content').hidden = false;
  } catch (err) {
    if (state.account?.username !== username || state.view !== 'account') return;
    $('profile-loading').textContent = `Không tải được hồ sơ: ${errorText(err)}`;
  }
}

function showView(view) {
  if (view.startsWith('admin') && !isAdmin()) return;
  if (view !== 'problems') { setContestFocus(null); setProblemFocus(false); }
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;
  state.view = view;
  for (const name of ['problems', 'submissions', 'contests', 'account', 'admin', 'admin-problems', 'admin-users']) $(`${name}-view`).hidden = name !== view;
  $('page-title').textContent = ({ problems: 'Bài tập', submissions: 'Bài nộp của tôi', contests: 'Cuộc thi', account: 'Hồ sơ cá nhân', admin: 'Tổng quan', 'admin-problems': 'Quản lý bài tập', 'admin-users': 'Người dùng' })[view];
  for (const name of ['problems', 'submissions', 'contests', 'account', 'admin', 'admin-problems', 'admin-users']) {
    const button = $(`nav-${name}`);
    button.classList.toggle('active', view === name);
    if (view === name) button.setAttribute('aria-current', 'page'); else button.removeAttribute('aria-current');
  }
  if (view === 'submissions') showSubmissions();
  if (view === 'account') loadProfile();
  if (view === 'contests') loadContests();
  if (view === 'admin') loadOverview();
  if (view === 'admin-problems') loadAdminProblems();
  if (view === 'admin-users') loadUsers();
}

async function init() {
  state.account = await window.client.account(); updateAccount();
  let pendingTopics = new Set();
  let refreshTimer = null;
  window.client.onLiveInvalidate(event => {
    for (const topic of event?.topics || []) pendingTopics.add(topic);
    clearTimeout(refreshTimer);
    refreshTimer = setTimeout(() => {
      const topics = pendingTopics;
      pendingTopics = new Set();
      if (topics.has('contests') && state.view === 'contests') loadContests();
      if (topics.has('problems')) {
        if (state.view === 'problems') {
          if (state.selected && $('problems-view').classList.contains('problem-focus')) refreshSelectedProblem();
          else loadProblems();
        }
        if (state.view === 'admin-problems') loadAdminProblems();
      }
      if (topics.has('submissions') && state.view === 'submissions') showSubmissions();
      if (topics.has('account') && state.view === 'account') loadProfile();
      if (topics.has('account') && state.view === 'admin-users') loadUsers();
    }, 250);
  });
  window.client.onLiveStatus(connected => {
    if (connected) $('connection-text').textContent = 'Đã kết nối CodeProOJ · trực tiếp';
    else if ($('connection-text').textContent.includes('trực tiếp')) $('connection-text').textContent = 'Đã kết nối CodeProOJ · đang nối lại';
  });
  if (await window.client.liveStatus()) $('connection-text').textContent = 'Đã kết nối CodeProOJ · trực tiếp';
  const editorSize = (() => { try { return window.localStorage.getItem('codeprooj-editor-size'); } catch { return null; } })();
  $('editor-font-size').value = ['12', '13', '14', '16'].includes(editorSize) ? editorSize : '13';
  document.documentElement.style.setProperty('--editor-font-size', `${$('editor-font-size').value}px`);
  $('editor-font-size').addEventListener('change', () => { const size = $('editor-font-size').value; document.documentElement.style.setProperty('--editor-font-size', `${size}px`); try { window.localStorage.setItem('codeprooj-editor-size', size); } catch { /* Storage can be unavailable in isolated preview contexts. */ } });
  $('nav-account').addEventListener('click', () => showView('account'));
  $('nav-settings').addEventListener('click', () => $('preferences-dialog').showModal());
  $('profile-login').addEventListener('click', () => $('login-dialog').showModal());
  $('profile-logout').addEventListener('click', logoutAccount);
  $('close-preferences').addEventListener('click', () => $('preferences-dialog').close());
  $('search-form').addEventListener('submit', event => { event.preventDefault(); state.query = $('search-input').value.trim(); state.page = 1; loadProblems(); });
  $('prev-page').addEventListener('click', () => { if (state.page > 1) { state.page--; loadProblems(); } });
  $('next-page').addEventListener('click', () => { if (state.page < state.pages) { state.page++; loadProblems(); } });
  $('refresh-btn').addEventListener('click', () => state.view === 'problems' ? loadProblems() : showView(state.view));
  $('contest-refresh').addEventListener('click', () => loadContests());
  $('contest-search-form').addEventListener('submit', event => { event.preventDefault(); state.contestQuery = $('contest-search').value.trim(); renderContests(); });
  $('nav-problems').addEventListener('click', () => { setContestFocus(null); setProblemFocus(false); showView('problems'); });
  $('back-to-contest').addEventListener('click', () => { if (state.contestKey) showView('contests'); else setProblemFocus(false); });
  $('nav-submissions').addEventListener('click', () => showView('submissions'));
  $('nav-contests').addEventListener('click', () => showView('contests'));
  $('nav-admin').addEventListener('click', () => showView('admin'));
  $('nav-admin-problems').addEventListener('click', () => showView('admin-problems'));
  $('nav-admin-users').addEventListener('click', () => showView('admin-users'));
  $('go-admin-contests').addEventListener('click', () => showView('contests'));
  $('go-admin-problems').addEventListener('click', () => showView('admin-problems'));
  $('go-admin-users').addEventListener('click', () => showView('admin-users'));
  $('new-contest').addEventListener('click', () => editContest());
  $('new-problem').addEventListener('click', () => editProblem());
  for (const button of document.querySelectorAll('.filter')) button.addEventListener('click', () => { state.contestStatus = button.dataset.status; document.querySelectorAll('.filter').forEach(node => node.classList.toggle('active', node === button)); renderContests(); });
  $('user-search-form').addEventListener('submit', event => { event.preventDefault(); state.userQuery = $('user-search').value.trim(); state.userPage = 1; loadUsers(); });
  $('user-prev').addEventListener('click', () => { if (state.userPage > 1) { state.userPage--; loadUsers(); } });
  $('user-next').addEventListener('click', () => { if (state.userPage < state.userPages) { state.userPage++; loadUsers(); } });
  $('close-edit').addEventListener('click', () => $('edit-dialog').close());
  $('edit-form').addEventListener('submit', async event => {
    event.preventDefault(); $('edit-error').textContent = '';
    const values = {};
    for (const input of $('edit-fields').querySelectorAll('input, select, textarea')) values[input.name] = input.type === 'checkbox' ? input.checked : input.value.trim();
    const button = $('edit-submit'); setBusy(button, true, 'Lưu');
    try { const result = await editAction(values); if (result !== false) $('edit-dialog').close(); }
    catch (err) { $('edit-error').textContent = errorText(err); }
    finally { setBusy(button, false, 'Lưu'); }
  });
  $('language-select').addEventListener('change', async () => { if (draftTimer) { clearTimeout(draftTimer); draftTimer = null; await saveDraft(); } updateFileTab(); await loadDraft(); });
  $('source-code').addEventListener('input', () => { $('draft-status').textContent = 'Đang lưu…'; clearTimeout(draftTimer); draftTimer = setTimeout(saveDraft, 600); });
  $('source-code').addEventListener('keydown', event => { if (event.key === 'Tab') { event.preventDefault(); const field = event.target; field.setRangeText('    ', field.selectionStart, field.selectionEnd, 'end'); field.dispatchEvent(new Event('input')); } });
  $('open-file').addEventListener('click', async () => { try { const file = await window.client.openFile(); if (file) { setSourceValue(file.source); await saveDraft(); notice(`Đã mở ${file.name}.`); codeEditor?.focus(); } } catch (err) { notice(errorText(err), true); } });
  $('save-file').addEventListener('click', async () => { try { if (await window.client.saveFile(sourceValue(), $('language-select').value)) notice('Đã lưu tệp mã nguồn.'); } catch (err) { notice(errorText(err), true); } });
  $('search-code').addEventListener('click', () => { if (codeEditor) codeEditor.search(); else $('source-code').focus(); });
  $('run-btn').addEventListener('click', runLocal);
  $('submit-btn').addEventListener('click', submit);
  $('open-web').addEventListener('click', () => { if (state.selected) window.client.openSite(`/problems/${state.selected}`); });
  $('login-btn').addEventListener('click', () => state.account ? showView('account') : $('login-dialog').showModal());
  $('close-login').addEventListener('click', () => $('login-dialog').close());
  $('twofa-back').addEventListener('click', () => { $('twofa-form').hidden = true; $('login-form').hidden = false; state.twofaUser = null; });
  $('login-form').addEventListener('submit', async event => {
    event.preventDefault(); $('login-error').textContent = '';
    const button = $('login-submit'); setBusy(button, true, 'Đăng nhập');
    try {
      const data = await window.client.api({ kind: 'login', body: { username: $('username').value.trim(), password: $('password').value } });
      if (data.requires_2fa) { state.twofaUser = data.user_id; $('login-form').hidden = true; $('twofa-form').hidden = false; $('password').value = ''; $('twofa-code').focus(); return; }
      state.account = data.user; updateAccount(); $('login-dialog').close(); $('password').value = ''; notice(`Xin chào ${data.user.username}!`);
      if (state.view === 'submissions') showSubmissions();
      if (state.view === 'account') loadProfile();
    } catch (err) { $('login-error').textContent = errorText(err); }
    finally { setBusy(button, false, 'Đăng nhập'); }
  });
  $('twofa-form').addEventListener('submit', async event => {
    event.preventDefault(); $('twofa-error').textContent = '';
    const button = $('twofa-submit'); setBusy(button, true, 'Xác nhận');
    try {
      const data = await window.client.api({ kind: 'verify2fa', body: { user_id: state.twofaUser, code: $('twofa-code').value.trim() } });
      state.account = data.user; state.twofaUser = null; updateAccount(); $('login-dialog').close(); $('twofa-code').value = ''; $('twofa-form').hidden = true; $('login-form').hidden = false; notice(`Xin chào ${data.user.username}!`);
      if (state.view === 'account') loadProfile();
    } catch (err) { $('twofa-error').textContent = errorText(err); }
    finally { setBusy(button, false, 'Xác nhận'); }
  });
  loadLanguages();
  loadProblems();
}
init().catch(err => notice(errorText(err), true));
