"""
测试单圈计算字段的单位转换和格式化
验证所有聚合字段（Lap/Session级别）的正确性

测试覆盖：
1. 标准聚合字段：avg_speed, avg_cadence, avg_power, avg_vertical_oscillation, etc.
2. IQ聚合字段：dr_lap_avg_speed, dr_lap_avg_cadence, dr_s_avg_* 等
3. 单位转换：速度→配速，步频×2，垂直振幅÷10，步幅÷1000
4. 格式化：配速格式(M:SS)，数值精度控制

执行要求：100% Pass 才能提交代码
"""
import pytest
import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))

from fit_parser import parse_fit_file
from models import Lap, Session


class TestLapCalculatedFields:
    """测试Lap级别计算字段"""
    
    @pytest.fixture
    def sample_activity(self):
        """加载测试FIT文件"""
        fit_path = Path(__file__).parent.parent.parent / 'data' / 'activities' / '546218476_ACTIVITY.fit'
        if not fit_path.exists():
            pytest.skip(f"Test FIT file not found: {fit_path}")
        
        activity = parse_fit_file(str(fit_path), 'test_id', 'test_activity')
        return activity
    
    def test_lap_data_exists(self, sample_activity):
        """验证测试数据包含Lap信息"""
        assert len(sample_activity.laps) > 0, "Activity should have lap data"
        assert sample_activity.laps[0].lap_number == 1, "First lap should be number 1"
    
    # ============================================================================
    # 标准聚合字段测试
    # ============================================================================
    
    def test_lap_avg_speed_is_valid(self, sample_activity):
        """测试Lap平均速度字段存在且合理"""
        for lap in sample_activity.laps:
            if lap.avg_speed is not None:
                # 速度应在合理范围内（0.5 - 10 m/s，即2-36 km/h）
                assert 0.5 <= lap.avg_speed <= 10.0, \
                    f"Lap {lap.lap_number} avg_speed {lap.avg_speed} out of range"
                
                # 速度应为m/s单位（后端存储）
                # 转换为配速：6:05 pace = 1000/(6*60+5) ≈ 2.75 m/s
                pace_seconds = 1000 / lap.avg_speed
                pace_minutes = pace_seconds / 60
                assert 3 < pace_minutes < 10, \
                    f"Lap {lap.lap_number} pace {pace_minutes:.2f} min/km unreasonable"
    
    def test_lap_avg_cadence_is_doubled(self, sample_activity):
        """测试Lap平均步频已乘以2（双脚计数）"""
        for lap in sample_activity.laps:
            if lap.avg_cadence is not None:
                # 步频应为SPM（双脚），范围150-200
                assert 140 <= lap.avg_cadence <= 220, \
                    f"Lap {lap.lap_number} avg_cadence {lap.avg_cadence} out of SPM range"
                
                # 不应是RPM值（70-110）
                assert lap.avg_cadence > 120, \
                    f"Lap {lap.lap_number} avg_cadence {lap.avg_cadence} looks like RPM, should be SPM"
    
    def test_lap_avg_vertical_oscillation_unit(self, sample_activity):
        """测试Lap平均垂直振幅单位为cm"""
        for lap in sample_activity.laps:
            if lap.avg_vertical_oscillation is not None:
                # 应为cm单位，合理范围3-20cm
                assert 3.0 <= lap.avg_vertical_oscillation <= 20.0, \
                    f"Lap {lap.lap_number} avg_vertical_oscillation {lap.avg_vertical_oscillation} not in cm range"
                
                # 不应是mm值（30-200）
                assert lap.avg_vertical_oscillation < 30, \
                    f"Lap {lap.lap_number} avg_vertical_oscillation {lap.avg_vertical_oscillation} looks like mm"
    
    def test_lap_avg_step_length_unit(self, sample_activity):
        """测试Lap平均步幅单位为m"""
        for lap in sample_activity.laps:
            if lap.avg_step_length is not None:
                # 应为m单位，合理范围0.4-2.5m
                assert 0.4 <= lap.avg_step_length <= 2.5, \
                    f"Lap {lap.lap_number} avg_step_length {lap.avg_step_length} not in meter range"
                
                # 不应是mm值（400-2500）
                assert lap.avg_step_length < 100, \
                    f"Lap {lap.lap_number} avg_step_length {lap.avg_step_length} looks like mm"
    
    def test_lap_max_speed_greater_than_avg(self, sample_activity):
        """测试Lap最大速度应大于等于平均速度"""
        for lap in sample_activity.laps:
            if lap.avg_speed and lap.max_speed:
                assert lap.max_speed >= lap.avg_speed, \
                    f"Lap {lap.lap_number} max_speed {lap.max_speed} < avg_speed {lap.avg_speed}"
    
    def test_lap_max_heart_rate_greater_than_avg(self, sample_activity):
        """测试Lap最大心率应大于等于平均心率"""
        for lap in sample_activity.laps:
            if lap.avg_heart_rate and lap.max_heart_rate:
                assert lap.max_heart_rate >= lap.avg_heart_rate, \
                    f"Lap {lap.lap_number} max_hr {lap.max_heart_rate} < avg_hr {lap.avg_heart_rate}"
    
    # ============================================================================
    # IQ聚合字段测试
    # ============================================================================
    
    def test_iq_lap_avg_speed_exists(self, sample_activity):
        """测试IQ Lap平均速度字段存在"""
        lap_iq_speed_fields = []
        for lap in sample_activity.laps:
            for key in lap.iq_fields.keys():
                if 'lap_avg' in key and 'speed' in key:
                    lap_iq_speed_fields.append(key)
        
        if lap_iq_speed_fields:
            print(f"\n✓ Found IQ lap avg speed fields: {set(lap_iq_speed_fields)}")
        else:
            pytest.skip("No IQ lap avg speed fields in test data")
    
    def test_iq_lap_avg_speed_value_range(self, sample_activity):
        """测试IQ Lap平均速度值在合理范围"""
        for lap in sample_activity.laps:
            for key, value in lap.iq_fields.items():
                if 'lap_avg' in key and 'speed' in key and value is not None:
                    # IQ速度也应为m/s
                    assert 0.5 <= value <= 10.0, \
                        f"Lap {lap.lap_number} IQ field {key}={value} out of speed range"
    
    def test_iq_fields_naming_pattern(self, sample_activity):
        """测试IQ字段命名规范"""
        iq_patterns = {
            'lap_avg': [],  # dr_lap_avg_* 格式
            's_avg': [],    # dr_s_avg_* 格式
            'dr_prefix': [] # dr_* 格式
        }
        
        for lap in sample_activity.laps:
            for key in lap.iq_fields.keys():
                if 'lap_avg' in key:
                    iq_patterns['lap_avg'].append(key)
                elif 's_avg' in key:
                    iq_patterns['s_avg'].append(key)
                elif key.startswith('dr_'):
                    iq_patterns['dr_prefix'].append(key)
        
        print(f"\n✓ IQ field patterns found:")
        for pattern, fields in iq_patterns.items():
            if fields:
                print(f"  {pattern}: {set(fields)}")


