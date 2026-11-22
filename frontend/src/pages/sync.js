import { badge, lead, section, table } from '../components/common/ui.js';
import { syncNames } from '../constants/domain.js';
import { request, session } from '../stores/session.js';
import { workspace } from '../stores/workspace.js';
import { escape as e, option } from '../utils/html.js';

const canSync = () => session.user.role === 'analyst';

const SAMPLE = `[
  {"reference": "CT-1118-01", "kind": "loan", "source": "CT", "destination": "YH",
   "instrument": "SHENG", "quantity": 4, "effective_on": "2026-11-18", "note": "离线交接单补录"}
]`;

function described(report) {
  return syncNames[report.status] || report.status;
}

function itemRows(items) {
  const catalog = workspace.catalog;
  const halls = Object.fromEntries(catalog.halls.map(hall => [hall.code, hall.name]));
  const instruments = Object.fromEntries(catalog.instruments.map(item => [item.code, item]));
  if (!items.length) return '';
  return items.map(item => {
    const tone = item.status === 'posted' ? 'green' : item.status === 'conflict' ? 'red' : '';
    const family = instruments[item.instrument];
    const route = item.kind === 'loan' || item.source
      ? `${e(halls[item.source] || item.source)}<span class="arrow">→</span>${e(halls[item.destination] || item.destination)}` : '沿用原签领';
    return `<tr><th scope="row"><span class="code">${e(item.reference)}</span>
      <small>最近：第 ${item.batch_id} 批 · 行 ${item.line_no}${item.note ? ` · ${e(item.note)}` : ''}</small></th>
      <td>${badge(item.kind === 'reversal' ? '冲销' : '签领', item.kind === 'reversal' ? 'red' : '')}
        ${item.original_reference ? `<small class="code">原 ${e(item.original_reference)}</small>` : ''}</td>
      <td>${e(item.effective_on)}</td>
      <td>${route}</td>
      <td>${family ? `${e(family.name)}<small>${item.quantity} ${e(family.unit)}</small>` : '—'}</td>
      <td>${badge(described(item), tone)}<small>${e(item.detail)}</small></td>
      <td class="code">${e(item.receipt_id ? `#${item.receipt_id}` : '—')}</td></tr>`;
  }).join('');
}

function batchRows() {
  return workspace.sync.batches.map(batch => `<tr><th scope="row">第 ${batch.id} 批
    <small>${e(batch.note || '未注明')} · ${e(batch.created_by)}</small></th>
    <td class="nowrap">${e(String(batch.created_at).replace('T', ' '))}</td>
    <td class="number">${batch.total}</td><td class="number positive">${batch.posted}</td>
    <td class="number">${batch.pending_original}</td><td class="number negative">${batch.conflict}</td></tr>`).join('');
}

export function syncPage() {
  const { items, batches, totals } = workspace.sync;
  const filters = `<form id="sync-filter" class="filter-row">
    <label>编号检索<input name="reference" placeholder="如 CT-1115-91" value="${e(workspace.sync.query.reference)}"></label>
    <label>入账状态<select name="status">${option('', '全部状态', workspace.sync.query.status)}
      ${Object.entries(syncNames).map(([code, name]) => option(code, name, workspace.sync.query.status)).join('')}</select></label>
    <button type="submit" class="outline">筛选</button></form>`;
  const form = `<form id="sync-form" class="entry-form">
    <label class="wide">批次说明<input name="note" maxlength="200" placeholder="如：雁回馆网络恢复后补传"></label>
    <label class="wide">离线凭据（JSON 数组）<textarea name="payload" rows="9" required spellcheck="false"
      placeholder='${e(SAMPLE)}'></textarea></label>
    <div class="form-end wide"><button type="submit" class="primary">提交补传</button>
      <span class="hint">同号同内容重跑不会重复入账；同号异内容保留旧单；冲销可先于原签领到达。</span>
      <span class="error" role="alert"></span></div></form>`;
  return lead('离线补传', '核对各馆网络恢复后补传的离线凭据：已入账、等原单或编号冲突。') +
    `<dl class="stats stats-sync"><div><dt>补传批次</dt><dd>${totals.batches}<small> 批</small></dd></div>
      <div><dt>已入账</dt><dd>${totals.posted}<small> 张</small></dd></div>
      <div><dt>等原单</dt><dd>${totals.pending_original}<small> 张</small></dd></div>
      <div><dt>编号冲突</dt><dd>${totals.conflict}<small> 张</small></dd></div></dl>
    <div class="work-grid">${section('补传凭据', '每张凭据显示最新一次登记状态；等候中的冲销会在原签领补到后自动接上。',
      filters + table(['凭据 / 最近批次', '类型', '生效日', '出借 → 入借', '器材 / 数量', '当前状态', '凭据号'],
        itemRows(items), '没有符合条件的补传记录。'))}
      ${section('补传批次', '每批在同一事务中落账，其他凭据不受单张冲突影响。',
        table(['批次', '接收时间', '条数', '已入账', '等原单', '编号冲突'], batchRows(), '尚未收到补传批次。'))}</div>
    ${canSync() ? section('接收离线批次', '粘贴各馆导出的凭据；服务端逐张判重、验签并按原单接续。', form) : ''}`;
}

export function bindSync(refresh) {
  bindFilter(refresh);
  const form = document.querySelector('#sync-form');
  form?.addEventListener('submit', async event => {
    event.preventDefault();
    const submit = form.querySelector('button[type=submit]');
    const error = form.querySelector('[role=alert]');
    submit.disabled = true;
    error.textContent = '';
    let items;
    try {
      items = parsePayload(form.elements.payload.value);
    } catch (failure) {
      error.textContent = failure.message;
      submit.disabled = false;
      return;
    }
    try {
      const batch = await request('/sync/batches', { body: { note: form.elements.note.value.trim(), items } });
      await refresh(`第 ${batch.id} 批补传已处理：已入账 ${batch.posted}、等原单 ${batch.pending_original}、冲突 ${batch.conflict}。`);
    } catch (failure) {
      error.textContent = failure.message;
      submit.disabled = false;
    }
  });
}

function bindFilter(refresh) {
  const form = document.querySelector('#sync-filter');
  form?.addEventListener('submit', event => {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(form));
    workspace.sync.query = { reference: data.reference.trim(), status: data.status };
    refresh();
  });
}

function parsePayload(value) {
  let parsed;
  try {
    parsed = JSON.parse(value);
  } catch {
    throw new Error('凭据内容不是合法的 JSON。');
  }
  const items = Array.isArray(parsed) ? parsed : [parsed];
  if (!items.length) throw new Error('请至少提交一张凭据。');
  return items;
}
