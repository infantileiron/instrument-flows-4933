import { badge, lead, section, table } from '../components/common/ui.js';
import { runNames } from '../constants/domain.js';
import { bindForm } from '../hooks/form.js';
import { request, session } from '../stores/session.js';
import { workspace } from '../stores/workspace.js';
import { escape as e, option, period } from '../utils/html.js';

export function plansPage() {
  const { plans, runs, catalog } = workspace;
  const analyst = session.user.role === 'analyst';
  const instruments = Object.fromEntries(catalog.instruments.map(item => [item.code, item.name]));
  const planRows = plans.map(plan => `<tr><th scope="row">${e(plan.series)} <span class="code">v${plan.version}</span></th>
    <td class="nowrap">${period(plan.start_on, plan.end_on)}</td><td>${e(instruments[plan.instrument] || '全部')}</td>
    ${analyst ? `<td><button class="quiet" data-run="${plan.id}">运行透视 →</button></td>` : ''}</tr>`).join('');
  const runRows = runs.map(row => `<tr><th scope="row"><a href="#report/${row.id}">${e(row.series)} · v${row.version}</a>
    <small class="code">#${row.id}</small></th><td>${badge(runNames[row.status], row.status === 'done' ? 'green' : '')}</td>
    <td>${row.published_at ? '已发布' : '待复核'}</td></tr>`).join('');
  const form = `<form id="plan-form" class="entry-form"><label class="wide">订阅名称<input name="series" required minlength="2" maxlength="64" value="十一月上半月调借"></label>
    <label>版本号<input name="version" type="number" min="1" max="10000" value="2" required></label>
    <label>器材族<select name="instrument">${option('', '全部器材')}${catalog.instruments.map(item => option(item.code, item.name)).join('')}</select></label>
    <label>周期起日<input name="start_on" type="date" value="2026-11-02" required></label>
    <label>周期末日<input name="end_on" type="date" value="2026-11-15" required></label>
    <div class="form-end wide"><button type="submit" class="primary">保存新版本</button><span class="error" role="alert"></span></div></form>`;
  return lead('透视方案', '按周期与器材族保存订阅参数，每次运行冻结凭据快照。') +
    `<div class="work-grid"><div>${section('订阅版本', '选定版本后提交馆际矩阵计算。',
      table(['订阅方案', '纳入周期（含首尾）', '器材族', ...(analyst ? ['操作'] : [])], planRows, '没有可阅的方案版本。') +
      '<p id="run-error" class="inline-error" role="alert"></p>')}
      ${section('运行记录', '打开报告核对凭据与行列边际。', table(['报告', '计算状态', '发布状态'], runRows, '暂无运行。'))}</div>
    ${analyst ? section('新增参数版本', '已有版本仅供复用，改口径时保存新版本。', form) : ''}</div>`;
}

export function bindPlans(refresh) {
  bindForm('#plan-form', async body => {
    const plan = await request('/plans', { body: { ...body, version: Number(body.version), instrument: body.instrument || null } });
    await refresh(`方案「${plan.series}」v${plan.version} 已保存。`);
  });
  document.querySelectorAll('[data-run]').forEach(button => button.addEventListener('click', async () => {
    button.disabled = true;
    try {
      const run = await request(`/plans/${button.dataset.run}/runs`, { body: {} });
      location.hash = `report/${run.id}`;
    } catch (error) {
      document.querySelector('#run-error').textContent = error.message;
      button.disabled = false;
    }
  }));
}
