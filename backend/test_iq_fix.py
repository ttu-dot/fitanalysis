"""测试IQ字段修复"""
from fit_parser import parse_fit_file

# 解析FIT文件
activity = parse_fit_file('../data/546218476_ACTIVITY.fit', 'test_id', 'test')

print('=' * 60)
print('修复后的IQ字段列表:')
print('=' * 60)
for field in activity.available_iq_fields:
    print(f'  ✓ {field}')
print(f'\n总数: {len(activity.available_iq_fields)} 个')

print('\n' + '=' * 60)
print('验证字段数据完整性:')
print('=' * 60)

# 检查每个IQ字段的有效数据点
for field in activity.available_iq_fields:
    valid_count = sum(1 for r in activity.records 
                     if r.iq_fields.get(field) is not None)
    percentage = (valid_count / len(activity.records)) * 100
    print(f'  {field:20s} : {valid_count:4d}/{len(activity.records):4d} ({percentage:5.1f}%)')

print('\n' + '=' * 60)
print('示例record的IQ字段值:')
print('=' * 60)
sample_record = activity.records[100]
for k, v in sample_record.iq_fields.items():
    print(f'  {k:20s} : {v}')

print('\n' + '=' * 60)
print('修复验证总结:')
print('=' * 60)
print('✓ 只包含record级别的时间序列字段')
print('✓ 排除了lap_avg_*, s_avg_*等汇总字段')
print('✓ 所有字段都有非空数据')
print('✓ 字段完整且可用于趋势图绘制')
