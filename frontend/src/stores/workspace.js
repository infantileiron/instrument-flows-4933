import { request } from './session.js';

export const workspace = { catalog: null, receipts: [], plans: [], runs: [], report: null };

export async function load(page, runId) {
  const catalog = request('/catalog');
  if (page === 'ledger' || page === 'reversals') workspace.receipts = await request('/receipts');
  if (page === 'plans') [workspace.plans, workspace.runs] = await Promise.all([request('/plans'), request('/runs')]);
  if (page === 'report') {
    workspace.runs = await request('/runs');
    const selected = runId ?? workspace.runs[0]?.id;
    workspace.report = selected ? await request(`/runs/${selected}`) : null;
  }
  workspace.catalog = await catalog;
}
