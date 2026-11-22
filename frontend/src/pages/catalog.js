import { lead, section, table } from '../components/common/ui.js';
import { workspace } from '../stores/workspace.js';
import { escape as e } from '../utils/html.js';

export function catalogPage() {
  const { halls, instruments } = workspace.catalog;
  return lead('馆藏名录', '确认调借凭据中的馆点、器材族与盘点单位。') +
    section('馆点', '调借方向以出借馆和入借馆登记。', table(['馆号', '馆点', '负责人', '排练用途'], halls.map(hall =>
      `<tr><td class="code">${e(hall.code)}</td><th scope="row">${e(hall.name)}</th><td>${e(hall.manager)}</td><td>${e(hall.purpose)}</td></tr>`).join(''), '馆点未配置。')) +
    section('器材族', '馆对相抵在同一器材族内计算。', table(['代码', '器材族', '记账单位'], instruments.map(item =>
      `<tr><td class="code">${e(item.code)}</td><th scope="row">${e(item.name)}</th><td>${e(item.unit)}</td></tr>`).join(''), '器材族未配置。'));
}
