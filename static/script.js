// 全局存储当前识别结果
let currentResults = [];
let currentStats = null;

// DOM引用
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const selectBtn = document.getElementById('selectBtn');
const fileList = document.getElementById('fileList');
const uploadBtn = document.getElementById('uploadBtn');
const progressSection = document.getElementById('progressSection');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statsSection = document.getElementById('statsSection');
const statsCount = document.getElementById('statsCount');
const resultSection = document.getElementById('resultSection');
const resultBody = document.getElementById('resultBody');
const exportExcelBtn = document.getElementById('exportExcelBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');
const clearBtn = document.getElementById('clearBtn');

let selectedFiles = [];

// 点击选择文件
selectBtn.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('click', () => fileInput.click());

// 拖拽上传
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  handleFiles(e.dataTransfer.files);
});

// 文件选择
fileInput.addEventListener('change', () => { handleFiles(fileInput.files); });

function handleFiles(files) {
  selectedFiles = Array.from(files);
  updateFileList();
  uploadBtn.disabled = selectedFiles.length === 0;
}

function updateFileList() {
  fileList.innerHTML = selectedFiles.map(f =>
    `<div class="file-item">📎 ${f.name} (${(f.size / 1024).toFixed(1)} KB)</div>`
  ).join('');
}

// 识别主流程
uploadBtn.addEventListener('click', async () => {
  if (selectedFiles.length === 0) return;

  progressSection.hidden = false;
  uploadBtn.disabled = true;
  resultSection.hidden = true;
  statsSection.hidden = true;

  const formData = new FormData();
  selectedFiles.forEach(f => formData.append('files', f));

  try {
    // 模拟进度（PaddleOCR无法提供真实进度）
    progressFill.style.width = '30%';
    progressText.textContent = '正在上传文件...';

    const resp = await fetch('/api/upload', { method: 'POST', body: formData });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || `服务器错误: ${resp.status}`);
    }

    progressFill.style.width = '80%';
    progressText.textContent = '识别完成，渲染结果...';

    const data = await resp.json();
    currentResults = data.results;
    currentStats = data.stats;

    // 渲染统计
    statsSection.hidden = false;
    statsCount.textContent = data.stats.total_unique_insured;

    // 渲染表格
    renderTable(data.results);
    resultSection.hidden = false;

    progressFill.style.width = '100%';
    progressText.textContent = `识别完成！共处理 ${data.results.length} 个文件`;
  } catch (err) {
    progressText.textContent = `❌ 错误：${err.message}`;
    progressText.style.color = '#d63031';
  } finally {
    uploadBtn.disabled = false;
    setTimeout(() => { progressSection.hidden = true; }, 3000);
  }
});

function renderTable(results) {
  const statusMap = {
    'ok': '✅ 正常',
    'not_policy': '⚠️ 非保单',
    'error': '❌ 错误',
    'low_confidence': '⚡ 低置信度'
  };

  resultBody.innerHTML = results.map(r => `
    <tr>
      <td>${escapeHtml(r.filename)}</td>
      <td class="status-${r.status}">${statusMap[r.status] || r.status}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_company || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.policy_type || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.policy_number || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.applicant || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insured || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.beneficiary || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.premium || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.payment_method || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.effective_date || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_period || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.sales_manager || '')}</td>
    </tr>
  `).join('');

  // 监听编辑事件，同步回内存数据
  document.querySelectorAll('td[contenteditable="true"]').forEach((td) => {
    td.addEventListener('blur', () => {
      const row = td.closest('tr');
      const rowIdx = Array.from(resultBody.children).indexOf(row);
      const colIdx = Array.from(row.children).indexOf(td) - 1; // 减去文件名列
      const fieldNames = ['insurance_company', 'policy_type', 'policy_number', 'applicant',
        'insured', 'beneficiary', 'premium', 'payment_method', 'effective_date',
        'insurance_period', 'sales_manager'];
      if (rowIdx >= 0 && colIdx >= 0 && colIdx < fieldNames.length) {
        currentResults[rowIdx].fields[fieldNames[colIdx]] = td.textContent.trim() || null;
      }
    });
  });
}

// 导出Excel
exportExcelBtn.addEventListener('click', async () => {
  if (!currentResults.length) return;
  try {
    const resp = await fetch('/api/export/excel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: currentResults, stats: currentStats }),
    });
    if (!resp.ok) throw new Error('导出失败');
    const blob = await resp.blob();
    downloadBlob(blob, '保单识别结果.xlsx');
  } catch (err) {
    alert('导出Excel失败：' + err.message);
  }
});

// 导出JSON
exportJsonBtn.addEventListener('click', async () => {
  if (!currentResults.length) return;
  try {
    const resp = await fetch('/api/export/json', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ results: currentResults, stats: currentStats }),
    });
    if (!resp.ok) throw new Error('导出失败');
    const blob = await resp.blob();
    downloadBlob(blob, '保单识别结果.json');
  } catch (err) {
    alert('导出JSON失败：' + err.message);
  }
});

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

// 清空
clearBtn.addEventListener('click', () => {
  currentResults = [];
  currentStats = null;
  selectedFiles = [];
  fileInput.value = '';
  updateFileList();
  uploadBtn.disabled = true;
  resultSection.hidden = true;
  statsSection.hidden = true;
  progressSection.hidden = true;
  resultBody.innerHTML = '';
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
