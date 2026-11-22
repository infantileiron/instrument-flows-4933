import { request } from './session.js';

export const workspace = {
  catalog: null, receipts: [], plans: [], runs: [], report: null,
  sync: {
    batches: [], items: [], query: { reference: '', status: '' },
    totals: { batches: 0, posted: 0, pending_original: 0, conflict: 0 },
  },
};

export async function load(page, runId) {
  const catalog = request('/catalog');
  if (page === 'ledger' || page === 'reversals') workspace.receipts = await request('/receipts');
  if (page === 'plans') [workspace.plans, workspace.runs] = await Promise.all([request('/plans'), request('/runs')]);
  if (page === 'sync') {
    const { reference, status } = workspace.sync.query;
    const query = new URLSearchParams({ reference, ...(status && { status }) });
    [workspace.sync.batches, workspace.sync.items, workspace.sync.totals] = await Promise.all([
      request('/sync/batches'),
      request(`/sync/items?${query}`),
      request('/sync/summary'),
    ]);
  }
  if (page === 'report') {
    workspace.runs = await request('/runs');
    const selected = runId ?? workspace.runs[0]?.id;
    workspace.report = selected ? await request(`/runs/${selected}`) : null;
  }
  workspace.catalog = await catalog;
}
