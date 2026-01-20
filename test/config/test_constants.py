"""Shared test constants and utilities"""
import json
from pathlib import Path

# Paths
TEST_DIR = Path(__file__).parent.parent
CONFIG_DIR = TEST_DIR / 'config'
FIXTURES_DIR = TEST_DIR / 'fixtures'
REPORTS_DIR = TEST_DIR / 'reports'
BACKEND_DIR = TEST_DIR.parent / 'backend'

# Ensure reports directory exists
REPORTS_DIR.mkdir(exist_ok=True)

# API endpoints
API_BASE = 'http://localhost:8082/api'  # v1.8.0: Updated port from 8000 to 8082
API_DEVICE_MAPPINGS = f'{API_BASE}/device-mappings'
API_ACTIVITIES = f'{API_BASE}/activities'
API_ACTIVITIES_ALL = f'{API_BASE}/activities/all'
API_VERSION = f'{API_BASE}/version'

# Test timeouts
DEFAULT_TIMEOUT = 5000  # ms for Playwright
API_TIMEOUT = 10  # seconds

# Performance thresholds (v1.8.0)
PERF_THRESHOLDS = {
    'api_device_mappings_ms': 3000,     # v1.8.0: /api/device-mappings first request < 3s (includes requests lib overhead)
    'api_upload_fit_ms': 2000,          # FIT upload should complete < 2s
    'api_get_activity_ms': 500,         # Get activity detail < 500ms
    'fit_parsing_ms': 2000,             # v1.8.0: Parse FIT file < 2s (updated from 1s)
    'ui_render_chart_ms': 1000,         # Render trend chart < 1s
    'ui_page_load_ms': 3000,            # Initial page load < 3s
    'code_coverage_percent': 80         # Code coverage target
}

# Test report retention
MAX_REPORTS_TO_KEEP = 10

# Load expected field config
def load_expected_fields():
    """Load expected DragonRun field configuration"""
    with open(CONFIG_DIR / 'expected_fields.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Convert fields dict to list format for tests
    dr_config = data['dragonrun']
    fields_dict = dr_config['fields']
    
    # Build fields list with full_label
    fields_list = []
    for field_name, field_data in fields_dict.items():
        fields_list.append({
            'field_name': field_name,
            'display_label': field_data['display_label'],
            'unit': field_data['unit'],
            'category': field_data['category'],
            'full_label': f"{dr_config['display_prefix']}{field_data['display_label']} ({field_data['unit']})",
            'description': ''  # Not in JSON yet
        })
    
    # Build aliases dict from individual field aliases
    aliases_dict = {}
    for field_name, field_data in fields_dict.items():
        if 'aliases' in field_data:
            for alias in field_data['aliases']:
                aliases_dict[alias] = field_name
    
    # Return normalized structure
    return {
        'dragonrun': {
            'device_id': 'dragonrun',
            'device_name': dr_config['device_name'],
            'field_prefix': dr_config['field_prefix'],
            'display_prefix': dr_config['display_prefix'],
            'fields': fields_list,
            'aliases': aliases_dict
        }
    }

EXPECTED_FIELDS = load_expected_fields()
DRAGONRUN_CONFIG = EXPECTED_FIELDS['dragonrun']

# Utility function for report cleanup
def cleanup_old_reports():
    """Keep only the most recent MAX_REPORTS_TO_KEEP reports"""
    if not REPORTS_DIR.exists():
        return
    
    reports = sorted(REPORTS_DIR.glob('test_report_*.html'), reverse=True)
    for old_report in reports[MAX_REPORTS_TO_KEEP:]:
        try:
            old_report.unlink()
        except Exception as e:
            print(f"Warning: Could not delete old report {old_report}: {e}")

# Validate expected fields structure
def validate_expected_fields():
    """Validate that expected_fields.json has correct structure"""
    dr_config = DRAGONRUN_CONFIG
    
    assert 'device_id' in dr_config
    assert 'device_name' in dr_config
    assert 'field_prefix' in dr_config
    assert 'display_prefix' in dr_config
    assert 'aliases' in dr_config
    assert 'fields' in dr_config
    
    assert dr_config['device_id'] == 'dragonrun'
    assert dr_config['field_prefix'] == 'dr_'
    assert dr_config['display_prefix'] == 'DR_'
    
    # Validate each field has required properties
    for field in dr_config['fields']:
        assert 'field_name' in field
        assert 'display_label' in field
        assert 'unit' in field
        assert 'full_label' in field
        assert 'description' in field
        assert 'category' in field
        
        # Validate full_label format
        expected_full_label = f"{dr_config['display_prefix']}{field['display_label']} ({field['unit']})"
        assert field['full_label'] == expected_full_label, \
            f"Field {field['field_name']}: full_label mismatch"
    
    print(f"✓ Expected fields configuration validated ({len(dr_config['fields'])} fields)")

if __name__ == '__main__':
    validate_expected_fields()
    print(f"✓ Test constants loaded successfully")
    print(f"  - Backend dir: {BACKEND_DIR}")
    print(f"  - Test dir: {TEST_DIR}")
    print(f"  - DragonRun fields: {len(DRAGONRUN_CONFIG['fields'])}")
