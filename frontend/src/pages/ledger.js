import { badge, lead, section, table } from '../components/common/ui.js';
import { receiptNames } from '../constants/domain.js';
import { bindForm } from '../hooks/form.js';
import { request, session } from '../stores/session.js';
import { workspace } from '../stores/workspace.js';
import { escape as e, option } from '../utils/html.js';

const canSign = () => session.user.role === 'analyst';

function receiptRows(receipts) {
  const catalog = workspace.catalog;
  const halls = Object.fromEntries(catalog.halls.map(hall => [hall.code, hall.name]));
  const instruments = Object.fromEntries(catalog.instruments.map(item => [item.code, item]));
  return receipts.map(row => `<tr><th scope="row"><span class="code">${e(row.reference)}</span>
    <small title="${e(row.note)}">${e(row.note)}</small></th><td>${e(row.effective_on)}</td>
    <td>${e(halls[row.source])}<span class="arrow">→</span>${e(halls[row.destination])}</td>
    <td>${e(instruments[row.instrument].name)}<small>${e(row.signer_name)}</small></td>
    <td class="number ${row.kind === 'reversal' ? 'negative' : ''}">${row.kind === 'reversal' ? '−' : ''}${row.quantity} ${e(instruments[row.instrument].unit)}</td>
    <td>${badge(receiptNames[row.kind], row.kind === 'reversal' ? 'red' : '')}
    ${badge(row.signature_valid ? '验签通过' : '签名失效', row.signature_valid ? 'green' : 'red')}</td>
    <td class="code">${e(row.original_reference || row.reversed_by || '—')}</td></tr>`).join('');
}

const commonFields = (reference) => `<label>凭据编号<input name="reference" placeholder="${reference}" required minlength="3" maxlength="32" pattern="[A-Z0-9][A-Z0-9\\-]{2,31}"></label>
  <label>生效日期<input name="effective_on" type="date" required></label>`;
const note = '<label class="wide">交接事由<input name="note" minlength="2" maxlength="200" required></label>';

export function ledgerPage(reversals = false) {
  const { receipts, catalog } = workspace;
  const selected = reversals ? receipts.filter(row => row.kind === 'reversal') : receipts;
  const eligible = receipts.filter(row => row.kind === 'loan' && row.signature_valid && !row.reversed_by);
  const halls = catalog.halls.map(hall => option(hall.code, hall.name)).join('');
  const instruments = catalog.instruments.map(item => option(item.code, `${item.name} · ${item.unit}`)).join('');
  const choices = eligible.map(row => option(row.reference, `${row.reference} · ${row.note}`)).join('');
  const form = reversals ? `<form id="sign" class="entry-form">${commonFields('CX-1115-02')}
    <label class="wide">原签领<select name="original_reference" required>${option('', '选择原签领凭据', '')}${choices}</select></label>
    ${note}<div class="form-end wide"><button type="submit" class="primary">签名并冲销</button><span class="error" role="alert"></span></div></form>` :
    `<form id="sign" class="entry-form">${commonFields('CT-1115-03')}
    <label>出借馆<select name="source" required>${halls}</select></label>
    <label>入借馆<select name="destination" required>${option('', '选择入借馆', '')}${halls}</select></label>
    <label>器材族<select name="instrument">${instruments}</select></label>
    <label>数量<input name="quantity" type="number" min="1" max="500" required></label>
    ${note}<div class="form-end wide"><button type="submit" class="primary">签名并入账</button><span class="error" role="alert"></span></div></form>`;
  return lead(reversals ? '冲销核对' : '凭据台账', reversals ? '以原签领编号追溯误录凭据与冲销生效日。' : '查看馆际调借、签名状态与原始凭据的关联。') +
    `<div class="work-grid">${section(reversals ? '冲销凭据' : '电子签领记录', `最近 ${selected.length} 笔 · 按生效日倒序`,
      table(['凭据 / 事由', '生效日', '出借 → 入借', '器材 / 签领人', '数量', '签名状态', '关联凭据'], receiptRows(selected),
        reversals ? '当前没有冲销凭据。误录签领可在登记时引用原凭据编号。' : '台账为空。请先登记一笔跨馆签领。'))}
      ${canSign() ? section(reversals ? '登记冲销' : '登记签领', reversals ? '一笔签领仅可全额冲销一次，沿用原调借方向。' : '确认器材和方向后，以当前席位签名。', form) : ''}</div>`;
}

export function bindLedger(reversals, refresh) {
  bindForm('#sign', async body => {
    if (!reversals) body.quantity = Number(body.quantity);
    const result = await request(`/receipts/${reversals ? 'reversals' : 'loans'}`, { body });
    await refresh(`凭据 ${result.reference} 已${reversals ? '冲销' : '签名入账'}。`);
  });
}
