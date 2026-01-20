"""
字段单位转换模块
提供配置化、可扩展的FIT字段单位转换功能

策略：
1. 配置驱动：基于FIT SDK Profile.xlsx的单位定义
2. 元数据验证：使用FIT字段的units属性（如果可用）
3. 智能检测：基于合理范围的自动单位推断
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class Unit(Enum):
    """FIT SDK支持的单位类型"""
    # 距离
    MILLIMETERS = "mm"
    CENTIMETERS = "cm"
    METERS = "m"
    KILOMETERS = "km"
    
    # 时间
    MILLISECONDS = "ms"
    SECONDS = "s"
    MINUTES = "min"
    
    # 速度
    METERS_PER_SECOND = "m/s"
    KILOMETERS_PER_HOUR = "km/h"
    
    # 角度
    SEMICIRCLES = "semicircles"
    DEGREES = "degrees"
    
    # 生理指标
    BPM = "bpm"  # 心率
    RPM = "rpm"  # 转速
    SPM = "spm"  # 步频
    WATTS = "watts"  # 功率
    PERCENT = "percent"  # 百分比
    
    # 其他
    DIMENSIONLESS = ""  # 无量纲
    CALORIES = "kcal"
    GRAMS = "g"


@dataclass
class FieldUnitConfig:
    """字段单位配置"""
    field_name: str
    fit_unit: Unit  # FIT文件中的单位
    display_unit: Unit  # 显示使用的单位
    scale_factor: float  # 转换系数
    reasonable_range: Tuple[float, float]  # 合理范围(转换后)
    description: str


# ============================================================================
# 标准字段单位配置（基于FIT SDK Profile.xlsx）
# ============================================================================

STANDARD_FIELD_UNITS: Dict[str, FieldUnitConfig] = {
    # 运动力学指标
    "vertical_oscillation": FieldUnitConfig(
        field_name="vertical_oscillation",
        fit_unit=Unit.MILLIMETERS,
        display_unit=Unit.CENTIMETERS,
        scale_factor=0.1,  # mm -> cm
        reasonable_range=(3.0, 20.0),  # 正常范围6-12cm，智能检测会自动处理异常值
        description="垂直振幅：跑步时身体上下运动幅度"
    ),
    "avg_vertical_oscillation": FieldUnitConfig(
        field_name="avg_vertical_oscillation",
        fit_unit=Unit.MILLIMETERS,
        display_unit=Unit.CENTIMETERS,
        scale_factor=0.1,
        reasonable_range=(3.0, 20.0),
        description="平均垂直振幅"
    ),
    "step_length": FieldUnitConfig(
        field_name="step_length",
        fit_unit=Unit.MILLIMETERS,
        display_unit=Unit.METERS,
        scale_factor=0.001,  # mm -> m
        reasonable_range=(0.4, 2.5),  # 正常范围0.8-1.5m
        description="步幅：单步移动距离"
    ),
    "avg_step_length": FieldUnitConfig(
        field_name="avg_step_length",
        fit_unit=Unit.MILLIMETERS,
        display_unit=Unit.METERS,
        scale_factor=0.001,
        reasonable_range=(0.4, 2.5),
        description="平均步幅"
    ),
    "stance_time": FieldUnitConfig(
        field_name="stance_time",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(150.0, 400.0),  # 正常范围200-300ms
        description="触地时间：脚接触地面的时间"
    ),
    "avg_stance_time": FieldUnitConfig(
        field_name="avg_stance_time",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(150.0, 400.0),
        description="平均触地时间"
    ),
    "stance_time_percent": FieldUnitConfig(
        field_name="stance_time_percent",
        fit_unit=Unit.PERCENT,
        display_unit=Unit.PERCENT,
        scale_factor=0.01,  # 百分比存储为 0-10000
        reasonable_range=(20.0, 50.0),
        description="触地时间百分比"
    ),
    "avg_stance_time_percent": FieldUnitConfig(
        field_name="avg_stance_time_percent",
        fit_unit=Unit.PERCENT,
        display_unit=Unit.PERCENT,
        scale_factor=0.01,
        reasonable_range=(20.0, 50.0),
        description="平均触地时间百分比"
    ),
    
    # GPS坐标
    "position_lat": FieldUnitConfig(
        field_name="position_lat",
        fit_unit=Unit.SEMICIRCLES,
        display_unit=Unit.DEGREES,
        scale_factor=(180.0 / (2**31)),  # semicircles -> degrees
        reasonable_range=(-90.0, 90.0),
        description="纬度"
    ),
    "position_long": FieldUnitConfig(
        field_name="position_long",
        fit_unit=Unit.SEMICIRCLES,
        display_unit=Unit.DEGREES,
        scale_factor=(180.0 / (2**31)),
        reasonable_range=(-180.0, 180.0),
        description="经度"
    ),
    
    # 速度配速
    "speed": FieldUnitConfig(
        field_name="speed",
        fit_unit=Unit.METERS_PER_SECOND,
        display_unit=Unit.METERS_PER_SECOND,
        scale_factor=0.001,  # mm/s -> m/s
        reasonable_range=(0.5, 15.0),  # 跑步0.5-10 m/s
        description="瞬时速度"
    ),
    "avg_speed": FieldUnitConfig(
        field_name="avg_speed",
        fit_unit=Unit.METERS_PER_SECOND,
        display_unit=Unit.METERS_PER_SECOND,
        scale_factor=0.001,
        reasonable_range=(0.5, 15.0),
        description="平均速度"
    ),
    "enhanced_speed": FieldUnitConfig(
        field_name="enhanced_speed",
        fit_unit=Unit.METERS_PER_SECOND,
        display_unit=Unit.METERS_PER_SECOND,
        scale_factor=0.001,
        reasonable_range=(0.5, 15.0),
        description="增强速度"
    ),
    "enhanced_avg_speed": FieldUnitConfig(
        field_name="enhanced_avg_speed",
        fit_unit=Unit.METERS_PER_SECOND,
        display_unit=Unit.METERS_PER_SECOND,
        scale_factor=0.001,
        reasonable_range=(0.5, 15.0),
        description="增强平均速度"
    ),
    
    # 心率
    "heart_rate": FieldUnitConfig(
        field_name="heart_rate",
        fit_unit=Unit.BPM,
        display_unit=Unit.BPM,
        scale_factor=1.0,
        reasonable_range=(40.0, 220.0),
        description="心率"
    ),
    "avg_heart_rate": FieldUnitConfig(
        field_name="avg_heart_rate",
        fit_unit=Unit.BPM,
        display_unit=Unit.BPM,
        scale_factor=1.0,
        reasonable_range=(40.0, 220.0),
        description="平均心率"
    ),
    "max_heart_rate": FieldUnitConfig(
        field_name="max_heart_rate",
        fit_unit=Unit.BPM,
        display_unit=Unit.BPM,
        scale_factor=1.0,
        reasonable_range=(40.0, 220.0),
        description="最大心率"
    ),
    
    # 步频
    "cadence": FieldUnitConfig(
        field_name="cadence",
        fit_unit=Unit.RPM,
        display_unit=Unit.SPM,
        scale_factor=2.0,  # RPM -> SPM (双脚)
        reasonable_range=(140.0, 220.0),  # 正常范围160-190
        description="步频"
    ),
    "avg_cadence": FieldUnitConfig(
        field_name="avg_cadence",
        fit_unit=Unit.RPM,
        display_unit=Unit.SPM,
        scale_factor=2.0,
        reasonable_range=(140.0, 220.0),
        description="平均步频"
    ),
    "max_cadence": FieldUnitConfig(
        field_name="max_cadence",
        fit_unit=Unit.RPM,
        display_unit=Unit.SPM,
        scale_factor=2.0,
        reasonable_range=(140.0, 220.0),
        description="最大步频"
    ),
    
    # 功率
    "power": FieldUnitConfig(
        field_name="power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(50.0, 1500.0),
        description="功率"
    ),
    "avg_power": FieldUnitConfig(
        field_name="avg_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(50.0, 1500.0),
        description="平均功率"
    ),
    "max_power": FieldUnitConfig(
        field_name="max_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(50.0, 1500.0),
        description="最大功率"
    ),
    
    # 高度
    "altitude": FieldUnitConfig(
        field_name="altitude",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=0.2,  # FIT存储为5倍
        reasonable_range=(-500.0, 9000.0),
        description="海拔高度"
    ),
    "enhanced_altitude": FieldUnitConfig(
        field_name="enhanced_altitude",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=0.2,
        reasonable_range=(-500.0, 9000.0),
        description="增强海拔"
    ),
    "total_ascent": FieldUnitConfig(
        field_name="total_ascent",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10000.0),
        description="累计爬升"
    ),
    "total_descent": FieldUnitConfig(
        field_name="total_descent",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10000.0),
        description="累计下降"
    ),
    
    # 距离
    "distance": FieldUnitConfig(
        field_name="distance",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=0.01,  # cm -> m
        reasonable_range=(0.0, 500000.0),
        description="距离"
    ),
    "total_distance": FieldUnitConfig(
        field_name="total_distance",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=0.01,
        reasonable_range=(0.0, 500000.0),
        description="总距离"
    ),
    
    # 卡路里
    "calories": FieldUnitConfig(
        field_name="calories",
        fit_unit=Unit.CALORIES,
        display_unit=Unit.CALORIES,
        scale_factor=1.0,
        reasonable_range=(0.0, 10000.0),
        description="卡路里"
    ),
    "total_calories": FieldUnitConfig(
        field_name="total_calories",
        fit_unit=Unit.CALORIES,
        display_unit=Unit.CALORIES,
        scale_factor=1.0,
        reasonable_range=(0.0, 10000.0),
        description="总卡路里"
    ),
}


# ============================================================================
# IQ字段单位配置（Connect IQ应用扩展字段）
# ============================================================================

IQ_FIELD_UNITS: Dict[str, FieldUnitConfig] = {
    # ============================================================================
    # 龙豆DragonValue 22个完整字段配置（保留dr_前缀）
    # ============================================================================
    "dr_timestamp": FieldUnitConfig(
        field_name="dr_timestamp",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(0.0, 100000.0),
        description="DR时间戳(ms)"
    ),
    "dr_distance": FieldUnitConfig(
        field_name="dr_distance",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=1.0,
        reasonable_range=(0.0, 100000.0),
        description="DR距离(m)"
    ),
    "dr_speed": FieldUnitConfig(
        field_name="dr_speed",
        fit_unit=Unit.METERS_PER_SECOND,
        display_unit=Unit.METERS_PER_SECOND,
        scale_factor=1.0,
        reasonable_range=(0.5, 15.0),
        description="DR速度(m/s)"
    ),
    "dr_cadence": FieldUnitConfig(
        field_name="dr_cadence",
        fit_unit=Unit.SPM,
        display_unit=Unit.SPM,
        scale_factor=1.0,
        reasonable_range=(140.0, 220.0),
        description="DR步频(spm)"
    ),
    "dr_stride": FieldUnitConfig(
        field_name="dr_stride",
        fit_unit=Unit.CENTIMETERS,
        display_unit=Unit.CENTIMETERS,
        scale_factor=1.0,
        reasonable_range=(50.0, 200.0),
        description="DR步幅(cm)"
    ),
    "dr_gct": FieldUnitConfig(
        field_name="dr_gct",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(150.0, 400.0),
        description="DR触地时间(ms)"
    ),
    "dr_air_time": FieldUnitConfig(
        field_name="dr_air_time",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(50.0, 300.0),
        description="DR腾空时间(ms)"
    ),
    "dr_v_osc": FieldUnitConfig(
        field_name="dr_v_osc",
        fit_unit=Unit.CENTIMETERS,
        display_unit=Unit.CENTIMETERS,
        scale_factor=1.0,
        reasonable_range=(3.0, 20.0),
        description="DR垂直振幅(cm)"
    ),
    "dr_vertical_ratio": FieldUnitConfig(
        field_name="dr_vertical_ratio",
        fit_unit=Unit.PERCENT,
        display_unit=Unit.PERCENT,
        scale_factor=1.0,
        reasonable_range=(0.0, 15.0),
        description="DR垂直步幅比(%)"
    ),
    "dr_ssl": FieldUnitConfig(
        field_name="dr_ssl",
        fit_unit=Unit.DIMENSIONLESS,
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 50.0),
        description="DR步速损失(cm/s)"
    ),
    "dr_ssl_percent": FieldUnitConfig(
        field_name="dr_ssl_percent",
        fit_unit=Unit.PERCENT,
        display_unit=Unit.PERCENT,
        scale_factor=1.0,
        reasonable_range=(0.0, 30.0),
        description="DR步速损失占比(%)"
    ),
    "dr_vertical_power": FieldUnitConfig(
        field_name="dr_vertical_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(0.0, 500.0),
        description="DR垂直功率(W)"
    ),
    "dr_propulsive_power": FieldUnitConfig(
        field_name="dr_propulsive_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(0.0, 500.0),
        description="DR前进功率(W)"
    ),
    "dr_slope_power": FieldUnitConfig(
        field_name="dr_slope_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(0.0, 500.0),
        description="DR坡度功率(W)"
    ),
    "dr_total_power": FieldUnitConfig(
        field_name="dr_total_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(0.0, 1000.0),
        description="DR总功率(W)"
    ),
    "dr_lss": FieldUnitConfig(
        field_name="dr_lss",
        fit_unit=Unit.DIMENSIONLESS,  # kN/m特殊单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(5.0, 25.0),
        description="DR下肢刚度(kN/m)"
    ),
    "dr_v_ilr": FieldUnitConfig(
        field_name="dr_v_ilr",
        fit_unit=Unit.DIMENSIONLESS,  # bw/s特殊单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(5.0, 30.0),
        description="DR垂直冲击力(bw/s)"
    ),
    "dr_h_ilr": FieldUnitConfig(
        field_name="dr_h_ilr",
        fit_unit=Unit.DIMENSIONLESS,  # bw/s特殊单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(5.0, 30.0),
        description="DR水平冲击力(bw/s)"
    ),
    "dr_v_pif": FieldUnitConfig(
        field_name="dr_v_pif",
        fit_unit=Unit.DIMENSIONLESS,  # g单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10.0),
        description="DR垂直冲击峰值(g)"
    ),
    "dr_h_pif": FieldUnitConfig(
        field_name="dr_h_pif",
        fit_unit=Unit.DIMENSIONLESS,  # g单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10.0),
        description="DR水平冲击峰值(g)"
    ),
    "dr_body_x_pif": FieldUnitConfig(
        field_name="dr_body_x_pif",
        fit_unit=Unit.DIMENSIONLESS,  # g单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10.0),
        description="DR传感器X轴冲击峰值(g)"
    ),
    "dr_body_y_pif": FieldUnitConfig(
        field_name="dr_body_y_pif",
        fit_unit=Unit.DIMENSIONLESS,  # g单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10.0),
        description="DR传感器Y轴冲击峰值(g)"
    ),
    "dr_body_z_pif": FieldUnitConfig(
        field_name="dr_body_z_pif",
        fit_unit=Unit.DIMENSIONLESS,  # g单位
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 10.0),
        description="DR传感器Z轴冲击峰值(g)"
    ),
    
    # ============================================================================
    # 其他IQ扩展字段（兼容旧版本，保留无dr_前缀的字段）
    # ============================================================================
    "v_osc": FieldUnitConfig(
        field_name="v_osc",
        fit_unit=Unit.CENTIMETERS,
        display_unit=Unit.CENTIMETERS,
        scale_factor=1.0,
        reasonable_range=(3.0, 20.0),
        description="垂直振幅(IQ)"
    ),
    "gct": FieldUnitConfig(
        field_name="gct",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(150.0, 400.0),
        description="触地时间(IQ)"
    ),
    "air_time": FieldUnitConfig(
        field_name="air_time",
        fit_unit=Unit.MILLISECONDS,
        display_unit=Unit.MILLISECONDS,
        scale_factor=1.0,
        reasonable_range=(50.0, 300.0),
        description="腾空时间(IQ)"
    ),
    "stride_length": FieldUnitConfig(
        field_name="stride_length",
        fit_unit=Unit.METERS,
        display_unit=Unit.METERS,
        scale_factor=1.0,
        reasonable_range=(0.8, 3.0),
        description="步幅(IQ)"
    ),
    "v_pif": FieldUnitConfig(
        field_name="v_pif",
        fit_unit=Unit.DIMENSIONLESS,
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(0.0, 100.0),
        description="垂直力峰值(IQ)"
    ),
    "bias": FieldUnitConfig(
        field_name="bias",
        fit_unit=Unit.PERCENT,
        display_unit=Unit.PERCENT,
        scale_factor=1.0,
        reasonable_range=(45.0, 55.0),
        description="左右平衡(IQ)"
    ),
    # Stryd功率计字段
    "form_power": FieldUnitConfig(
        field_name="form_power",
        fit_unit=Unit.WATTS,
        display_unit=Unit.WATTS,
        scale_factor=1.0,
        reasonable_range=(0.0, 500.0),
        description="形态功率(Stryd)"
    ),
    "leg_spring_stiffness": FieldUnitConfig(
        field_name="leg_spring_stiffness",
        fit_unit=Unit.DIMENSIONLESS,
        display_unit=Unit.DIMENSIONLESS,
        scale_factor=1.0,
        reasonable_range=(5.0, 20.0),
        description="腿部刚度(Stryd)"
    ),
}


# ============================================================================
# 合理范围快速查询表
# ============================================================================

FIELD_REASONABLE_RANGES: Dict[str, Tuple[float, float]] = {
    config.field_name: config.reasonable_range
    for config in list(STANDARD_FIELD_UNITS.values()) + list(IQ_FIELD_UNITS.values())
}


# ============================================================================
# 核心转换函数
# ============================================================================

def smart_unit_detection(field_name: str, value: float, 
                        reasonable_range: Tuple[float, float]) -> Optional[float]:
    """
    智能单位检测：基于合理范围自动推断单位并转换
    
    策略：尝试常见的缩放因子，看哪个能让值落入合理范围
    
    Args:
        field_name: 字段名
        value: 原始值
        reasonable_range: 合理范围(min, max)
        
    Returns:
        转换后的值，如果无法推断则返回None
    """
    min_val, max_val = reasonable_range
    
    # 检查原始值是否已在合理范围
    if min_val <= value <= max_val:
        logger.debug(f"{field_name}: 值{value}已在合理范围[{min_val}, {max_val}]")
        return value
    
    # 尝试常见的缩放因子
    scale_factors = [0.1, 0.01, 0.001, 10, 100, 1000]
    
    for scale in scale_factors:
        converted = value * scale
        if min_val <= converted <= max_val:
            logger.debug(f"{field_name}: 智能检测单位转换 {value} * {scale} = {converted}")
            return converted
    
    # 无法推断，记录debug信息
    logger.debug(
        f"{field_name}: 无法推断单位，值{value}无法通过常见缩放因子转换到合理范围[{min_val}, {max_val}]"
    )
    return None


def normalize_field_value(field_name: str, value: float, 
                         is_iq_field: bool = False) -> float:
    """
    字段值单位规范化（3层策略）
    
    策略：
    1. 配置驱动：查找字段配置，应用标准转换
    2. 元数据验证：检查FIT字段元数据（如果可用）
    3. 智能检测：基于合理范围自动推断单位
    
    Args:
        field_name: 字段名
        value: 原始值
        is_iq_field: 是否为IQ扩展字段
        
    Returns:
        转换后的值
    """
    if value is None:
        return None
    
    # 策略1: 配置驱动转换
    config_dict = IQ_FIELD_UNITS if is_iq_field else STANDARD_FIELD_UNITS
    
    if field_name in config_dict:
        config = config_dict[field_name]
        converted = value * config.scale_factor
        
        # 验证转换结果是否在合理范围
        min_val, max_val = config.reasonable_range
        if min_val <= converted <= max_val:
            logger.debug(
                f"{field_name}: 配置转换 {value} {config.fit_unit.value} "
                f"-> {converted:.2f} {config.display_unit.value}"
            )
            return converted
        else:
            logger.debug(
                f"{field_name}: 配置转换结果{converted}超出合理范围[{min_val}, {max_val}]，"
                f"尝试智能检测"
            )
            # 转换结果异常，回退到智能检测
            detected = smart_unit_detection(field_name, value, config.reasonable_range)
            if detected is not None:
                return detected
            # 智能检测也失败，返回原始配置转换结果
            return converted
    
    # 策略2: 元数据验证（当前fitdecode库支持有限，预留接口）
    # TODO: 未来可以从FIT message的field.units属性获取单位信息
    
    # 策略3: 智能检测（没有配置的字段）
    if field_name in FIELD_REASONABLE_RANGES:
        reasonable_range = FIELD_REASONABLE_RANGES[field_name]
        detected = smart_unit_detection(field_name, value, reasonable_range)
        if detected is not None:
            return detected
    
    # 无法转换，返回原值
    logger.debug(f"{field_name}: 无配置且无法智能检测，返回原值{value}")
    return value


# ============================================================================
# 便捷函数（向后兼容）
# ============================================================================

def normalize_vertical_oscillation(value: float, is_iq_field: bool = False) -> float:
    """垂直振幅单位转换（向后兼容接口）"""
    field_name = "v_osc" if is_iq_field else "vertical_oscillation"
    return normalize_field_value(field_name, value, is_iq_field)


def normalize_step_length(value: float) -> float:
    """步幅单位转换"""
    return normalize_field_value("step_length", value)


def normalize_stance_time(value: float) -> float:
    """触地时间单位转换"""
    return normalize_field_value("stance_time", value)


def normalize_gps_coordinate(coord_type: str, value: int) -> float:
    """GPS坐标转换（semicircles -> degrees）"""
    return normalize_field_value(coord_type, value)


# ============================================================================
# 测试代码
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 80)
    print("字段单位转换系统测试")
    print("=" * 80)
    
    # 测试1: 标准字段 - 垂直振幅（mm -> cm）
    print("\n测试1: 垂直振幅转换")
    test_values = [79.1, 68, 120]  # mm
    for val in test_values:
        result = normalize_field_value("vertical_oscillation", val)
        print(f"  {val} mm -> {result:.2f} cm")
    
    # 测试2: IQ字段 - 垂直振幅（可能已是cm）
    print("\n测试2: IQ垂直振幅转换")
    test_values = [6.8, 7.9, 80]  # 可能是cm或mm
    for val in test_values:
        result = normalize_field_value("v_osc", val, is_iq_field=True)
        print(f"  {val} -> {result:.2f} cm")
    
    # 测试3: 步幅转换（mm -> m）
    print("\n测试3: 步幅转换")
    test_values = [1200, 1500, 900]  # mm
    for val in test_values:
        result = normalize_field_value("step_length", val)
        print(f"  {val} mm -> {result:.3f} m")
    
    # 测试4: GPS坐标转换
    print("\n测试4: GPS坐标转换")
    lat_semicircles = 429496729  # 示例
    result = normalize_field_value("position_lat", lat_semicircles)
    print(f"  {lat_semicircles} semicircles -> {result:.6f} degrees")
    
    # 输出配置统计
    print("\n" + "=" * 80)
    print("配置统计:")
    print(f"  标准字段: {len(STANDARD_FIELD_UNITS)} 个")
    print(f"  IQ字段: {len(IQ_FIELD_UNITS)} 个")
    print(f"  总计: {len(STANDARD_FIELD_UNITS) + len(IQ_FIELD_UNITS)} 个")
    print("=" * 80)
