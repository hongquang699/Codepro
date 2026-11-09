(function () {
  'use strict';
  const contestKey = ContestAdminAPI.getContestKey();
  const api = (path, options) => ContestAdminAPI.antiCheat(contestKey, path, options);
  const byId = id => document.getElementById(id);
  let activeCase = null;
  let activeAppeal = null;
  let currentView = 'dashboard';
  const views = new Set(['dashboard', 'scans', 'similarity', 'groups', 'cases', 'ai-risk', 'penalties', 'appeals', 'settings', 'audit']);

  ContestAdminUI.renderSidebar('anti-cheat', contestKey);
  ContestAdminUI.renderHeader('Chống gian lận', 'Quét bài nộp, xem bằng chứng và xử lý hồ sơ nghi vấn');

  function notice(message, kind = '') {
    byId('acNotice').textContent = message;
    byId('acNotice').dataset.kind = kind;
  }

  function cell(row, value) {
    const td = row.insertCell();
    td.textContent = value === null || value === undefined ? '—' : String(value);
    return td;
  }

  function badge(row, status) {
    const td = row.insertCell();
    const span = document.createElement('span');
    span.className = 'ac-badge';
    span.dataset.status = status;
    span.textContent = status;
    td.appendChild(span);
  }

  function action(row, label, handler) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = label;
    button.addEventListener('click', handler);
    row.insertCell().appendChild(button);
  }

  function emptyRows(tbody, columns, message) {
    const row = tbody.insertRow();
    const td = row.insertCell();
    td.colSpan = columns;
    td.textContent = message;
  }

  function showView(name, shouldRefresh = true) {
    const view = views.has(name) ? name : 'dashboard';
    currentView = view;
    document.querySelectorAll('[data-ac-view]').forEach(section => {
      section.hidden = section.dataset.acView !== view;
    });
    document.querySelectorAll('[data-ac-tab]').forEach(button => {
      const selected = button.dataset.acTab === view;
      button.classList.toggle('active', selected);
      button.setAttribute('aria-selected', String(selected));
      if (selected) button.setAttribute('aria-current', 'page');
      else button.removeAttribute('aria-current');
    });
    if (window.location.hash.slice(1) !== view) history.replaceState(null, '', `#${view}`);
    if (shouldRefresh) refresh();
  }

  async function loadDashboard() {
    const data = await api('/dashboard');
    byId('acScanned').textContent = data.scanned_submissions;
    byId('acFlagged').textContent = data.flagged_submissions;
    byId('acHighRisk').textContent = `${data.high_risk_cases} hồ sơ ưu tiên cao (≥95%)`;
    byId('acScans').textContent = data.scans;
    byId('acPending').textContent = data.pending_scans;
    byId('acOpen').textContent = data.open_cases;
    byId('acConfirmed').textContent = data.confirmed_cases;
    byId('acEngineState').textContent = data.enabled ? 'Bot đang bật' : 'Bot đang tắt';
    byId('acEngineState').dataset.active = String(data.enabled);
    const latest = data.latest_scan;
    byId('acScanStatus').textContent = latest
      ? `Lượt mới nhất #${latest.id}: ${latest.status} · ${latest.processed}/${latest.total} bài · ${latest.matches} cặp nghi vấn`
      : 'Chưa có lượt quét nào.';
  }

  async function loadSimilarities() {
    const data = await api('/similarities');
    const tbody = byId('acSimilarityRows');
    const top = byId('acTopMatches');
    tbody.replaceChildren();
    top.replaceChildren();
    if (!data.similarities.length) {
      emptyRows(tbody, 6, 'Chưa có cặp mã nguồn vượt ngưỡng trong kỳ thi này.');
      top.textContent = 'Chưa có cặp nghi vấn.';
      return;
    }
    for (const item of data.similarities) {
      const row = tbody.insertRow();
      cell(row, `${item.user_a} ↔ ${item.user_b}`);
      cell(row, item.problem);
      cell(row, `#${item.submission_a} · #${item.submission_b}`);
      const score = cell(row, `${item.score.toFixed(2)}%`);
      score.className = 'ac-score';
      score.dataset.high = String(item.score >= 95);
      cell(row, item.algorithm_version);
      if (item.case_id) action(row, 'Xem hồ sơ', () => openEvidence({ id: item.case_id }));
      else cell(row, '—');
    }
    for (const item of data.similarities.slice(0, 3)) {
      const line = document.createElement('div');
      line.className = 'ac-top-match';
      const names = document.createElement('div');
      const title = document.createElement('strong');
      title.textContent = `${item.user_a} ↔ ${item.user_b}`;
      const problem = document.createElement('small');
      problem.textContent = `Bài ${item.problem}`;
      names.append(title, problem);
      const score = document.createElement('span');
      score.className = 'ac-score';
      score.dataset.high = String(item.score >= 95);
      score.textContent = `${item.score.toFixed(2)}%`;
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'ac-text-button';
      button.textContent = 'Xem →';
      button.addEventListener('click', () => item.case_id ? openEvidence({ id: item.case_id }) : showView('similarity'));
      line.append(names, score, button);
      top.appendChild(line);
    }
  }

  async function loadGroups() {
    const data = await api('/groups');
    const root = byId('acGroupList');
    root.replaceChildren();
    if (!data.groups.length) { root.textContent = 'Chưa có nhóm từ ba thí sinh trở lên.'; return; }
    data.groups.forEach((users, index) => {
      const group = document.createElement('div');
      group.className = 'ac-group';
      const title = document.createElement('strong');
      title.textContent = `Nhóm ${index + 1} · ${users.length} thí sinh`;
      const names = document.createElement('p');
      names.textContent = users.join(' · ');
      group.append(title, names);
      root.appendChild(group);
    });
  }

  async function loadPenalties() {
    const data = await api('/penalties');
    const tbody = byId('acPenaltyRows');
    tbody.replaceChildren();
    if (!data.penalties.length) return emptyRows(tbody, 7, 'Chưa có quyết định xử lý.');
    for (const item of data.penalties) {
      const row = tbody.insertRow();
      cell(row, `#${item.id}`);
      cell(row, `#${item.case_id}`);
      cell(row, item.user);
      cell(row, item.kind === 'DISQUALIFY' ? 'Loại khỏi kỳ thi' : 'Cảnh cáo');
      cell(row, item.issued_by);
      badge(row, item.revoked ? 'ĐÃ THU HỒI' : 'CÒN HIỆU LỰC');
      cell(row, new Date(item.created_at).toLocaleString('vi-VN'));
    }
  }

  async function loadAudit() {
    const data = await api('/audit');
    const tbody = byId('acAuditRows');
    tbody.replaceChildren();
    if (!data.audit.length) return emptyRows(tbody, 5, 'Chưa có hoạt động được ghi nhận.');
    for (const item of data.audit) {
      const row = tbody.insertRow();
      cell(row, new Date(item.created_at).toLocaleString('vi-VN'));
      cell(row, item.action.replaceAll('_', ' '));
      cell(row, item.actor);
      cell(row, item.target_type ? `${item.target_type} #${item.target_id}` : '—');
      cell(row, item.details || '—');
    }
  }

  async function loadScans() {
    const data = await api('/scans');
    const tbody = byId('acScanRows');
    tbody.replaceChildren();
    if (!data.scans.length) return emptyRows(tbody, 7, 'Chưa có lượt quét.');
    for (const scan of data.scans) {
      const row = tbody.insertRow();
      cell(row, `#${scan.id}`);
      cell(row, scan.target_submission ? `Bài nộp #${scan.target_submission}` : 'Toàn bộ kỳ thi');
      badge(row, scan.status);
      cell(row, `${scan.processed}/${scan.total}`);
      cell(row, scan.matches);
      cell(row, new Date(scan.created_at).toLocaleString('vi-VN'));
      if (scan.status === 'FAILED') {
        action(row, 'Thử lại', async () => {
          try {
            await api(`/scans/${scan.id}/retry`, { method: 'POST', body: '{}' });
            notice('Đã xếp lại lượt quét.', 'success');
            await refresh();
          } catch (error) { notice(error.message, 'error'); }
        });
      } else cell(row, scan.error || '');
    }
  }

  async function loadCases() {
    const status = byId('acCaseFilter').value;
    const data = await api(`/cases${status ? `?status=${encodeURIComponent(status)}` : ''}`);
    const tbody = byId('acCaseRows');
    tbody.replaceChildren();
    if (!data.cases.length) return emptyRows(tbody, 7, 'Chưa có hồ sơ nghi vấn.');
    for (const item of data.cases) {
      const row = tbody.insertRow();
      cell(row, `#${item.id}`);
      cell(row, item.problem);
      cell(row, `${item.user_a} · ${item.user_b}`);
      cell(row, `${item.score.toFixed(2)}%`);
      badge(row, item.status);
      cell(row, new Date(item.created_at).toLocaleString('vi-VN'));
      action(row, 'Xem bằng chứng', () => openEvidence(item));
    }
  }

  async function openEvidence(item) {
    try {
      const data = await api(`/cases/${item.id}/evidence`);
      activeCase = data.case;
      const caseInfo = data.case;
      byId('acEvidenceTitle').textContent = `Hồ sơ #${caseInfo.id} · ${caseInfo.problem} · ${caseInfo.score.toFixed(2)}%`;
      byId('acEvidenceMeta').textContent = `Thuật toán ${caseInfo.algorithm_version}; fingerprint chung: ${data.evidence.common_fingerprints}. ${data.source_unchanged ? 'Mã nguồn khớp bản đã quét.' : 'Mã nguồn đã thay đổi; cần quét lại.'}`;
      byId('acSourceAHeading').textContent = `${caseInfo.user_a} · bài nộp #${caseInfo.submission_a}`;
      byId('acSourceBHeading').textContent = `${caseInfo.user_b} · bài nộp #${caseInfo.submission_b}`;
      byId('acSourceA').textContent = data.source_a;
      byId('acSourceB').textContent = data.source_b;
      byId('acDecisionReason').value = '';
      const canDecide = ['OPEN', 'UNDER_REVIEW'].includes(caseInfo.status);
      byId('acConfirm').hidden = !canDecide;
      byId('acDismiss').hidden = !canDecide;
      byId('acPenaltySection').hidden = caseInfo.status !== 'CONFIRMED';
      const users = byId('acPenaltyUser');
      users.replaceChildren();
      for (const [id, name] of [[caseInfo.user_a_id, caseInfo.user_a], [caseInfo.user_b_id, caseInfo.user_b]]) {
        const option = document.createElement('option');
        option.value = String(id);
        option.textContent = name;
        users.appendChild(option);
      }
      byId('acEvidenceDialog').showModal();
    } catch (error) { notice(error.message, 'error'); }
  }

  async function decide(actionName) {
    if (!activeCase) return;
    const reason = byId('acDecisionReason').value.trim();
    if (reason.length < 10) return notice('Hãy ghi lý do ít nhất 10 ký tự.', 'error');
    try {
      await api(`/cases/${activeCase.id}/${actionName}`, { method: 'POST', body: JSON.stringify({ reason }) });
      byId('acEvidenceDialog').close();
      notice('Đã ghi quyết định và nhật ký kiểm toán.', 'success');
      await refresh();
    } catch (error) { notice(error.message, 'error'); }
  }

  async function issuePenalty() {
    if (!activeCase) return;
    const reason = byId('acDecisionReason').value.trim();
    if (reason.length < 10) return notice('Hãy ghi lý do xử lý ít nhất 10 ký tự.', 'error');
    try {
      await api(`/cases/${activeCase.id}/penalties`, { method: 'POST', body: JSON.stringify({
        kind: byId('acPenaltyKind').value, user_id: Number(byId('acPenaltyUser').value), reason
      }) });
      byId('acEvidenceDialog').close();
      notice('Đã ghi quyết định xử lý. Thí sinh có quyền khiếu nại.', 'success');
      await refresh();
    } catch (error) { notice(error.message, 'error'); }
  }

  async function loadSettings() {
    const data = await api('/settings');
    byId('acEnabled').checked = data.enabled;
    byId('acThreshold').value = data.similarity_threshold;
    byId('acMinTokens').value = data.min_tokens;
    byId('acScanMode').value = data.scan_mode;
  }

  async function loadAppeals() {
    const data = await api('/appeals');
    const tbody = byId('acAppealRows');
    tbody.replaceChildren();
    if (!data.appeals.length) return emptyRows(tbody, 6, 'Chưa có khiếu nại.');
    for (const item of data.appeals) {
      const row = tbody.insertRow();
      cell(row, `#${item.id}`);
      cell(row, `#${item.case_id}`);
      cell(row, item.appellant);
      cell(row, item.reason);
      badge(row, item.status);
      if (item.status !== 'OPEN') { cell(row, item.decision); continue; }
      action(row, 'Xét kháng nghị', () => {
        activeAppeal = item;
        byId('acAppealTitle').textContent = `Kháng nghị #${item.id} · hồ sơ #${item.case_id}`;
        byId('acAppealContext').textContent = `${item.appellant}: ${item.reason}`;
        byId('acAppealExplanation').value = '';
        byId('acAppealExplanation').setCustomValidity('');
        byId('acAppealError').textContent = '';
        byId('acAppealDialog').showModal();
      });
    }
  }

  async function resolveAppeal(decision) {
    if (!activeAppeal) return;
    const explanation = byId('acAppealExplanation').value.trim();
    if (explanation.length < 10) {
      byId('acAppealExplanation').setCustomValidity('Cần giải thích ít nhất 10 ký tự.');
      byId('acAppealExplanation').reportValidity();
      return;
    }
    byId('acAppealExplanation').setCustomValidity('');
    try {
      const result = await api(`/appeals/${activeAppeal.id}/resolve`, {
        method: 'POST', body: JSON.stringify({ decision, explanation })
      });
      byId('acAppealDialog').close();
      activeAppeal = null;
      notice(result.manual_reinstatement_required
        ? 'Đã chấp nhận kháng nghị. Hãy khôi phục tư cách thi đấu trong mục Thí sinh sau khi kiểm tra các quyết định khác.'
        : 'Đã xử lý kháng nghị.', 'success');
      await refresh();
    } catch (error) { byId('acAppealError').textContent = error.message; }
  }

  async function refresh() {
    const sectionLoaders = {
      dashboard: loadSimilarities,
      scans: loadScans,
      similarity: loadSimilarities,
      groups: loadGroups,
      cases: loadCases,
      penalties: loadPenalties,
      appeals: loadAppeals,
      settings: loadSettings,
      audit: loadAudit,
    };
    const jobs = [loadDashboard()];
    if (sectionLoaders[currentView]) jobs.push(sectionLoaders[currentView]());
    const results = await Promise.allSettled(jobs);
    const error = results.find(result => result.status === 'rejected');
    if (error) notice(`Một số dữ liệu chưa tải được: ${error.reason.message}`, 'error');
  }

  byId('acRefresh').addEventListener('click', refresh);
  document.querySelectorAll('[data-ac-tab]').forEach(button => button.addEventListener('click', () => showView(button.dataset.acTab)));
  document.querySelectorAll('[data-ac-go]').forEach(button => button.addEventListener('click', () => showView(button.dataset.acGo)));
  window.addEventListener('hashchange', () => showView(window.location.hash.slice(1)));
  byId('acCaseFilter').addEventListener('change', loadCases);
  byId('acStartScan').addEventListener('click', async () => {
    try {
      await api('/scans', { method: 'POST', body: '{}' });
      notice('Đã xếp lượt quét toàn bộ kỳ thi.', 'success');
      await refresh();
    } catch (error) { notice(error.message, 'error'); }
  });
  byId('acSettingsForm').addEventListener('submit', async event => {
    event.preventDefault();
    try {
      await api('/settings', { method: 'PATCH', body: JSON.stringify({
        enabled: byId('acEnabled').checked,
        similarity_threshold: Number(byId('acThreshold').value),
        min_tokens: Number(byId('acMinTokens').value),
        scan_mode: byId('acScanMode').value,
      }) });
      notice('Đã lưu chính sách quét.', 'success');
      await refresh();
    } catch (error) { notice(error.message, 'error'); }
  });
  byId('acCloseDialog').addEventListener('click', () => byId('acEvidenceDialog').close());
  byId('acConfirm').addEventListener('click', () => decide('confirm'));
  byId('acDismiss').addEventListener('click', () => decide('dismiss'));
  byId('acIssuePenalty').addEventListener('click', issuePenalty);
  byId('acCloseAppeal').addEventListener('click', () => byId('acAppealDialog').close());
  byId('acAppealApprove').addEventListener('click', () => resolveAppeal('UPHELD'));
  byId('acAppealReject').addEventListener('click', () => resolveAppeal('REJECTED'));
  byId('acAppealExplanation').addEventListener('input', () => byId('acAppealExplanation').setCustomValidity(''));
  showView(window.location.hash.slice(1), false);
  refresh();
  setInterval(() => {
    if (!document.hidden && !byId('acEvidenceDialog').open && !byId('acAppealDialog').open) refresh();
  }, 30000);
})();
