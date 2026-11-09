(() => {
  const root = '/admin/judge';
  const apiRoot = '/api/v1/admin/judge';
  const content = document.getElementById('content');
  const parts = location.pathname.slice(root.length).split('/').filter(Boolean);
  const section = parts[0] || 'dashboard';
  const h = value => String(value ?? '—').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const link = (path, label) => `<a href="${root}/${h(path)}">${h(label)}</a>`;
  const badge = value => `<span class="badge ${h(String(value || '').toUpperCase())}">${h(value || '—')}</span>`;
  const date = value => value ? new Date(value).toLocaleString('vi-VN') : '—';
  const table = (headers, rows) => `<div class="panel"><table class="table"><thead><tr>${headers.map(x => `<th>${h(x)}</th>`).join('')}</tr></thead><tbody>${rows.length ? rows.map(row => `<tr>${row.map(cell => `<td>${cell}</td>`).join('')}</tr>`).join('') : `<tr><td colspan="${headers.length}" class="empty">Chưa có dữ liệu</td></tr>`}</tbody></table></div>`;
  const tabs = items => `<div class="tabs">${items.map(([path,label]) => `<a class="${location.pathname === root+'/'+path ? 'active':''}" href="${root}/${path}">${h(label)}</a>`).join('')}</div>`;
  const button = (label, action, id='', klass='secondary') => `<button class="${klass}" data-action="${h(action)}" data-id="${h(id)}">${h(label)}</button>`;
  const title = (name, description='') => `<h1>${h(name)}</h1><p class="muted">${h(description)}</p>`;
  const cards = items => `<div class="cards">${items.map(([name,value]) => `<div class="card"><span class="muted">${h(name)}</span><strong>${h(value)}</strong></div>`).join('')}</div>`;
  const toast = (message, bad=false) => { const el=document.getElementById('toast'); el.textContent=message; el.style.background=bad?'#7d2c3d':'#25476d'; el.style.display='block'; setTimeout(()=>el.style.display='none',4500); };
  const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/)||[])[1] || '';

  async function request(path, method='GET', body) {
    const token = localStorage.getItem('token');
    const response = await fetch(apiRoot + path, {
      method, credentials:'same-origin',
      headers:{Accept:'application/json', ...(token?{Authorization:`Token ${token}`} : {}),
        ...(method!=='GET'?{'Content-Type':'application/json','X-CSRFToken':decodeURIComponent(csrf())}: {})},
      ...(body?{body:JSON.stringify(body)}:{})
    });
    let result={}; try { result=await response.json(); } catch (_) {}
    if (!response.ok) throw Object.assign(new Error(result.error || result.detail || `HTTP ${response.status}`),{status:response.status});
    return result;
  }

  async function dashboard() {
    const d=await request('/dashboard');
    content.innerHTML=title('Judge System','Trạng thái thực tế từ Judge Manager và các bài chấm gần đây.')+
      cards([['Workers',d.workers.length],['Queue',d.queue.length],['Running',d.running],['Errors today',d.errors_today]])+
      `<div class="toolbar"><h2>Worker status</h2>${link('workers','Xem tất cả workers →')}</div>`+
      table(['Worker','CPU','RAM','Job','Status'],d.workers.map(w=>[link(`workers/${encodeURIComponent(w.id)}`,w.name),h(w.cpu==null?'—':w.cpu+'%'),h(w.ram==null?'—':w.ram+'%'),h(w.current_job),badge(w.status)]))+
      `<p class="muted">Queue: ${h(d.queue.length)} đang chờ · ${d.paused?'Đang tạm dừng':'Đang hoạt động'}</p>`;
  }

  async function workers() {
    const d=await request('/workers');
    if(parts[1] && parts[1]!=='create') return workerDetail(decodeURIComponent(parts[1]));
    content.innerHTML=title('Workers','Danh sách node, heartbeat và chính sách nhận job.')+
      `<div class="toolbar"><span>${h(d.workers.length)} worker đã ghi nhận</span>${link('workers/create','Đăng ký worker')}</div>`+
      table(['ID','Hostname / IP','OS','CPU','RAM','Disk','Languages','Current job','Status','Heartbeat'],d.workers.map(w=>[
        link(`workers/${encodeURIComponent(w.id)}`,w.id),h(w.hostname)+'<br>'+h(w.ip_address),h(w.os),h(w.cpu==null?'—':w.cpu+'%'),
        h(w.ram==null?'—':w.ram+'%'),h(w.disk==null?'—':w.disk+'%'),h(w.supported_languages.join(', ')),h(w.current_job),badge(w.status),h(w.last_seen_sec_ago==null?'—':w.last_seen_sec_ago+'s')
      ]));
    if(parts[1]==='create') content.innerHTML=title('Đăng ký worker','Worker được khai báo trong judge-system/config/workers.yml và tự đăng ký bằng heartbeat.')+
      '<div class="panel"><p>Thêm cấu hình worker trên Judge Manager, khởi động worker bằng supervisor, sau đó làm mới danh sách. Trang web không khởi chạy process trên máy chấm.</p></div>';
  }

  async function workerDetail(id) {
    const w=await request('/workers/'+encodeURIComponent(id));
    const sub=parts[2]||'detail';
    content.innerHTML=title(`Worker: ${w.name}`,`ID ${w.id} · ${w.hostname} · ${w.ip_address||'IP chưa có'}`)+
      tabs([[`workers/${encodeURIComponent(id)}`,'Chi tiết'],[`workers/${encodeURIComponent(id)}/logs`,'Logs'],[`workers/${encodeURIComponent(id)}/edit`,'Cấu hình']])+
      (sub==='logs' ? table(['Thời gian','Mức','Thao tác','Nội dung'],(w.logs||[]).map(x=>[h(date(x.created_at)),badge(x.level),h(x.action),h(x.message)])) + `<div id="worker-file-log" class="panel"><h2>Worker log</h2><p class="muted">Đang tải…</p></div>` :
       sub==='edit' ? '<div class="panel">Tên, giới hạn tài nguyên và ngôn ngữ của worker được quản lý trên Judge Manager. Chỉnh trong workers.yml rồi khởi động lại worker bằng supervisor.</div>' :
       cards([['Status',w.status],['CPU',w.cpu==null?'—':w.cpu+'%'],['RAM',w.ram==null?'—':w.ram+'%'],['Disk',w.disk==null?'—':w.disk+'%'],['Current job',w.current_job||'—']])+
       `<div class="panel"><h2>Supported languages</h2><p>${h(w.supported_languages.join(', ')||'Chưa báo cáo')}</p>${w.error?`<p class="error">${h(w.error)}</p>`:''}<div class="actions">${button('Enable','worker-enable',id)}${button('Maintenance','worker-maintenance',id)}${button('Disable','worker-disable',id,'danger')}${button('Restart','worker-restart',id)}</div></div>`);
    if(sub==='logs') {
      const d=await request('/logs?source=worker&worker_id='+encodeURIComponent(id));
      document.getElementById('worker-file-log').innerHTML=`<h2>Worker log</h2><pre>${h(d.system_logs.join('\n')||'Chưa có log')}</pre>`;
    }
  }

  async function queue() {
    const d=await request('/queue'); const filter=parts[1]||'all';
    const rows=filter==='pending'?d.jobs.filter(x=>x.status==='WAITING'):filter==='running'?d.jobs.filter(x=>x.status==='Judging'):filter==='completed'?d.jobs.filter(x=>x.status==='Completed'):filter==='failed'?d.jobs.filter(x=>['Failed','Cancelled'].includes(x.status)):d.jobs;
    content.innerHTML=title('Queue',`Judge Manager ${d.paused?'đang tạm dừng':'đang nhận job'}.`)+
      tabs([['queue','Tất cả'],['queue/pending','Waiting'],['queue/running','Running'],['queue/completed','Completed'],['queue/failed','Failed']])+
      `<div class="toolbar"><span>${h(rows.length)} job</span><div class="actions">${button('Pause Queue','queue-pause')}${button('Resume Queue','queue-resume')}</div></div>`+
      table(['Priority','Submission / Job','User','Problem','Contest','Language','Submitted','Waiting','Worker','Status','Actions'],rows.map(j=>[
        h(j.priority),h(j.submission_id||j.job_id),h(j.user),h(j.problem_code),h(j.contest),h(j.language),h(j.submitted_at?date(j.submitted_at*1000):'—'),
        h(j.waiting_seconds==null?'—':j.waiting_seconds+'s'),h(j.assigned_worker),badge(j.status),j.status==='WAITING'?button('Cancel','job-cancel',j.job_id,'danger'):['Failed','Cancelled'].includes(j.status)?button('Retry','job-retry',j.job_id):''
      ]));
  }

  async function submissions() {
    if(parts[1] && /^\d+$/.test(parts[1])) return submissionDetail(Number(parts[1]));
    const d=await request('/submissions');
    content.innerHTML=title('Submissions','100 bài nộp gần nhất.')+
      table(['ID','User','Problem','Contest','Language','Status','Verdict','Score','Time','Submitted'],d.submissions.map(s=>[
        link(`submissions/${s.id}`,'#'+s.id),h(s.user),h(s.problem),h(s.contest),h(s.language),badge(s.status),badge(s.verdict),h(s.score),h(s.time_ms+' ms'),h(date(s.submitted_at))
      ]));
  }

  async function submissionDetail(id) {
    const s=await request('/submissions/'+id);
    content.innerHTML=title(`Submission #${s.id}`,`${s.user} · ${s.problem} · ${s.language}`)+
      cards([['Status',s.status],['Verdict',s.verdict||'—'],['Score',s.score??'—'],['Time',s.time_ms+' ms'],['Memory',s.memory_kb==null?'—':s.memory_kb+' KB']])+
      `<div class="actions">${button('Rejudge','rejudge',id)}${button('View Source','source',id)}${button('View Logs','submission-logs',id)}</div>`+
      table(['Testcase','Verdict','Time','Memory','Points','Feedback'],s.testcases.map(t=>[h(t.case),badge(t.verdict),h(t.time_ms+' ms'),h(t.memory_kb+' KB'),h(t.points),h(t.feedback)]))+
      `<div id="submission-extra" class="panel" hidden></div>`;
    content.dataset.source=s.source||'';
    content.dataset.logs=s.error||'';
  }

  async function languages() {
    const d=await request('/languages');
    if(parts[1]==='create') {
      content.innerHTML=title('Thêm ngôn ngữ','Tạo metadata ngôn ngữ trong Django. Compiler phải được cấu hình trên Judge Manager.')+
        '<form id="language-form" class="panel"><label>Key</label><input name="key" required maxlength="20"><label>Tên</label><input name="name" required maxlength="50"><label>Tên ngắn</label><input name="short_name"><label>Tên chung</label><input name="common_name"><p><button>Tạo ngôn ngữ</button></p></form>'; return;
    }
    if(parts[1]==='edit') {
      const lang=d.languages.find(x=>x.id===Number(parts[2]));
      if(!lang) throw new Error('Language not found');
      content.innerHTML=title(`Sửa ${lang.name}`)+`<form id="language-form" data-id="${lang.id}" class="panel"><label>Tên</label><input name="name" value="${h(lang.name)}" required><label>Tên ngắn</label><input name="short_name" value="${h(lang.short_name)}"><label>Active</label><input type="checkbox" name="is_active" ${lang.is_active?'checked':''}><p><button>Lưu</button></p></form>`; return;
    }
    content.innerHTML=title('Languages','Ngôn ngữ bật trong Django; cấu hình compiler thuộc Judge Manager.')+
      `<div class="toolbar">${link('languages/create','+ Thêm ngôn ngữ')}</div>`+
      table(['Key','Name','Short name','Active',''],d.languages.map(x=>[h(x.key),h(x.name),h(x.short_name),badge(x.is_active?'YES':'NO'),link(`languages/edit/${x.id}`,'Sửa')]));
  }

  async function monitoring() {
    const d=await request('/monitoring'); const metric=parts[1]||'cpu';
    content.innerHTML=title('Monitoring','Số liệu tài nguyên do worker báo qua heartbeat.')+
      tabs([['monitoring/cpu','CPU'],['monitoring/memory','Memory'],['monitoring/disk','Disk'],['monitoring/network','Network']])+
      table(['Worker','Status',metric.toUpperCase()],d.workers.map(w=>[link(`workers/${encodeURIComponent(w.id)}`,w.name),badge(w.status),h(metric==='cpu'?w.cpu==null?'Chưa báo cáo':w.cpu+'%':metric==='memory'?w.ram==null?'Chưa báo cáo':w.ram+'%':metric==='disk'?w.disk==null?'Chưa báo cáo':w.disk+'%':w.network_rx_kbps==null?'Chưa báo cáo':`↓ ${w.network_rx_kbps} KB/s · ↑ ${w.network_tx_kbps} KB/s`)]));
  }

  async function logs() {
    const filter=parts[1]==='error'?'?level=ERROR':parts[1]==='worker'?'?source=worker':''; const d=await request('/logs'+filter);
    content.innerHTML=title('Logs','Audit log và lỗi chấm được lưu trong cơ sở dữ liệu.')+
      tabs([['logs','Tất cả'],['logs/worker','Worker'],['logs/judge','Judge'],['logs/error','Errors']])+
      table(['Thời gian','Mức','Actor','Action','Worker','Job','Message'],d.logs.filter(x=>parts[1]==='worker'?x.worker:parts[1]==='judge'?x.job:true).map(x=>[
        h(date(x.created_at)),badge(x.level),h(x.actor),h(x.action),h(x.worker),h(x.job),h(x.message)
      ]))+`<div class="panel"><h2>Judge Manager log</h2><pre>${h(d.system_logs.join('\n')||'Chưa có log')}</pre></div>`;
  }

  async function info() {
    const name=section==='test'?'Test Runner':section==='sandbox'?'Sandbox':'Settings';
    const detail=section==='test'?'Chạy thử mã chỉ được thực hiện trong sandbox của Judge Worker.':section==='sandbox'?'Giới hạn chạy và chính sách cách ly được cấu hình trên Judge Manager.':'Cấu hình vận hành được quản lý trên Judge Manager.';
    const choices=section==='test'?[['test','Tổng quan'],['test/run','Run']]:section==='sandbox'?[['sandbox','Tổng quan'],['sandbox/policies','Policies']]:[['settings','Tổng quan'],['settings/limits','Limits'],['settings/security','Security'],['settings/maintenance','Maintenance']];
    if(section==='test' && parts[1]==='run') {
      const d=await request('/languages');
      content.innerHTML=title(name,detail)+tabs(choices)+`<form id="test-run-form" class="panel"><label>Mã bài toán</label><input name="problem" required maxlength="20"><label>Ngôn ngữ</label><select name="language">${d.languages.filter(x=>x.is_active).map(x=>`<option value="${h(x.key)}">${h(x.name)}</option>`).join('')}</select><label>Mã nguồn thử</label><textarea name="source" required rows="16" style="width:100%"></textarea><p><button>Đưa vào sandbox</button></p><p id="test-result" class="muted"></p></form>`;
      return;
    }
    if(section==='test') {
      content.innerHTML=title(name,detail)+tabs(choices)+`<div class="panel"><h2>Kiểm tra máy chấm</h2><p>Chọn một bài toán đã có testcase rồi gửi mã nguồn qua Judge Manager. Kết quả xuất hiện trong Queue.</p>${link('test/run','Mở Test Runner →')}</div>`;
      return;
    }
    if(section==='sandbox' || parts[1]==='limits') {
      const d=await request('/limits');
      const limits=d.limits||{};
      const rows=Object.entries(limits).flatMap(([group,values])=>Object.entries(values||{}).map(([key,value])=>[h(group),h(key),h(value)]));
      content.innerHTML=title(name,detail)+tabs(choices)+table(['Nhóm','Giới hạn','Giá trị'],rows);
      return;
    }
    if(parts[1]==='maintenance') {
      const d=await request('/queue');
      content.innerHTML=title(name,detail)+tabs(choices)+cards([['Queue',d.paused?'PAUSED':'RUNNING'],['Waiting',d.jobs.filter(x=>x.status==='WAITING').length]])+
        `<div class="panel"><p>Tạm dừng chỉ ngăn cấp job mới. Job đang chấm tiếp tục hoàn tất.</p><div class="actions">${button('Pause Queue','queue-pause')}${button('Resume Queue','queue-resume')}</div></div>`;
      return;
    }
    if(parts[1]==='security') {
      content.innerHTML=title(name,detail)+tabs(choices)+`<div class="panel"><h2>Chính sách truy cập</h2><p>Chỉ staff, superuser, Judge Admin và Judge Manager được gọi API quản trị. Thao tác bằng cookie cần CSRF. Mọi lệnh vận hành đi qua Judge Manager và được ghi vào audit log.</p></div>`;
      return;
    }
    const health=await request('/health');
    content.innerHTML=title(name,detail)+tabs(choices)+cards([['Manager',health.status],['Queue',health.queue_size],['Completed cache',health.completed_results]])+
      `<div class="panel"><p>Cấu hình triển khai nằm trong <code>judge-system/config</code>.</p></div>`;
  }

  async function init() {
    document.querySelectorAll('.side a').forEach(a=>a.classList.toggle('active',a.pathname===root+(section==='dashboard'?'':'/'+section)));
    try {
      const access=await request('/access');
      document.getElementById('user-label').textContent=`${access.username} · ${access.role}`;
      const routes={dashboard,workers,queue,submissions,languages,monitoring,logs,test:info,sandbox:info,settings:info};
      await (routes[section]||dashboard)();
    } catch (err) {
      if(err.status===401){location.href='/login?next='+encodeURIComponent(location.pathname);return;}
      content.innerHTML=title('Không thể tải Judge Admin')+`<div class="panel error">${h(err.status===403?'Tài khoản không có quyền Judge Admin / Judge Manager.':err.message)}</div>`;
    }
  }

  content.addEventListener('click',async event=>{
    const el=event.target.closest('button[data-action]'); if(!el) return;
    const action=el.dataset.action,id=el.dataset.id;
    if(action==='source'||action==='submission-logs'){
      const target=document.getElementById('submission-extra'); target.hidden=false;
      target.innerHTML=`<h2>${action==='source'?'Source':'Logs'}</h2><pre>${h(action==='source'?content.dataset.source:content.dataset.logs)}</pre>`;return;
    }
    if(['worker-disable','worker-restart','job-cancel','rejudge'].includes(action) && !confirm(`Xác nhận ${action} ${id}?`)) return;
    el.disabled=true;
    try {
      let path;
      if(action.startsWith('worker-')) path=`/workers/${encodeURIComponent(id)}/${action.slice(7)}`;
      else if(action.startsWith('queue-')) path=`/queue/${action.slice(6)}`;
      else if(action==='job-cancel'||action==='job-retry') path=`/queue/${encodeURIComponent(id)}/${action.slice(4)}`;
      else if(action==='rejudge') path=`/submissions/${encodeURIComponent(id)}/rejudge`;
      else return;
      await request(path,'POST');toast('Thao tác đã được Judge Manager ghi nhận.');await init();
    } catch(err){toast(err.message,true);} finally{el.disabled=false;}
  });

  content.addEventListener('submit',async event=>{
    if(event.target.id==='test-run-form'){
      event.preventDefault();
      try {
        const result=await request('/test/run','POST',Object.fromEntries(new FormData(event.target)));
        document.getElementById('test-result').innerHTML=`Job ${h(result.job_id)} đã vào hàng đợi. ${link('queue','Xem Queue →')}`;
      } catch(err){toast(err.message,true);}
      return;
    }
    if(event.target.id!=='language-form') return;event.preventDefault();
    const form=event.target,data=Object.fromEntries(new FormData(form));
    if(form.dataset.id) data.is_active=form.elements.is_active.checked;
    try { await request(form.dataset.id?`/languages/${form.dataset.id}`:'/languages',form.dataset.id?'PATCH':'POST',data);location.href=root+'/languages'; }
    catch(err){toast(err.message,true);}
  });
  init();
})();
