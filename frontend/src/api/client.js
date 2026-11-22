export async function api(path, { token, body, raw = false } = {}) {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? 'GET' : 'POST',
    headers: { ...(token && { Authorization: `Bearer ${token}` }),
      ...(body !== undefined && { 'Content-Type': 'application/json' }) },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    const validation = error.fields?.map(item => item.field).filter(Boolean).join('、');
    throw Object.assign(new Error((error.detail || '服务暂时不可用，请重试') + (validation ? `（${validation}）` : '')),
      { status: response.status });
  }
  return raw ? response.blob() : response.json();
}
