"""
Integration tests for /api/device-mappings endpoint (v1.8.0)
Tests API response structure, performance, and data integrity
"""
import pytest
import requests
import time
import sys
from pathlib import Path

# Add config to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'config'))
from test_constants import (
    API_BASE, API_DEVICE_MAPPINGS, PERF_THRESHOLDS, DRAGONRUN_CONFIG
)


class TestDeviceMappingsAPI:
    """Test /api/device-mappings endpoint"""
    
    def test_api_responds_successfully(self):
        """Verify API returns 200 OK"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    def test_api_response_is_valid_json(self):
        """Verify API returns valid JSON structure"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        assert isinstance(data, dict), "Response should be a dict"
        assert 'dragonrun' in data, "Response should contain 'dragonrun' key"
    
    def test_dragonrun_device_exists(self):
        """Verify DragonRun device configuration is present"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        dr_config = data['dragonrun']
        assert dr_config['device_name'] == '龙豆跑步'
        assert dr_config['field_prefix'] == 'dr_'
        assert dr_config['display_prefix'] == 'DR_'
    
    def test_all_23_fields_complete(self):
        """Verify all 23 DragonValue fields are present in API"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        dr_config = data['dragonrun']
        fields_list = dr_config['fields']
        
        assert isinstance(fields_list, list), "fields should be a list"
        assert len(fields_list) == 23, f"Expected 23 fields, got {len(fields_list)}"
        
        # Verify all expected field names are present
        expected_field_names = {f['field_name'] for f in DRAGONRUN_CONFIG['fields']}
        actual_field_names = {f['field_name'] for f in fields_list}
        
        missing = expected_field_names - actual_field_names
        extra = actual_field_names - expected_field_names
        
        assert not missing, f"Missing fields: {missing}"
        assert not extra, f"Extra fields: {extra}"
    
    def test_no_duplicate_dr_prefix(self):
        """Verify no fields have DR_DR_ or dr_dr_ duplicate prefix (v1.8.0 bugfix)"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        dr_config = data['dragonrun']
        
        for field in dr_config['fields']:
            field_name = field['field_name']
            full_label = field['full_label']
            
            # Field name should not have duplicate prefix
            assert not field_name.startswith('dr_dr_'), \
                f"Duplicate prefix in field_name: {field_name}"
            assert not field_name.lower().startswith('dr_dr_'), \
                f"Duplicate prefix (case-insensitive) in field_name: {field_name}"
            
            # Full label should have exactly one DR_ prefix
            assert full_label.count('DR_') == 1, \
                f"Label should have exactly one DR_ prefix: {full_label}"
            assert 'DR_DR_' not in full_label, \
                f"Duplicate DR_ prefix in full_label: {full_label}"
    
    def test_field_structure_validation(self):
        """Verify each field has required v1.8.0 properties"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        dr_config = data['dragonrun']
        
        required_properties = [
            'field_name', 'display_label', 'unit', 'full_label', 
            'description', 'category',
            # v1.8.0 new properties
            'storage_unit', 'display_unit', 'requires_conversion', 'precision'
        ]
        
        for field in dr_config['fields']:
            for prop in required_properties:
                assert prop in field, f"Field {field.get('field_name', 'UNKNOWN')} missing {prop}"
            
            # Validate types
            assert isinstance(field['requires_conversion'], bool), \
                f"requires_conversion should be bool for {field['field_name']}"
            assert isinstance(field['precision'], int), \
                f"precision should be int for {field['field_name']}"
            assert 0 <= field['precision'] <= 3, \
                f"precision out of range for {field['field_name']}"
    
    def test_api_performance(self):
        """Verify API responds within performance threshold (v1.8.0)"""
        # Warm-up request to load modules/cache
        requests.get(API_DEVICE_MAPPINGS, timeout=5)
        
        # Actual performance measurement
        start_time = time.time()
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert response.status_code == 200
        assert elapsed_ms < PERF_THRESHOLDS['api_device_mappings_ms'], \
            f"API too slow: {elapsed_ms:.1f}ms > {PERF_THRESHOLDS['api_device_mappings_ms']}ms threshold"
    
    def test_speed_field_has_conversion_config(self):
        """Verify dr_speed field has proper conversion configuration"""
        response = requests.get(API_DEVICE_MAPPINGS, timeout=5)
        data = response.json()
        
        dr_config = data['dragonrun']
        speed_field = next((f for f in dr_config['fields'] if f['field_name'] == 'dr_speed'), None)
        
        assert speed_field is not None, "dr_speed field not found"
        assert speed_field['storage_unit'] == 'm/s', "dr_speed storage unit should be m/s"
        assert speed_field['display_unit'] == 'min/km', "dr_speed display unit should be min/km"
        assert speed_field['requires_conversion'] is True, "dr_speed should require conversion"
        assert speed_field['precision'] == 2, "dr_speed precision should be 2"


class TestDeviceMappingsIntegration:
    """Test device mappings integration with other endpoints"""
    
    def test_version_endpoint_shows_v1_8_0(self):
        """Verify version endpoint returns v1.8.0"""
        response = requests.get(f"{API_BASE}/version", timeout=5)
        data = response.json()
        
        assert 'version' in data
        assert data['version'] == '1.8.0', f"Expected v1.8.0, got {data['version']}"


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
