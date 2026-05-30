// API配置
const API_BASE = '';

// 状态
let uploadedFileId = null;
let currentResults = null;

// DOM元素
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statsSection = document.getElementById('statsSection');
const resultSection = document.getElementById('resultSection');
const resultBody = document.getElementById('resultBody');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const clearBtn = document.getElementById('clearBtn');
const detailModal = document.getElementById('detailModal');
const modalTitle = document.getElementById('modalTitle');
const modalBody = document.getElementById('modalBody');
const modalCloseBtn = document.getElementById('modalCloseBtn');

// 文件选择
selectBtn.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

fileInput.addEventListener('change', (e) => {
  handleFiles(e.target.files);
});

function handleFiles(files) {
  if (!files || files.length === 0) {
    fileList.innerHTML = '';
    uploadBtn.disabled = true;
    return;
  }

  const fileArray = Array.from(files);
  fileList.innerHTML = fileArray.map(f => `
    <div class="file-item">
      📄 ${escapeHtml(f.name)} <span class="file-size">(${formatSize(f.size)})</span>
    </div>
  `).join('');

  document.getElementById('fileCountBadge').textContent = `${fileArray.length} 个文件`;
  uploadBtn.disabled = false;

  uploadBtn.onclick = async () => {
    await uploadAndRecognize(files);
  };
}

async function uploadAndRecognize(files) {
  progressSection.hidden = false;
  progressFill.style.width = '0%';
  progressText.textContent = '正在上传文件...';
  uploadBtn.disabled = true;

  try {
    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append('files', files[i]);
    }

    progressFill.style.width = '30%';
    progressText.textContent = '正在识别文件...';

    const response = await fetch(`${API_BASE}/api/upload`, {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || '上传失败');
    }

    progressFill.style.width = '90%';
    progressText.textContent = '正在处理结果...';

    currentResults = await response.json();

    renderStats(currentResults.stats);
    renderResultsTable(currentResults.results);

    // 结果显示后进入紧凑布局
    document.body.classList.add('has-results');

    progressFill.style.width = '100%';
    progressText.textContent = '识别完成';

    setTimeout(() => {
      progressSection.hidden = true;
    }, 1000);

  } catch (error) {
    progressFill.style.width = '100%';
    progressFill.style.background = '#e74c3c';
    progressText.textContent = `错误: ${error.message}`;
  } finally {
    uploadBtn.disabled = false;
  }
}

function renderStats(stats) {
  statsSection.hidden = false;
  document.getElementById('totalFiles').textContent = stats.total_files;
  document.getElementById('sensitiveFiles').textContent = stats.sensitive_files;
  document.getElementById('globalPersons').textContent = stats.global_unique_persons;

  // 人身险涉敏
  document.getElementById('lifeStats').textContent = stats.life_sensitive_files;
  document.getElementById('lifeStatsLabel').textContent = '人身险涉敏文件';
  document.getElementById('lifePersonsHint').textContent = `${stats.life_unique_persons} 涉敏人数`;

  // 财产险
  document.getElementById('propertyStats').textContent = stats.property_files;
  document.getElementById('propertyStatsLabel').textContent = '财产险文件总数';
  document.getElementById('propertyPersonsHint').textContent = `${stats.property_sensitive_persons} 涉敏人数`;

  // 异常文件
  document.getElementById('anomalyFiles').textContent = stats.anomaly_files;
}

function renderResultsTable(results) {
  resultSection.hidden = false;

  const statusMap = {
    'ok': '✅ 是',
    'no_pii': '⚠️ 无个人信息',
    'not_insurance': '❌ 非保险文档',
    'error': '❌ 错误'
  };

  resultBody.innerHTML = results.map((r, idx) => {
    const personsSummary = r.persons && r.persons.length > 0
      ? r.persons.map(p => `${p.name || '(匿名)'}(${p.role_display})`).join('<br>')
      : '-';

    const anomalyHtml = r.anomaly
      ? `<span class="anomaly-badge">${escapeHtml(r.anomaly)}</span>`
      : '-';

    return `
      <tr${r.anomaly ? ' class="row-anomaly"' : ''}>
        <td>${escapeHtml(r.filename)}</td>
        <td>${escapeHtml(r.document_type_display)}</td>
        <td>${escapeHtml(r.insurance_category_display)}</td>
        <td>${escapeHtml(r.insurance_branch_display || '未知')}</td>
        <td>${escapeHtml(r.insurance_company)}</td>
        <td>${anomalyHtml}</td>
        <td>${r.sensitive_count}</td>
        <td>${personsSummary}</td>
        <td><button class="btn-detail" onclick="showDetail(${idx})">查看</button></td>
      </tr>
    `;
  }).join('');
}

