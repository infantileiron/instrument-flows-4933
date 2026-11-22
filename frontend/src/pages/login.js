import { api } from '../api/client.js';
import { bindForm } from '../hooks/form.js';
import { signIn } from '../stores/session.js';

export function loginPage() {
  return `<main class="login-layout"><section class="login-cover">
    <div class="cover-wordmark"><span class="mark">桐</span> 吹桐民乐</div>
    <div class="cover-title"><p>馆务总谱</p><h1>跨馆器材<br>调借透视</h1><div class="cover-divider"></div>
      <p>三馆共用器材的签领记录、冲销和净流报告。</p></div>
    <p class="cover-footer">吹桐总馆　·　雁回分馆　·　竹水分馆</p></section>
    <section class="login-content"><form id="login-form" class="login-form">
      <h2>登录馆务工作台</h2><label>账号<input name="username" autocomplete="username" required></label>
      <label>口令<input name="password" type="password" autocomplete="current-password" required></label>
      <button class="primary" type="submit">进入工作台 <span aria-hidden="true">→</span></button>
      <p class="error" role="alert"></p>
      <div class="login-help">演示账号　<button type="button" data-demo="analyst">分析</button>
        <button type="button" data-demo="reviewer">复核</button><button type="button" data-demo="observer">观察</button></div>
    </form></section></main>`;
}

export function bindLogin(refresh) {
  const passwords = { analyst: 'ScoreAnalysis12!', reviewer: 'ScoreReview12!', observer: 'ScoreObserve12!' };
  document.querySelectorAll('[data-demo]').forEach(button => button.addEventListener('click', () => {
    const username = button.dataset.demo;
    const form = button.form;
    form.elements.username.value = username;
    form.elements.password.value = passwords[username];
  }));
  bindForm('#login-form', async body => {
    signIn(await api('/login', { body }));
    if (location.hash === '#report') refresh();
    else location.hash = 'report';
  });
}
