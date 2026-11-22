export const links = [
  ['report', '净流报告', '▤'], ['ledger', '凭据台账', '▥'], ['reversals', '冲销核对', '↶'],
  ['plans', '透视方案', '⊞'], ['catalog', '馆藏名录', '▧'],
];

export function route() {
  const [page, selected] = location.hash.slice(1).split('/');
  return { page: links.some(([key]) => key === page) ? page : 'report', runId: /^\d+$/.test(selected) ? Number(selected) : null };
}
