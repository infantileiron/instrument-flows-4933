HALLS = [
    ('CT', '吹桐总馆', '陆清扬', '合奏排练与总库周转'),
    ('YH', '雁回分馆', '余闻笙', '少年团分声部合练'),
    ('ZS', '竹水分馆', '林至远', '社区巡演与打击乐排练'),
]
INSTRUMENTS = [('SHENG', '笙', '支'), ('DRUM', '鼓', '面'), ('GONG', '锣', '面')]
USERS = [('reviewer', '陆清扬', 'reviewer', 'ScoreReview12!'),
         ('analyst', '许听澜', 'analyst', 'ScoreAnalysis12!'),
         ('observer', '林至远', 'observer', 'ScoreObserve12!')]
LOANS = [
    ('CT-1028-01', '2026-10-28', 'CT', 'ZS', 'DRUM', 4, '旧周期巡演鼓借用'),
    ('CT-1102-01', '2026-11-02', 'CT', 'YH', 'SHENG', 8, '雁回少年团合练'),
    ('CT-1103-02', '2026-11-03', 'CT', 'YH', 'SHENG', 5, '五支笙误录在雁回领单'),
    ('YH-1104-01', '2026-11-04', 'YH', 'CT', 'SHENG', 3, '总馆三重奏替补'),
    ('YH-1105-01', '2026-11-05', 'YH', 'ZS', 'DRUM', 6, '竹水社区巡演备鼓'),
    ('ZS-1106-01', '2026-11-06', 'ZS', 'YH', 'DRUM', 2, '雁回少年团加场'),
    ('ZS-1107-01', '2026-11-07', 'ZS', 'CT', 'GONG', 4, '总馆打击乐排练'),
    ('CT-1108-01', '2026-11-08', 'CT', 'ZS', 'GONG', 1, '竹水领一面小锣'),
    ('CT-1109-01', '2026-11-09', 'CT', 'YH', 'GONG', 2, '雁回换场伴奏'),
    ('YH-1110-01', '2026-11-10', 'YH', 'ZS', 'SHENG', 3, '竹水分声部排练'),
    ('ZS-1112-01', '2026-11-12', 'ZS', 'CT', 'DRUM', 2, '总馆备用堂鼓'),
    ('YH-1113-01', '2026-11-13', 'YH', 'CT', 'GONG', 2, '总馆分谱回排'),
]
REVERSALS = [
    ('CX-1101-01', '2026-11-01', 'CT-1028-01', '旧周期四面鼓重复签领，登记冲销'),
    ('CX-1111-01', '2026-11-11', 'CT-1103-02', '核对雁回收件联后冲销五支笙'),
]
SERIES = '十一月上半月调借'
# 离线补传演示：日期落在 v1 报告（11-02 至 11-15）之外，不改变既定基线。
# 同一批里演示已入账、等原单、编号冲突三种结果。
SYNC_BATCHES = [
    {'note': '演示：雁回馆网络恢复后补传', 'items': [
        {'reference': 'CT-1117-01', 'kind': 'loan', 'source': 'CT', 'destination': 'YH',
         'instrument': 'SHENG', 'quantity': 2, 'effective_on': '2026-11-17', 'note': '离线交接单补录'},
        {'reference': 'CX-1117-01', 'kind': 'reversal', 'original_reference': 'CT-1117-01',
         'effective_on': '2026-11-17', 'note': '同日误录回冲，自动接上原单'},
        {'reference': 'CX-1117-02', 'kind': 'reversal', 'original_reference': 'CT-1117-99',
         'effective_on': '2026-11-17', 'note': '原单尚在路上，先等候'},
        {'reference': 'CT-1102-01', 'kind': 'loan', 'source': 'CT', 'destination': 'YH',
         'instrument': 'SHENG', 'quantity': 99, 'effective_on': '2026-11-02', 'note': '重复编号异内容，应扣住'},
    ]},
]
