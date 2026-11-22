const replacements = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' };
export const escape = (value) => String(value ?? '').replace(/[&<>"']/g, character => replacements[character]);
export const signedNumber = (value) => value > 0 ? `+${value}` : String(value).replace('-', '−');
export const period = (start, end) => `${start.replaceAll('-', '.')} — ${end.replaceAll('-', '.')}`;
export const option = (value, label, selected) => `<option value="${escape(value)}" ${String(value) === String(selected) ? 'selected' : ''}>${escape(label)}</option>`;
