import { roleNames } from './constants/domain.js';
import { catalogPage } from './pages/catalog.js';
import { bindLedger, ledgerPage } from './pages/ledger.js';
import { bindLogin, loginPage } from './pages/login.js';
import { bindPlans, plansPage } from './pages/plans.js';
import { bindReport, reportPage } from './pages/report.js';
import { links, route } from './router/routes.js';
import { request, session, signOut } from './stores/session.js';
import { load } from './stores/workspace.js';
import { escape as e } from './utils/html.js';

const app = document.querySelector('#app');
const pages = { report: reportPage, ledger: ledgerPage, reversals: () => ledgerPage(true), plans: plansPage, catalog: catalogPage };
let refreshNumber = 0;
let pollTimer;

function shell(page, content, message) {
  const { user } = session;
  const nav = links.map(([key, label, symbol]) => `<a href="#${key}" ${key === page ? 'aria-current="page"' : ''}>
    <span aria-hidden="true">${symbol}</span>${label}</a>`).join('');
  const title = links.find(([key]) => key === page)[1];
  return `<div class="shell"><aside class="rail"><a class="wordmark" href="#report"><span class="mark">桐</span>
    <div>吹桐民乐<small>馆务总谱</small></div></a>
    <nav aria-label="馆务模块">${nav}</nav><div class="rail-bottom"><span class="rail-avatar">${e(user.display_name[0])}</span>
    <div>${e(user.display_name)}<small>${roleNames[user.role]}</small></div><button id="logout">退出</button></div></aside>
    <div class="workspace"><div class="topbar"><span>馆务工作台 <span class="slash">/</span> <b>${title}</b></span>
    <span class="top-role"><i></i>${roleNames[user.role]}</span></div>
    <main id="content">${message ? `<p class="notice" role="status">${e(message)}</p>` : ''}${content}</main>
    <footer class="workspace-foot">吹桐民乐 · 跨馆器材调借</footer></div></div>`;
}

function logout() {
  signOut();
  refresh();
}

async function refresh(message = '') {
  clearTimeout(pollTimer);
  const ticket = ++refreshNumber;
  if (!session.token) {
    app.innerHTML = loginPage();
    bindLogin(refresh);
    return;
  }
  const { page, runId } = route();
  try {
    if (!session.user) session.user = await request('/me');
    await load(page, runId);
    if (ticket !== refreshNumber) return;
    app.innerHTML = shell(page, pages[page](), message);
    document.querySelector('#logout').addEventListener('click', logout);
    if (page === 'ledger' || page === 'reversals') bindLedger(page === 'reversals', refresh);
    if (page === 'plans') bindPlans(refresh);
    if (page === 'report') pollTimer = bindReport(refresh);
  } catch (failure) {
    if (ticket !== refreshNumber) return;
    if (failure.status === 401) return logout();
    const recovery = `<div class="empty error-panel"><p role="alert">${e(failure.message)}</p>
      <button id="retry" class="outline">重试</button> <a href="#report">返回报告列表</a></div>`;
    app.innerHTML = session.user ? shell(page, recovery) : recovery;
    document.querySelector('#retry').addEventListener('click', () => refresh());
    document.querySelector('#logout')?.addEventListener('click', logout);
  }
}

window.addEventListener('hashchange', () => {
  window.scrollTo(0, 0);
  refresh();
});
refresh();
