"""
Backend unit tests for device_mappings.py
Tests DragonRun field normalization and display label generation

This file implements Test-Driven Development (TDD):
- Tests are written BEFORE device_mappings.py is implemented
- Tests define the expected behavior of the DeviceRegistry system
- Implementation will follow to make these tests pass
"""
import pytest
import sys
from pathlib import Path

# Add backend and config to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'backend'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))

try:
    from device_mappings import DeviceRegistry, DRAGONRUN_FIELDS, DRAGONRUN_FIELD_ALIASES
except ImportError:
    # Module not yet implemented - tests will fail until implementation is complete
    DeviceRegistry = None
    DRAGONRUN_FIELDS = {}
    DRAGONRUN_FIELD_ALIASES = {}

from test_constants import EXPECTED_FIELDS, DRAGONRUN_CONFIG


class TestDragonRunFieldNormalization:
    """Test field name normalization (aliases → normalized names)"""
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_all_aliases_map_correctly(self):
        """Verify all aliases from expected config map to correct normalized names"""
        for alias, expected_normalized in DRAGONRUN_CONFIG['aliases'].items():
            actual_normalized = DeviceRegistry.normalize_field_name(alias)
            assert actual_normalized == expected_normalized, \
                f"Alias {alias} should map to {expected_normalized}, got {actual_normalized}"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_normalized_names_unchanged(self):
        """Verify normalized names pass through unchanged"""
        for field_info in DRAGONRUN_CONFIG['fields']:
            field_name = field_info['field_name']
            actual = DeviceRegistry.normalize_field_name(field_name)
            assert actual == field_name, \
                f"Normalized name {field_name} should pass through unchanged, got {actual}"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_no_duplicate_prefix_in_normalized_names(self):
        """Ensure normalized names have single dr_ prefix"""
        for alias, normalized in DRAGONRUN_FIELD_ALIASES.items():
            assert not normalized.startswith('dr_dr_'), \
                f"Duplicate prefix in normalized name: {normalized}"
            assert normalized.count('dr_') == 1, \
                f"Multiple dr_ occurrences in: {normalized}"
            assert normalized in DRAGONRUN_FIELDS, \
                f"Normalized name {normalized} not in DRAGONRUN_FIELDS"


class TestDragonRunDisplayLabels:
    """Test display label generation"""
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_all_fields_have_correct_labels(self):
        """Verify all fields generate expected full_label"""
        for field_info in DRAGONRUN_CONFIG['fields']:
            field_name = field_info['field_name']
            expected_label = field_info['full_label']
            
            actual_label = DeviceRegistry.get_display_label(field_name)
            assert actual_label == expected_label, \
                f"Field {field_name}: expected '{expected_label}', got '{actual_label}'"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_no_duplicate_dr_prefix_in_labels(self):
        """Ensure display labels have exactly one DR_ prefix"""
        for field_name in DRAGONRUN_FIELDS.keys():
            label = DeviceRegistry.get_display_label(field_name)
            
            assert label.count('DR_') == 1, \
                f"Label should have exactly one DR_ prefix: {label}"
            assert 'DR_DR_' not in label, \
                f"Duplicate DR_ prefix in label: {label}"
            assert 'DR_dr_' not in label, \
                f"Mixed case prefix in label: {label}"
            # Lowercase dr_ should not appear in display label
            assert label.lower().count('dr_') == 1, \
                f"Lowercase dr_ should not appear in display label: {label}"


class TestDeviceRegistry:
    """Test DeviceRegistry functionality"""
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_dragonrun_device_registered(self):
        """Verify DragonRun device is registered"""
        device = DeviceRegistry.get_device_by_prefix('dr_gct')
        assert device is not None, "DragonRun device should be registered"
        assert device.device_id == 'dragonrun'
        assert device.device_name == '龙豆跑步'
        assert device.field_prefix == 'dr_'
        assert device.display_prefix == 'DR_'
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_all_23_fields_present(self):
        """Verify all 23 DragonValue fields are mapped"""
        expected_count = len(DRAGONRUN_CONFIG['fields'])
        actual_count = len(DRAGONRUN_FIELDS)
        
        assert actual_count == expected_count, \
            f"Expected {expected_count} fields, got {actual_count}"
        
        # Verify each expected field exists
        expected_field_names = {f['field_name'] for f in DRAGONRUN_CONFIG['fields']}
        actual_field_names = set(DRAGONRUN_FIELDS.keys())
        
        missing = expected_field_names - actual_field_names
        extra = actual_field_names - expected_field_names
        
        assert not missing, f"Missing fields: {missing}"
        assert not extra, f"Extra fields: {extra}"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_device_detection_by_prefix(self):
        """Test device auto-detection from field prefix"""
        # DragonRun fields
        device1 = DeviceRegistry.get_device_by_prefix('dr_gct')
        assert device1 is not None and device1.device_id == 'dragonrun'
        
        device2 = DeviceRegistry.get_device_by_prefix('dr_v_osc')
        assert device2 is not None and device2.device_id == 'dragonrun'
        
        # Unknown device (not yet registered)
        assert DeviceRegistry.get_device_by_prefix('garmin_gct') is None
        assert DeviceRegistry.get_device_by_prefix('unknown_field') is None
        
        # Native FIT field (no prefix)
        assert DeviceRegistry.get_device_by_prefix('heart_rate') is None
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_get_all_devices_config_structure(self):
        """Verify API export structure"""
        config = DeviceRegistry.get_all_devices_config()
        
        assert 'dragonrun' in config
        dr_config = config['dragonrun']
        
        assert dr_config['device_name'] == '龙豆跑步'
        assert dr_config['field_prefix'] == 'dr_'
        assert dr_config['display_prefix'] == 'DR_'
        assert 'fields' in dr_config
        assert isinstance(dr_config['fields'], list), "Fields should be a list"
        assert len(dr_config['fields']) == len(DRAGONRUN_FIELDS)
        
        # Verify field structure (fields is now a list)
        for field in dr_config['fields']:
            assert 'field_name' in field
            assert 'display_label' in field
            assert 'unit' in field
            assert 'full_label' in field
            assert 'description' in field
            assert 'category' in field
            
            # Verify full_label format
            assert field['full_label'].startswith('DR_')
            assert f"({field['unit']})" in field['full_label']