class TestSessionCalculatedFields:
    """测试Session级别计算字段"""
    
    @pytest.fixture
    def sample_session(self):
        """加载测试Session数据"""
        fit_path = Path(__file__).parent.parent.parent / 'data' / 'activities' / '546218476_ACTIVITY.fit'
        if not fit_path.exists():
            pytest.skip(f"Test FIT file not found: {fit_path}")
        
        activity = parse_fit_file(str(fit_path), 'test_id', 'test_activity')
        return activity.session
    
    def test_session_avg_speed_is_valid(self, sample_session):
        """测试Session平均速度"""
        if sample_session.avg_speed:
            assert 0.5 <= sample_session.avg_speed <= 10.0, \
                f"Session avg_speed {sample_session.avg_speed} out of range"
    
    def test_session_avg_cadence_is_doubled(self, sample_session):
        """测试Session平均步频已乘以2"""
        if sample_session.avg_cadence:
            assert 140 <= sample_session.avg_cadence <= 220, \
                f"Session avg_cadence {sample_session.avg_cadence} not in SPM range"
            assert sample_session.avg_cadence > 120, \
                f"Session avg_cadence {sample_session.avg_cadence} looks like RPM"
    
    def test_session_total_distance_unit(self, sample_session):
        """测试Session总距离单位为米"""
        if sample_session.total_distance:
            # 应为米，合理范围1000m - 50000m（1-50km）
            assert 1000 <= sample_session.total_distance <= 50000, \
                f"Session total_distance {sample_session.total_distance} not in meter range"


