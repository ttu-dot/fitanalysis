"""
Device-specific field mapping module
Provides centralized IQ field normalization and display configuration

Extension Guide:
To add a new device (e.g., Garmin, Stryd):
1. Create DEVICE_NAME_FIELDS dict with FieldMapping entries
2. Create DEVICE_NAME_FIELD_ALIASES dict for name variations
3. Call DeviceRegistry.register() with DeviceConfig
4. Add one if-statement in fit_parser.py extract_developer_fields()
5. No changes needed in frontend code - API serves all configs

Example (Garmin HRM-Pro):
```python
GARMIN_FIELDS = {
    'garmin_gct': FieldMapping(
        field_name='garmin_gct',
        display_label='Ground Contact Time',
        unit='ms',
        description='Garmin running dynamics GCT',
        field_category='dynamics'
    ),
    ...
}

DeviceRegistry.register(DeviceConfig(
    device_id='garmin',
    device_name='Garmin',
    field_prefix='garmin_',
    display_prefix='Garmin_',
    fields=GARMIN_FIELDS,
    field_aliases={'garmin_stance_time': 'garmin_gct'}
))
```
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class FieldMapping:
    """Configuration for a single device field"""
    field_name: str           # Full name with device prefix: "dr_gct"
    display_label: str        # Label without device prefix: "触地时间"
    unit: str                 # Display unit: "ms", "cm", "bpm" (DEPRECATED: use display_unit)
    description: str          # Full Chinese description
    field_category: str       # "dynamics", "power", "impact", etc.
    storage_unit: str = None  # v1.8.0: Unit in backend storage (e.g., "m/s" for speed)
    display_unit: str = None  # v1.8.0: Unit in frontend display (e.g., "min/km" for pace)
    requires_conversion: bool = False  # v1.8.0: Whether frontend needs to convert value
    precision: int = 2        # v1.8.0: Decimal places for display
    
    def __post_init__(self):
        """Auto-fill storage_unit and display_unit if not explicitly set"""
        if self.storage_unit is None:
            self.storage_unit = self.unit
        if self.display_unit is None:
            self.display_unit = self.unit


@dataclass  
class DeviceConfig:
    """Configuration for a device (e.g., DragonRun, Garmin)"""
    device_id: str            # Unique ID: "dragonrun", "garmin", "stryd"
    device_name: str          # Display name: "龙豆跑步", "Garmin", "Stryd"
    field_prefix: str         # Field name prefix: "dr_", "garmin_", "stryd_"
    display_prefix: str       # UI display prefix: "DR_", "Garmin_", "Stryd_"
    fields: Dict[str, FieldMapping]
    field_aliases: Dict[str, str]  # Alias mappings for normalization


# ============================================================================
# DragonRun Device Configuration
# ============================================================================

# DragonRun field mappings (23 fields from DragonValue specification)
DRAGONRUN_FIELDS = {
    'dr_timestamp': FieldMapping(
        field_name='dr_timestamp',
        display_label='时间戳',
        unit='ms',
        description='步态数据记录的时间点',
        field_category='basic'
    ),
    'dr_distance': FieldMapping(
        field_name='dr_distance',
        display_label='距离',
        unit='m',
        description='跑步累计距离',
        field_category='basic'
    ),
    'dr_speed': FieldMapping(
        field_name='dr_speed',
        display_label='配速',
        unit='min/km',
        description='当前配速',
        field_category='pace',
        storage_unit='m/s',      # v1.8.0: Backend stores speed in m/s
        display_unit='min/km',   # v1.8.0: Frontend displays as pace
        requires_conversion=True, # v1.8.0: Frontend converts m/s → min/km
        precision=2
    ),
    'dr_cadence': FieldMapping(
        field_name='dr_cadence',
        display_label='步频',
        unit='spm',
        description='每分钟步数（双脚计数）',
        field_category='dynamics'
    ),
    'dr_stride': FieldMapping(
        field_name='dr_stride',
        display_label='步幅',
        unit='cm',
        description='单步距离',
        field_category='dynamics'
    ),
    'dr_gct': FieldMapping(
        field_name='dr_gct',
        display_label='触地时间',
        unit='ms',
        description='每步跑步时地面接触的时间',
        field_category='dynamics'
    ),
    'dr_air_time': FieldMapping(
        field_name='dr_air_time',
        display_label='腾空时间',
        unit='ms',
        description='每步跑步时双脚离地的时间',
        field_category='dynamics'
    ),
    'dr_v_osc': FieldMapping(
        field_name='dr_v_osc',
        display_label='垂直振幅',
        unit='cm',
        description='身体重心上下振幅',
        field_category='dynamics'
    ),
    'dr_vertical_ratio': FieldMapping(
        field_name='dr_vertical_ratio',
        display_label='垂直步幅比',
        unit='%',
        description='垂直振幅与步幅的比值',
        field_category='dynamics'
    ),
    'dr_SSL': FieldMapping(
        field_name='dr_SSL',
        display_label='步速损失',
        unit='cm/s',
        description='每次着地时速度损失量',
        field_category='dynamics'
    ),
    'dr_SSL_percent': FieldMapping(
        field_name='dr_SSL_percent',
        display_label='步速损失占比',
        unit='%',
        description='步速损失占当前速度的百分比',
        field_category='dynamics'
    ),
    'dr_vertical_power': FieldMapping(
        field_name='dr_vertical_power',
        display_label='垂直功率',
        unit='W',
        description='克服重力做功的功率',
        field_category='power'
    ),
    'dr_propulsive_power': FieldMapping(
        field_name='dr_propulsive_power',
        display_label='前进功率',
        unit='W',
        description='前进方向的有效功率',
        field_category='power'
    ),
    'dr_slope_power': FieldMapping(
        field_name='dr_slope_power',
        display_label='坡度功率',
        unit='W',
        description='上坡或下坡消耗的功率',
        field_category='power'
    ),
    'dr_total_power': FieldMapping(
        field_name='dr_total_power',
        display_label='总功率',
        unit='W',
        description='垂直功率+前进功率+坡度功率',
        field_category='power'
    ),
    'dr_LSS': FieldMapping(
        field_name='dr_LSS',
        display_label='下肢刚度',
        unit='kN/m',
        description='腿部弹性系数，刚度越高弹性越好',
        field_category='biomechanics'
    ),
    'dr_v_ILR': FieldMapping(
        field_name='dr_v_ILR',
        display_label='垂直冲击力',
        unit='bw/s',
        description='垂直方向的冲击负荷率',
        field_category='impact'
    ),
    'dr_h_ILR': FieldMapping(
        field_name='dr_h_ILR',
        display_label='水平冲击力',
        unit='bw/s',
        description='水平方向的冲击负荷率',
        field_category='impact'
    ),
    'dr_v_PIF': FieldMapping(
        field_name='dr_v_PIF',
        display_label='垂直冲击峰值',
        unit='g',
        description='足部着地时垂直方向的最大加速度',
        field_category='impact'
    ),
    'dr_h_PIF': FieldMapping(
        field_name='dr_h_PIF',
        display_label='水平冲击峰值',
        unit='g',
        description='足部着地时水平方向的最大加速度',
        field_category='impact'
    ),
    'dr_body_X_PIF': FieldMapping(
        field_name='dr_body_X_PIF',
        display_label='传感器X轴冲击',
        unit='g',
        description='传感器X轴检测到的冲击峰值',
        field_category='impact'
    ),
    'dr_body_Y_PIF': FieldMapping(
        field_name='dr_body_Y_PIF',
        display_label='传感器Y轴冲击',
        unit='g',
        description='传感器Y轴检测到的冲击峰值',
        field_category='impact'
    ),
    'dr_body_Z_PIF': FieldMapping(
        field_name='dr_body_Z_PIF',
        display_label='传感器Z轴冲击',
        unit='g',
        description='传感器Z轴检测到的冲击峰值',
        field_category='impact'
    )
}

# DragonRun field name variations (handle inconsistent FIT data)
DRAGONRUN_FIELD_ALIASES = {
    # Official abbreviation aliases (6 mappings)
    'dr_stance': 'dr_gct',              # Alias: stance → gct
    'dr_air': 'dr_air_time',            # Alias: air → air_time
    'dr_at': 'dr_air_time',             # Alternative alias for air_time
    'dr_vertical_osc': 'dr_v_osc',      # Alias: vertical_osc → v_osc
    'dr_vert_osc': 'dr_v_osc',          # Alternative alias
    'dr_prop_power': 'dr_propulsive_power',  # v1.8.0: prop_power → propulsive_power
    
    # Case variation aliases (10 mappings for DragonValue official capitalization)
    'dr_ssl': 'dr_SSL',                 # v1.8.0: ssl → SSL
    'dr_ssl%': 'dr_SSL_percent',        # v1.8.0: Handle special character ssl% → SSL_percent
    'dr_SSL%': 'dr_SSL_percent',        # v1.8.0: Handle special character SSL% → SSL_percent
    'dr_lss': 'dr_LSS',                 # v1.8.0: lss → LSS
    'dr_v_ilr': 'dr_v_ILR',             # v1.8.0: v_ilr → v_ILR
    'dr_h_ilr': 'dr_h_ILR',             # v1.8.0: h_ilr → h_ILR
    'dr_v_pif': 'dr_v_PIF',             # v1.8.0: v_pif → v_PIF
    'dr_h_pif': 'dr_h_PIF',             # v1.8.0: h_pif → h_PIF
    'dr_body_x_pif': 'dr_body_X_PIF',   # v1.8.0: body_x_pif → body_X_PIF
    'dr_body_y_pif': 'dr_body_Y_PIF',   # v1.8.0: body_y_pif → body_Y_PIF
    'dr_body_z_pif': 'dr_body_Z_PIF',   # v1.8.0: body_z_pif → body_Z_PIF
    
    # Legacy aliases
    'dr_slop_power': 'dr_slope_power',  # Fix typo in source data
}


# ============================================================================
# Device Registry
# ============================================================================

class DeviceRegistry:
    """
    Global registry for device-specific field mappers
    
    Manages all registered device configurations and provides
    field normalization and display label lookup services.
    """
    _devices: Dict[str, DeviceConfig] = {}
    
    @classmethod
    def register(cls, config: DeviceConfig):
        """
        Register a new device configuration
        
        Args:
            config: DeviceConfig instance with device metadata and field mappings
        """
        cls._devices[config.device_id] = config
    
    @classmethod
    def get_device_by_prefix(cls, field_name: str) -> Optional[DeviceConfig]:
        """
        Detect device from field name prefix
        
        Args:
            field_name: Field name to check (e.g., 'dr_gct' → dragonrun)
        
        Returns:
            DeviceConfig if device found, None otherwise
        """
        for device in cls._devices.values():
            if field_name.startswith(device.field_prefix):
                return device
        return None
    
    @classmethod
    def normalize_field_name(cls, raw_name: str) -> str:
        """
        Normalize field name using device-specific aliases
        
        Converts field name variations to canonical normalized names.
        Example: 'dr_stance' → 'dr_gct'
        
        Args:
            raw_name: Raw field name from FIT file
        
        Returns:
            Normalized field name
        """
        device = cls.get_device_by_prefix(raw_name)
        if not device:
            return raw_name
        
        # Check if it's an alias that needs mapping
        return device.field_aliases.get(raw_name, raw_name)
    
    @classmethod
    def get_display_label(cls, field_name: str) -> str:
        """
        Get full display label with device prefix
        
        Example: 'dr_gct' → 'DR_触地时间 (ms)'
        
        Args:
            field_name: Normalized field name
        
        Returns:
            Full display label for UI
        """
        device = cls.get_device_by_prefix(field_name)
        if not device or field_name not in device.fields:
            return field_name
        
        mapping = device.fields[field_name]
        return f"{device.display_prefix}{mapping.display_label} ({mapping.unit})"
    
    @classmethod
    def get_all_devices_config(cls) -> Dict:
        """
        Export all device configurations as JSON-serializable dict
        
        Used by /api/device-mappings endpoint to serve config to frontend.
        
        Returns:
            Dict with structure:
            {
                "device_id": {
                    "device_name": str,
                    "field_prefix": str,
                    "display_prefix": str,
                    "fields": [  # List format for easy frontend iteration
                        {
                            "field_name": str,
                            "display_label": str,
                            "unit": str,
                            "storage_unit": str,        # v1.8.0
                            "display_unit": str,        # v1.8.0
                            "requires_conversion": bool, # v1.8.0
                            "precision": int,           # v1.8.0
                            "full_label": str,
                            "description": str,
                            "category": str
                        }
                    ]
                }
            }
        """
        result = {}
        for device_id, device in cls._devices.items():
            result[device_id] = {
                'device_name': device.device_name,
                'field_prefix': device.field_prefix,
                'display_prefix': device.display_prefix,
                'fields': []  # Changed to list format
            }
            for field_name, mapping in device.fields.items():
                field_dict = {
                    'field_name': field_name,  # Include field_name in each object
                    'display_label': mapping.display_label,
                    'unit': mapping.unit,
                    'full_label': f"{device.display_prefix}{mapping.display_label} ({mapping.unit})",
                    'description': mapping.description,
                    'category': mapping.field_category
                }
                # v1.8.0: Add conversion-related fields if present
                if mapping.storage_unit:
                    field_dict['storage_unit'] = mapping.storage_unit
                if mapping.display_unit:
                    field_dict['display_unit'] = mapping.display_unit
                field_dict['requires_conversion'] = mapping.requires_conversion
                field_dict['precision'] = mapping.precision
                
                result[device_id]['fields'].append(field_dict)
        return result


# ============================================================================
# Initialize Devices
# ============================================================================

# Register DragonRun device on module import
DeviceRegistry.register(DeviceConfig(
    device_id='dragonrun',
    device_name='龙豆跑步',
    field_prefix='dr_',
    display_prefix='DR_',
    fields=DRAGONRUN_FIELDS,
    field_aliases=DRAGONRUN_FIELD_ALIASES
))


# ============================================================================
# Module Test
# ============================================================================

if __name__ == '__main__':
    """Test the device mapping module"""
    print("Device Mapping Module Test")
    print("=" * 60)
    
    # Test DragonRun registration
    dr_device = DeviceRegistry.get_device_by_prefix('dr_gct')
    assert dr_device is not None
    print(f"✓ DragonRun device registered: {dr_device.device_name}")
    
    # Test normalization
    assert DeviceRegistry.normalize_field_name('dr_stance') == 'dr_gct'
    assert DeviceRegistry.normalize_field_name('dr_vertical_osc') == 'dr_v_osc'
    print(f"✓ Field normalization working")
    
    # Test display labels
    label = DeviceRegistry.get_display_label('dr_gct')
    assert label == 'DR_触地时间 (ms)'
    print(f"✓ Display label generation: {label}")
    
    # Test API export
    config = DeviceRegistry.get_all_devices_config()
    assert 'dragonrun' in config
    assert len(config['dragonrun']['fields']) == 23
    print(f"✓ API export structure: {len(config['dragonrun']['fields'])} fields")
    
    # Check for duplicate prefixes
    for field_name, field_data in config['dragonrun']['fields'].items():
        full_label = field_data['full_label']
        assert 'DR_DR_' not in full_label
        assert full_label.count('DR_') == 1
    print(f"✓ No duplicate DR_ prefixes in labels")
    
    print("\n" + "=" * 60)
    print("All tests passed! ✓")