class TestFieldUnitConversion:
    """Test v1.8.0 unit conversion features"""
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_speed_field_has_conversion_config(self):
        """Verify dr_speed has proper conversion configuration"""
        from device_mappings import DRAGONRUN_FIELDS
        
        speed_field = DRAGONRUN_FIELDS.get('dr_speed')
        assert speed_field is not None, "dr_speed field should exist"
        assert hasattr(speed_field, 'storage_unit'), "Should have storage_unit"
        assert hasattr(speed_field, 'display_unit'), "Should have display_unit"
        assert hasattr(speed_field, 'requires_conversion'), "Should have requires_conversion"
        
        assert speed_field.storage_unit == 'm/s'
        assert speed_field.display_unit == 'min/km'
        assert speed_field.requires_conversion is True
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_non_conversion_fields_config(self):
        """Verify non-conversion fields have matching storage/display units"""
        from device_mappings import DRAGONRUN_FIELDS
        
        gct_field = DRAGONRUN_FIELDS.get('dr_gct')
        assert gct_field is not None
        assert gct_field.storage_unit == gct_field.display_unit == 'ms'
        assert gct_field.requires_conversion is False
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_all_fields_have_precision(self):
        """Verify all fields have precision setting"""
        from device_mappings import DRAGONRUN_FIELDS
        
        for field_name, field in DRAGONRUN_FIELDS.items():
            assert hasattr(field, 'precision'), f"{field_name} missing precision"
            assert isinstance(field.precision, int), f"{field_name} precision should be int"
            assert 0 <= field.precision <= 3, f"{field_name} precision out of range"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_alias_normalization_preserves_case(self):
        """Verify v1.8.0 alias normalization uses official capitalization"""
        test_cases = [
            ('dr_ssl', 'dr_SSL'),  # lowercase → uppercase alias
            ('dr_stance', 'dr_gct'),  # alias → normalized
            ('dr_lss', 'dr_LSS'),  # lowercase → uppercase alias
            ('dr_v_osc', 'dr_v_osc'),  # already correct, not an alias
        ]
        
        for alias, expected in test_cases:
            actual = DeviceRegistry.normalize_field_name(alias)
            assert actual == expected, f"{alias} should normalize to {expected}, got {actual}"
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_get_all_devices_exports_new_properties(self):
        """Verify API exports storage_unit, display_unit, requires_conversion, precision"""
        config = DeviceRegistry.get_all_devices_config()
        dr_config = config['dragonrun']
        
        for field in dr_config['fields']:
            assert 'storage_unit' in field, f"{field['field_name']} missing storage_unit"
            assert 'display_unit' in field, f"{field['field_name']} missing display_unit"
            assert 'requires_conversion' in field, f"{field['field_name']} missing requires_conversion"
            assert 'precision' in field, f"{field['field_name']} missing precision"


class TestFieldCategories:
    """Test field categorization for grouping"""
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_power_fields_categorized(self):
        """Verify power fields are correctly categorized"""
        power_fields = [f for f in DRAGONRUN_CONFIG['fields'] if f['category'] == 'power']
        power_field_names = {f['field_name'] for f in power_fields}
        
        expected_power = {'dr_vertical_power', 'dr_propulsive_power', 'dr_slope_power', 'dr_total_power'}
        assert power_field_names == expected_power
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_impact_fields_categorized(self):
        """Verify impact fields are correctly categorized"""
        impact_fields = [f for f in DRAGONRUN_CONFIG['fields'] if f['category'] == 'impact']
        impact_field_names = {f['field_name'] for f in impact_fields}
        
        # v1.8.0: Use official capitalization (PIF, ILR are uppercase)
        expected_impact = {'dr_v_PIF', 'dr_h_PIF', 'dr_v_ILR', 'dr_h_ILR',
                          'dr_body_X_PIF', 'dr_body_Y_PIF', 'dr_body_Z_PIF'}
        assert impact_field_names == expected_impact
    
    @pytest.mark.skipif(DeviceRegistry is None, reason="device_mappings.py not yet implemented")
    def test_dynamics_fields_categorized(self):
        """Verify dynamics fields are correctly categorized"""
        dynamics_fields = [f for f in DRAGONRUN_CONFIG['fields'] if f['category'] == 'dynamics']
        
        # Should include gct, air_time, v_osc, stride, cadence, vertical_ratio, ssl, ssl_percent
        assert len(dynamics_fields) >= 8


# Test to verify the expected_fields.json is valid
def test_expected_fields_json_valid():
    """Verify expected_fields.json has valid structure"""
    assert 'dragonrun' in EXPECTED_FIELDS
    dr_config = DRAGONRUN_CONFIG
    
    assert dr_config['device_id'] == 'dragonrun'
    assert dr_config['field_prefix'] == 'dr_'
    assert dr_config['display_prefix'] == 'DR_'
    assert len(dr_config['fields']) == 23  # 23 DragonValue fields
    assert len(dr_config['aliases']) >= 16  # v1.8.0: 16+ aliases (including case variations)


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v'])