function showDetail(idx) {
  const result = currentResults.results[idx];
  modalTitle.textContent = `文件详情 — ${result.filename}`;

  let personsHtml = '';
  if (result.persons && result.persons.length > 0) {
    personsHtml = '<h4>涉敏人员</h4><div class="persons-list">';
    result.persons.forEach((p, i) => {
      personsHtml += `
        <div class="person-card">
          <div class="person-header">
            <strong>${escapeHtml(p.name || '(匿名)')}</strong>
            <span class="role-badge">${escapeHtml(p.role_display)}</span>
          </div>
          ${p.details && p.details.length > 0 ? `
            <ul class="pii-list">
              ${p.details.map(d => `
                <li><span class="pii-label">${escapeHtml(d.raw_label || d.type)}:</span> ${escapeHtml(d.value)}</li>
              `).join('')}
            </ul>
          ` : '<p class="no-pii">仅姓名</p>'}
        </div>
      `;
    });
    personsHtml += '</div>';
  } else {
    personsHtml = '<p class="no-persons">无涉敏人员</p>';
  }

  modalBody.innerHTML = `
    <div class="detail-summary">
      <p><strong>文件名:</strong> ${escapeHtml(result.filename)}</p>
      <p><strong>文档类型:</strong> ${escapeHtml(result.document_type_display)}</p>
      <p><strong>险种类别:</strong> ${escapeHtml(result.insurance_category_display)}</p>
      <p><strong>险种大类:</strong> ${escapeHtml(result.insurance_branch_display || '未知')}</p>
      <p><strong>保险公司:</strong> ${escapeHtml(result.insurance_company)}</p>
      ${result.policy_number ? `<p><strong>保单号:</strong> ${escapeHtml(result.policy_number)}</p>` : ''}
      ${result.anomaly ? `<p class="anomaly-warning"><strong>异常标记:</strong> ${escapeHtml(result.anomaly)}</p>` : ''}
    </div>
    <hr>
    ${personsHtml}
    <hr>
    <details class="raw-text-section">
      <summary>识别原文（点击展开）</summary>
      <pre class="ocr-raw-text">${escapeHtml(result.raw_text || '无识别结果')}</pre>
    </details>
  `;

  detailModal.classList.add('open');
}

// 关闭详情抽屉
modalCloseBtn.addEventListener('click', () => {
  detailModal.classList.remove('open');
});

detailModal.addEventListener('click', (e) => {
  if (e.target === detailModal) {
    detailModal.classList.remove('open');
  }
});

// 导出功能
exportExcelBtn.addEventListener('click', async () => {
  if (!currentResults) return;

  try {
    const response = await fetch(`${API_BASE}/api/export/excel`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentResults)
    });

    if (!response.ok) throw new Error('导出失败');

    const blob = await response.blob();
    downloadBlob(blob, '保险涉敏信息识别结果.xlsx');
  } catch (error) {
    alert(`导出失败: ${error.message}`);
  }
});

exportJsonBtn.addEventListener('click', async () => {
  if (!currentResults) return;

  try {
    const response = await fetch(`${API_BASE}/api/export/json`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(currentResults)
    });

    if (!response.ok) throw new Error('导出失败');

    const blob = await response.blob();
    downloadBlob(blob, '保险涉敏信息识别结果.json');
  } catch (error) {
    alert(`导出失败: ${error.message}`);
  }
});

// 清空
clearBtn.addEventListener('click', () => {
  uploadedFileId = null;
  currentResults = null;
  fileInput.value = '';
  fileList.innerHTML = '';
  document.getElementById('fileCountBadge').textContent = '0 个文件';
  uploadBtn.disabled = true;
  progressSection.hidden = true;
  statsSection.hidden = true;
  resultSection.hidden = true;
});

// 工具函数
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
