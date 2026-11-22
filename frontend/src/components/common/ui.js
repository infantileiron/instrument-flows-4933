import { escape } from '../../utils/html.js';

export function badge(text, tone = '') {
  return `<span class="badge ${tone}">${escape(text)}</span>`;
}

export function section(title, subtitle, body, actions = '') {
  return `<section class="panel"><header class="section-head"><div><h2>${escape(title)}</h2>
    ${subtitle ? `<p>${escape(subtitle)}</p>` : ''}</div>${actions}</header>${body}</section>`;
}

export function table(headers, content, empty) {
  if (!content) return `<div class="empty">${escape(empty)}</div>`;
  return `<div class="table-scroll"><table><thead><tr>${headers.map(x => `<th scope="col">${escape(x)}</th>`).join('')}</tr></thead>
    <tbody>${content}</tbody></table></div>`;
}

export function lead(title, subtitle, content = '') {
  return `<header class="page-head"><div><h1>${escape(title)}</h1><p>${escape(subtitle)}</p></div>${content}</header>`;
}
