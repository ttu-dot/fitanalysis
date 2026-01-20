"""
后端API测试 - 测试FIT解析器和字段映射
运行方式: python test_api.py
"""
import sys
import os

# 添加backend目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fit_parser import parse_fit_bytes, DR_FIELD_MAPPING
import uuid


class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []
    
    def test(self, name, fn):
        try:
            fn()
            self.passed += 1
            self.results.append({'name': name, 'status': 'PASS'})
            print(f"✓ {name}")
        except Exception as e:
            self.failed += 1
            self.results.append({'name': name, 'status': 'FAIL', 'error': str(e)})
            print(f"✗ {name}: {e}")
    
    def assertEqual(self, actual, expected, message=''):
        if actual != expected:
            raise AssertionError(f"{message} Expected '{expected}', got '{actual}'")
    
    def assertTrue(self, condition, message=''):
        if not condition:
            raise AssertionError(f"{message} Expected True, got False")
    
    def assertIn(self, item, container, message=''):
        if item not in container:
            raise AssertionError(f"{message} '{item}' not found in container")
    
    def summary(self):
        print(f"\n========== 测试结果 ==========")
        print(f"通过: {self.passed}, 失败: {self.failed}")
        return {'passed': self.passed, 'failed': self.failed}


def main():
    runner = TestRunner()
    
    # 测试FIT文件路径
    fit_path = os.path.join(os.path.dirname(__file__), '..', 'data', '546218476_ACTIVITY.fit')
    
    if not os.path.exists(fit_path):
        print(f"警告: 测试FIT文件不存在: {fit_path}")
        return
    
    # 加载FIT文件
    with open(fit_path, 'rb') as f:
        fit_data = f.read()
    
    activity = parse_fit_bytes(fit_data, 'test.fit', str(uuid.uuid4()))
    
    print("\n========== DR字段映射测试 ==========\n")
    
    runner.test('DR_FIELD_MAPPING包含dr_gct映射', lambda: 
        runner.assertEqual(DR_FIELD_MAPPING.get('dr_gct'), 'gct'))
    
    runner.test('DR_FIELD_MAPPING包含dr_at映射为air_time', lambda: 
        runner.assertEqual(DR_FIELD_MAPPING.get('dr_at'), 'air_time'))
    
    runner.test('DR_FIELD_MAPPING包含dr_stride映射为stride_length', lambda: 
        runner.assertEqual(DR_FIELD_MAPPING.get('dr_stride'), 'stride_length'))
    
    runner.test('DR_FIELD_MAPPING包含dr_vert_osc映射为v_osc', lambda: 
        runner.assertEqual(DR_FIELD_MAPPING.get('dr_vert_osc'), 'v_osc'))
    
    runner.test('DR_FIELD_MAPPING包含dr_v_PIF映射为v_pif', lambda: 
        runner.assertEqual(DR_FIELD_MAPPING.get('dr_v_PIF'), 'v_pif'))
    
    print("\n========== FIT解析测试 ==========\n")
    
    runner.test('活动应成功解析', lambda: 
        runner.assertTrue(activity is not None, '活动不应为None'))
    
    runner.test('活动应有session数据', lambda: 
        runner.assertTrue(activity.session is not None))
    
    runner.test('活动应有records数据', lambda: 
        runner.assertTrue(len(activity.records) > 0, '应有记录数据'))
    
    runner.test('活动应有available_iq_fields', lambda: 
        runner.assertTrue(hasattr(activity, 'available_iq_fields')))
    
    print("\n========== IQ字段提取测试 ==========\n")
    
    # 检查是否有IQ字段
    has_iq_fields = False
    for record in activity.records:
        if record.iq_fields and len(record.iq_fields) > 0:
            has_iq_fields = True
            break
    
    if has_iq_fields:
        runner.test('应正确提取IQ字段', lambda: 
            runner.assertTrue(has_iq_fields, '应有IQ字段'))
        
        # 找到第一个有IQ字段的记录
        sample_record = None
        for r in activity.records:
            if r.iq_fields and len(r.iq_fields) > 0:
                sample_record = r
                break
        
        if sample_record:
            iq_keys = list(sample_record.iq_fields.keys())
            print(f"  发现的IQ字段: {iq_keys}")
            
            # 检查是否包含映射后的字段名
            runner.test('IQ字段应使用映射后的名称（如gct而非dr_gct）', lambda: 
                runner.assertTrue(
                    any(k in ['gct', 'air_time', 'stride_length', 'v_osc', 'v_pif', 'cadence', 'speed', 'distance'] 
                        for k in iq_keys),
                    f'字段名应是映射后的标准名称, 实际: {iq_keys}'
                ))
    else:
        print("  注意: 此FIT文件不包含IQ字段")
    
    print("\n========== elapsed_time计算测试 ==========\n")
    
    runner.test('第一条记录的elapsed_time应为0或接近0', lambda: 
        runner.assertTrue(
            activity.records[0].elapsed_time is not None and activity.records[0].elapsed_time < 5,
            f'第一条记录elapsed_time应接近0, 实际: {activity.records[0].elapsed_time}'
        ))
    
    runner.test('elapsed_time应递增', lambda: 
        runner.assertTrue(
            activity.records[-1].elapsed_time > activity.records[0].elapsed_time,
            'elapsed_time应该递增'
        ))
    
    # 输出测试摘要
    summary = runner.summary()
    
    return summary['failed'] == 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