class TestFrontendFormatting:
    """测试前端格式化函数（模拟JavaScript逻辑）"""
    
    def speed_to_pace(self, speed_ms: float) -> str:
        """模拟前端speed_to_pace函数"""
        if not speed_ms or speed_ms <= 0:
            return '--:--'
        
        pace_seconds = 1000 / speed_ms
        minutes = int(pace_seconds // 60)
        seconds = round(pace_seconds % 60)
        
        return f"{minutes}:{seconds:02d}"
    
    def test_speed_to_pace_conversion(self):
        """测试速度→配速转换"""
        # 6:05 pace = 1000/(6*60+5) ≈ 2.74 m/s
        assert self.speed_to_pace(2.74) == "6:05"
        
        # 5:00 pace = 1000/300 = 3.33 m/s
        pace = self.speed_to_pace(3.33)
        assert pace in ["5:00", "5:01"], f"Expected ~5:00, got {pace}"
        
        # 4:30 pace = 1000/270 ≈ 3.70 m/s
        pace = self.speed_to_pace(3.70)
        assert pace in ["4:30", "4:31"], f"Expected ~4:30, got {pace}"
    
    def test_pace_format_validation(self):
        """测试配速格式正则验证"""
        import re
        pace_pattern = r'^\d+:\d{2}$'
        
        valid_paces = ["5:30", "6:05", "4:15", "10:00", "05:30", "12:00"]
        for pace in valid_paces:
            assert re.match(pace_pattern, pace), f"{pace} should match pace pattern"
        
        invalid_paces = ["5:5", "65", "5.5"]
        for pace in invalid_paces:
            if not re.match(pace_pattern, pace):
                continue  # Expected to not match
            pytest.fail(f"{pace} should NOT match pace pattern")
    
    def test_user_reported_bug_case(self):
        """测试用户报告的Bug #29案例"""
        # 用户数据：圈平均配速显示2.76，实际应为~6:01
        # 2.76 m/s → 1000/2.76/60 ≈ 6.04 min/km
        result = self.speed_to_pace(2.76)
        minutes = int(result.split(':')[0])
        
        # 应显示约6分钟配速
        assert 5 <= minutes <= 7, \
            f"2.76 m/s should convert to ~6:XX pace, got {result}"
        
        # 不应显示原始值2.76
        assert result != "2.76", \
            "Should display pace format, not raw speed value"


class TestAggregateFieldDetection:
    """测试聚合字段检测模式"""
    
    def test_aggregate_pattern_matching(self):
        """测试聚合字段正则模式"""
        import re
        
        # Bug #29修复使用的模式
        aggregate_pattern = r'(avg|max|min)_\w+|_lap_avg_|_s_avg_'
        
        # 应匹配的聚合字段
        aggregate_fields = [
            'avg_speed',
            'max_speed',
            'min_speed',
            'avg_heart_rate',
            'max_cadence',
            'avg_vertical_oscillation',
            'dr_lap_avg_speed',
            'dr_lap_avg_cadence',
            'dr_s_avg_speed',
            'dr_s_avg_power'
        ]
        
        for field in aggregate_fields:
            assert re.search(aggregate_pattern, field), \
                f"Aggregate field {field} should match pattern"
        
        # 不应匹配的即时字段
        instant_fields = [
            'speed',
            'heart_rate',
            'cadence',
            'dr_speed',
            'dr_gct',
            'dr_v_osc'
        ]
        
        for field in instant_fields:
            assert not re.search(aggregate_pattern, field), \
                f"Instant field {field} should NOT match aggregate pattern"


# ============================================================================
# 测试执行和报告
# ============================================================================

def run_tests():
    """运行所有测试并生成报告"""
    import subprocess
    
    # 运行pytest并生成详细报告
    result = subprocess.run(
        ['pytest', __file__, '-v', '--tb=short', '--color=yes'],
        capture_output=True,
        text=True
    )
    
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    
    # 检查是否100% Pass
    if result.returncode != 0:
        print("\n❌ 测试未100%通过！请修复后再提交代码。")
        return False
    else:
        print("\n✅ 所有测试100% PASS！可以提交代码。")
        return True


if __name__ == '__main__':
    # 直接运行pytest
    pytest.main([__file__, '-v', '--tb=short'])
