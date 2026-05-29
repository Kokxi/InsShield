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
const sensitiveStatsCount = document.getElementById('sensitiveStatsCount');
const lifeStatsCount = document.getElementById('lifeStatsCount');
const propertyStatsCount = document.getElementById('propertyStatsCount');
const unknownStatsCount = document.getElementById('unknownStatsCount');
const totalStatsCount = document.getElementById('totalStatsCount');
const resultSection = document.getElementById('resultSection');
const applicantBody = document.getElementById('applicantBody');
const insuredBody = document.getElementById('insuredBody');
const policyInfoBody = document.getElementById('policyInfoBody');
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

// 险种类型中文名映射
const CATEGORY_NAMES = {
  'life': '人寿险',
  'health': '健康险',
  'accident': '意外险',
  'car': '车险',
  'property': '财产险',
  'unknown': '未知'
};

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
    renderStats(data.stats, data.results.length);

    // 渲染三张表格
    renderPolicyInfoTable(data.results);
    renderApplicantTable(data.results);
    renderInsuredTable(data.results);
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

function renderStats(stats, totalCount) {
  statsSection.hidden = false;
  sensitiveStatsCount.textContent = stats.sensitive_info_count;
  lifeStatsCount.textContent = stats.life_insured_count;
  propertyStatsCount.textContent = stats.property_count;
  unknownStatsCount.textContent = stats.unknown_count;
  totalStatsCount.textContent = totalCount;
}

function getCategory(category) {
  return CATEGORY_NAMES[category] || '未知';
}

function buildPolicyDetails(fields) {
  const parts = [];
  if (fields.insurance_company) parts.push(`保险公司: ${fields.insurance_company}`);
  if (fields.policy_type) parts.push(`险种: ${fields.policy_type}`);
  if (fields.policy_number) parts.push(`保单号: ${fields.policy_number}`);
  if (fields.applicant) parts.push(`投保人: ${fields.applicant}`);
  if (fields.insured) parts.push(`被保人: ${fields.insured}`);
  if (fields.beneficiary) parts.push(`受益人: ${fields.beneficiary}`);
  if (fields.premium) parts.push(`保费: ${fields.premium}`);
  if (fields.payment_method) parts.push(`交费方式: ${fields.payment_method}`);
  if (fields.effective_date) parts.push(`生效日期: ${fields.effective_date}`);
  if (fields.insurance_period) parts.push(`保险期间: ${fields.insurance_period}`);
  if (fields.sales_manager) parts.push(`销售经理: ${fields.sales_manager}`);
  return parts.join(' | ');
}

// 渲染保单信息表（所有 is_policy=true 的文件）
function renderPolicyInfoTable(results) {
  policyInfoBody.innerHTML = results
    .filter(r => r.is_policy)
    .map(r => `
      <tr>
        <td>${escapeHtml(r.filename)}</td>
        <td>${getCategory(r.fields.insurance_category)}</td>
        <td>${escapeHtml(r.fields.insurance_company || '')}</td>
        <td class="status-ok">✅ 有效</td>
        <td class="policy-detail">${escapeHtml(buildPolicyDetails(r.fields))}</td>
      </tr>
    `).join('');
}

// 渲染投保人信息表（所有状态为ok的保单，每文件一行）
function renderApplicantTable(results) {
  const statusMap = {
    'ok': '✅ 正常',
    'not_policy': '⚠️ 非保单',
    'error': '❌ 错误',
    'low_confidence': '⚡ 低置信度'
  };

  applicantBody.innerHTML = results.map((r, idx) => `
    <tr>
      <td>${escapeHtml(r.filename)}</td>
      <td class="status-${r.status}">${statusMap[r.status] || r.status}</td>
      <td>${r.status === 'ok' ? getCategory(r.fields.insurance_category) : ''}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_company || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.applicant || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.policy_number || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.premium || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.payment_method || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.effective_date || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.insurance_period || '')}</td>
      <td contenteditable="${r.status === 'ok'}">${escapeHtml(r.fields.sales_manager || '')}</td>
    </tr>
  `).join('');

  // 编辑监听
  const fieldNames = ['insurance_company', 'applicant', 'policy_number',
    'premium', 'payment_method', 'effective_date', 'insurance_period', 'sales_manager'];
  document.querySelectorAll('#applicantTable td[contenteditable="true"]').forEach((td) => {
    td.addEventListener('blur', () => {
      const row = td.closest('tr');
      const rowIdx = Array.from(applicantBody.children).indexOf(row);
      const colIdx = Array.from(row.children).indexOf(td) - 3; // 减去文件名、状态、险种类型列
      if (rowIdx >= 0 && colIdx >= 0 && colIdx < fieldNames.length) {
        currentResults[rowIdx].fields[fieldNames[colIdx]] = td.textContent.trim() || null;
      }
    });
  });
}

// 渲染被保人信息表（仅人身险，被保人多人时拆行）
function renderInsuredTable(results) {
  const lifeCategories = ['life', 'health', 'accident'];
  const rows = [];

  results.forEach((r) => {
    if (r.status !== 'ok') return;
    const cat = r.fields.insurance_category;
    if (!lifeCategories.includes(cat)) return;

    // 拆分多个被保人
    let insuredNames = [];
    if (r.fields.insured) {
      const text = r.fields.insured.replace(/,/g, '，').replace(/、/g, '，');
      insuredNames = text.split('，').map(n => n.trim()).filter(n => n);
    }
    if (insuredNames.length === 0) {
      insuredNames = ['']; // 至少一行
    }

    insuredNames.forEach((name) => {
      rows.push({
        applicant: r.fields.applicant || '',
        insured: name,
        beneficiary: r.fields.beneficiary || '',
        category: getCategory(cat),
        company: r.fields.insurance_company || '',
        policyNumber: r.fields.policy_number || '',
      });
    });
  });

  insuredBody.innerHTML = rows.map(r => `
    <tr>
      <td>${escapeHtml(r.applicant)}</td>
      <td>${escapeHtml(r.insured)}</td>
      <td>${escapeHtml(r.beneficiary)}</td>
      <td>${escapeHtml(r.category)}</td>
      <td>${escapeHtml(r.company)}</td>
      <td>${escapeHtml(r.policyNumber)}</td>
    </tr>
  `).join('');
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
    const blob = await blob;
    const jsonBlob = await resp.blob();
    downloadBlob(jsonBlob, '保单识别结果.json');
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
  applicantBody.innerHTML = '';
  insuredBody.innerHTML = '';
  policyInfoBody.innerHTML = '';
});

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
