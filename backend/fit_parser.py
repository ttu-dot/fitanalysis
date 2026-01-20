"""
FIT跑步数据分析器 - FIT文件解析器
动态提取所有字段，包括IQ扩展字段
"""
import fitdecode
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import math

from models import Activity, Record, Lap, Session
from field_units import normalize_field_value, normalize_vertical_oscillation


# Garmin FIT 使用的坐标转换常量
SEMICIRCLE_TO_DEGREE = 180.0 / (2 ** 31)


def semicircles_to_degrees(semicircles: int) -> float:
    """将 semicircles 转换为度"""
    if semicircles is None:
        return None
    return semicircles * SEMICIRCLE_TO_DEGREE


# 注意: normalize_vertical_oscillation() 已移至 field_units.py 模块
# 现在使用 normalize_field_value() 进行所有字段的单位转换


def speed_to_pace(speed_mps: float) -> str:
    """将速度(m/s)转换为配速(min/km)"""
    if speed_mps is None or speed_mps <= 0:
        return "--:--"
    pace_seconds = 1000 / speed_mps
    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def get_field_value(frame, field_name: str, default=None):
    """安全获取FIT frame字段值"""
    try:
        field = frame.get_field(field_name)
        if field is not None and field.value is not None:
            return field.value
    except (KeyError, AttributeError):
        pass
    return default


# 龙豆(DragonRun)字段映射 - 将dr_前缀字段映射为保留dr_前缀的IQ字段名
# 扩展支持22个完整字段，避免与标准FIT字段命名冲突
DR_FIELD_MAPPING = {
    'dr_timestamp': 'dr_timestamp',           # 0. 时间戳 (ms)
    'dr_distance': 'dr_distance',             # 1. 距离 (m)
    'dr_speed': 'dr_speed',                   # 2. 速度 (m/s)
    'dr_cadence': 'dr_cadence',               # 3. 步频 (spm)
    'dr_stride': 'dr_stride',                 # 4. 步幅 (cm)
    'dr_stance': 'dr_gct',                    # 5. 触地时间 (ms) - Ground Contact Time
    'dr_air': 'dr_air_time',                  # 6. 腾空时间 (ms)
    'dr_vertical_osc': 'dr_v_osc',            # 7. 垂直振幅 (cm)
    'dr_vertical_ratio': 'dr_vertical_ratio', # 8. 垂直步幅比 (%)
    'dr_ssl': 'dr_ssl',                       # 9. 步速损失 (cm/s)
    'dr_ssl%': 'dr_ssl_percent',              # 10. 步速损失占比 (%)
    'dr_vertical_power': 'dr_vertical_power', # 11. 垂直功率 (W)
    'dr_propulsive_power': 'dr_propulsive_power', # 12. 前进功率 (W)
    'dr_slop_power': 'dr_slope_power',        # 13. 坡度功率 (W)
    'dr_total_power': 'dr_total_power',       # 14. 总功率 (W)
    'dr_lss': 'dr_lss',                       # 15. 下肢刚度 (kN/m)
    'dr_v_ilr': 'dr_v_ilr',                   # 16. 垂直冲击力 (bw/s)
    'dr_h_ilr': 'dr_h_ilr',                   # 17. 水平冲击力 (bw/s)
    'dr_v_pif': 'dr_v_pif',                   # 18. 垂直冲击峰值 (g)
    'dr_h_pif': 'dr_h_pif',                   # 19. 水平冲击峰值 (g)
    'dr_body_x_pif': 'dr_body_x_pif',         # 20. 传感器X轴冲击峰值 (g)
    'dr_body_y_pif': 'dr_body_y_pif',         # 21. 传感器Y轴冲击峰值 (g)
    'dr_body_z_pif': 'dr_body_z_pif',         # 22. 传感器Z轴冲击峰值 (g)
}


def extract_developer_fields(frame) -> Dict[str, Any]:
    """提取开发者字段（IQ扩展字段），包括龙豆跑步dr_字段"""
    iq_fields = {}
    try:
        if hasattr(frame, 'fields'):
            for field in frame.fields:
                field_name_raw = str(field.name) if hasattr(field, 'name') else ''
                field_name_lower = field_name_raw.lower()
                
                # 方法1: 龙豆跑步字段 (dr_ 前缀)
                if field_name_lower.startswith('dr_') and field.value is not None:
                    # 使用映射后的名称（保留dr_前缀）
                    mapped_name = DR_FIELD_MAPPING.get(field_name_lower, field_name_lower)
                    field_value = field.value
                    
                    # 所有DR字段统一由配置系统处理，不做特殊转换
                    iq_fields[mapped_name] = field_value
                    continue
                
                # 方法2: 检查 is_dev_field 属性
                is_dev = False
                
                if hasattr(field, 'is_dev_field') and field.is_dev_field:
                    is_dev = True
                elif hasattr(field, 'field'):
                    if hasattr(field.field, 'is_dev_field') and field.field.is_dev_field:
                        is_dev = True
                    # 方法3: 检查 field_def 是否是开发者字段定义
                    elif hasattr(field.field, 'def_num') and field.field.def_num is None:
                        is_dev = True
                
                # 方法4: 检查字段名是否包含 Connect IQ 相关关键词
                if not is_dev:
                    if any(kw in field_name_lower for kw in ['connect_iq', 'developer', 'iq_', 'bias', 'longdou', 'dragon']):
                        is_dev = True
                
                if is_dev and field.value is not None:
                    # 清理字段名
                    clean_name = field_name_raw.replace(' ', '_').replace('(', '').replace(')', '').lower()
                    
                    # IQ字段特殊处理：v_osc垂直振幅转换
                    if clean_name == 'v_osc':
                        iq_fields[clean_name] = normalize_field_value('v_osc', field.value, is_iq_field=True)
                    else:
                        iq_fields[clean_name] = field.value
    except Exception as e:
        pass
    return iq_fields


def parse_record_message(frame) -> Record:
    """解析 record 消息（秒级数据）"""
    record = Record()
    
    # 基础字段
    record.timestamp = get_field_value(frame, 'timestamp')
    record.elapsed_time = get_field_value(frame, 'elapsed_time')
    record.distance = get_field_value(frame, 'distance')
    record.heart_rate = get_field_value(frame, 'heart_rate')
    
    # 速度 - 优先使用 enhanced_speed
    speed = get_field_value(frame, 'speed')
    enhanced_speed = get_field_value(frame, 'enhanced_speed')
    record.speed = enhanced_speed if enhanced_speed is not None else speed
    
    # 步频 - 跑步时FIT存储的是单腿步频，需要*2
    cadence = get_field_value(frame, 'cadence')
    if cadence is not None:
        record.cadence = cadence * 2  # 转换为双腿步频
    
    record.power = get_field_value(frame, 'power')
    
    # 海拔
    altitude = get_field_value(frame, 'altitude')
    enhanced_altitude = get_field_value(frame, 'enhanced_altitude')
    record.altitude = enhanced_altitude if enhanced_altitude is not None else altitude
    
    # GPS坐标
    lat = get_field_value(frame, 'position_lat')
    long = get_field_value(frame, 'position_long')
    record.position_lat = semicircles_to_degrees(lat) if lat else None
    record.position_long = semicircles_to_degrees(long) if long else None
    
    # 其他字段
    record.grade = get_field_value(frame, 'grade')
    record.temperature = get_field_value(frame, 'temperature')
    
    # 垂直振幅 - 使用配置化转换系统
    vertical_osc = get_field_value(frame, 'vertical_oscillation')
    record.vertical_oscillation = normalize_field_value('vertical_oscillation', vertical_osc)
    
    record.vertical_ratio = get_field_value(frame, 'vertical_ratio')
    record.stance_time = get_field_value(frame, 'stance_time')
    record.stance_time_balance = get_field_value(frame, 'stance_time_balance')
    record.step_length = get_field_value(frame, 'step_length')
    record.fractional_cadence = get_field_value(frame, 'fractional_cadence')
    
    # IQ扩展字段
    record.iq_fields = extract_developer_fields(frame)
    
    return record


def parse_lap_message(frame, lap_number: int) -> Lap:
    """解析 lap 消息（每圈汇总）"""
    lap = Lap(lap_number=lap_number)
    
    lap.start_time = get_field_value(frame, 'start_time')
    lap.total_elapsed_time = get_field_value(frame, 'total_elapsed_time')
    lap.total_distance = get_field_value(frame, 'total_distance')
    
    lap.avg_heart_rate = get_field_value(frame, 'avg_heart_rate')
    lap.max_heart_rate = get_field_value(frame, 'max_heart_rate')
    
    lap.avg_speed = get_field_value(frame, 'avg_speed')
    enhanced_avg_speed = get_field_value(frame, 'enhanced_avg_speed')
    if enhanced_avg_speed is not None:
        lap.avg_speed = enhanced_avg_speed
    
    lap.max_speed = get_field_value(frame, 'max_speed')
    enhanced_max_speed = get_field_value(frame, 'enhanced_max_speed')
    if enhanced_max_speed is not None:
        lap.max_speed = enhanced_max_speed
    
    # 步频
    avg_cadence = get_field_value(frame, 'avg_cadence')
    if avg_cadence is not None:
        lap.avg_cadence = avg_cadence * 2
    max_cadence = get_field_value(frame, 'max_cadence')
    if max_cadence is not None:
        lap.max_cadence = max_cadence * 2
    
    lap.avg_power = get_field_value(frame, 'avg_power')
    lap.max_power = get_field_value(frame, 'max_power')
    
    lap.total_ascent = get_field_value(frame, 'total_ascent')
    lap.total_descent = get_field_value(frame, 'total_descent')
    
    # 垂直振幅 - 使用配置化转换系统
    avg_vertical_osc = get_field_value(frame, 'avg_vertical_oscillation')
    lap.avg_vertical_oscillation = normalize_field_value('avg_vertical_oscillation', avg_vertical_osc)
    
    lap.avg_stance_time = get_field_value(frame, 'avg_stance_time')
    lap.avg_step_length = get_field_value(frame, 'avg_step_length')
    
    lap.total_calories = get_field_value(frame, 'total_calories')
    
    # IQ扩展字段
    lap.iq_fields = extract_developer_fields(frame)
    
    return lap


def parse_session_message(frame) -> Session:
    """解析 session 消息（整体汇总）"""
    session = Session()
    
    sport = get_field_value(frame, 'sport')
    if sport is not None:
        session.sport = str(sport).lower() if hasattr(sport, 'lower') else str(sport)
    
    sub_sport = get_field_value(frame, 'sub_sport')
    if sub_sport is not None:
        session.sub_sport = str(sub_sport)
    
    session.start_time = get_field_value(frame, 'start_time')
    session.total_elapsed_time = get_field_value(frame, 'total_elapsed_time')
    session.total_timer_time = get_field_value(frame, 'total_timer_time')
    session.total_distance = get_field_value(frame, 'total_distance')
    
    session.avg_heart_rate = get_field_value(frame, 'avg_heart_rate')
    session.max_heart_rate = get_field_value(frame, 'max_heart_rate')
    
    session.avg_speed = get_field_value(frame, 'avg_speed')
    enhanced_avg_speed = get_field_value(frame, 'enhanced_avg_speed')
    if enhanced_avg_speed is not None:
        session.avg_speed = enhanced_avg_speed
    
    session.max_speed = get_field_value(frame, 'max_speed')
    enhanced_max_speed = get_field_value(frame, 'enhanced_max_speed')
    if enhanced_max_speed is not None:
        session.max_speed = enhanced_max_speed
    
    # 步频
    avg_cadence = get_field_value(frame, 'avg_cadence')
    if avg_cadence is not None:
        session.avg_cadence = avg_cadence * 2
    max_cadence = get_field_value(frame, 'max_cadence')
    if max_cadence is not None:
        session.max_cadence = max_cadence * 2
    
    session.avg_power = get_field_value(frame, 'avg_power')
    session.max_power = get_field_value(frame, 'max_power')
    
    session.total_ascent = get_field_value(frame, 'total_ascent')
    session.total_descent = get_field_value(frame, 'total_descent')
    session.total_calories = get_field_value(frame, 'total_calories')
    
    session.avg_temperature = get_field_value(frame, 'avg_temperature')
    
    # 垂直振幅 - 使用配置化转换系统
    avg_vertical_osc = get_field_value(frame, 'avg_vertical_oscillation')
    session.avg_vertical_oscillation = normalize_field_value('avg_vertical_oscillation', avg_vertical_osc)
    
    session.avg_stance_time = get_field_value(frame, 'avg_stance_time')
    session.avg_step_length = get_field_value(frame, 'avg_step_length')
    
    # IQ扩展字段
    session.iq_fields = extract_developer_fields(frame)
    
    return session


def collect_available_fields(records: List[Record], laps: List[Lap], session: Session) -> Tuple[List[str], List[str]]:
    """收集所有可用字段
    
    注意: 
    - 只收集records中的IQ字段（时间序列数据），用于趋势图
    - 排除lap/session汇总字段（如lap_avg_*, s_avg_*），这些是统计值不适合趋势图
    - 只收集至少有一个非空值的字段
    """
    standard_fields = set()
    iq_fields_with_values = {}  # {field_name: has_value}
    
    # 从records收集
    if records:
        sample = records[0]
        # fractional_cadence 不加入available_fields，因为它不是独立有意义的字段
        # 而是步频的小数部分，不应在UI中单独显示
        for field in ['elapsed_time', 'distance', 'heart_rate', 'speed', 'cadence', 
                      'power', 'altitude', 'grade', 'temperature', 'vertical_oscillation',
                      'vertical_ratio', 'stance_time', 'stance_time_balance', 'step_length',
                      'position_lat', 'position_long']:
            if getattr(sample, field, None) is not None:
                standard_fields.add(field)
        
        # 收集records中的IQ字段，并检查是否有非空值
        for record in records:
            for field_name, field_value in record.iq_fields.items():
                # 跳过lap/session汇总字段（以lap_、s_开头）
                if field_name.startswith('lap_') or field_name.startswith('s_'):
                    continue
                
                # 如果字段第一次出现，初始化为False
                if field_name not in iq_fields_with_values:
                    iq_fields_with_values[field_name] = False
                
                # 如果有非空值，标记为True
                if field_value is not None:
                    iq_fields_with_values[field_name] = True
    
    # 只保留有非空值的IQ字段
    iq_fields = {field for field, has_value in iq_fields_with_values.items() if has_value}
    
    return sorted(list(standard_fields)), sorted(list(iq_fields))


def parse_fit_file(file_path: str, activity_id: str, activity_name: str = None) -> Activity:
    """
    解析FIT文件，返回Activity对象
    
    Args:
        file_path: FIT文件路径
        activity_id: 活动ID
        activity_name: 活动名称（可选）
    
    Returns:
        Activity对象
    """
    file_path = Path(file_path)
    
    if activity_name is None:
        activity_name = file_path.stem
    
    records: List[Record] = []
    laps: List[Lap] = []
    session: Session = Session()
    lap_counter = 0
    
    with fitdecode.FitReader(str(file_path)) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            
            if frame.name == 'record':
                record = parse_record_message(frame)
                if record.timestamp is not None or record.elapsed_time is not None:
                    records.append(record)
            
            elif frame.name == 'lap':
                lap_counter += 1
                lap = parse_lap_message(frame, lap_counter)
                laps.append(lap)
            
            elif frame.name == 'session':
                session = parse_session_message(frame)
    
    # 收集可用字段
    available_fields, available_iq_fields = collect_available_fields(records, laps, session)
    
    # 创建Activity对象
    activity = Activity(
        id=activity_id,
        name=activity_name,
        file_name=file_path.name,
        created_at=datetime.now(),
        session=session,
        laps=laps,
        records=records,
        available_fields=available_fields,
        available_iq_fields=available_iq_fields
    )
    
    return activity


def parse_fit_bytes(file_bytes: bytes, file_name: str, activity_id: str, activity_name: str = None) -> Activity:
    """
    从字节流解析FIT文件
    
    Args:
        file_bytes: FIT文件字节内容
        file_name: 原始文件名
        activity_id: 活动ID
        activity_name: 活动名称（可选）
    
    Returns:
        Activity对象
    """
    import io
    
    if activity_name is None:
        activity_name = Path(file_name).stem
    
    records: List[Record] = []
    laps: List[Lap] = []
    session: Session = Session()
    lap_counter = 0
    start_timestamp = None
    all_iq_field_names = set()  # 收集所有IQ字段名
    
    with fitdecode.FitReader(io.BytesIO(file_bytes)) as fit:
        for frame in fit:
            if not isinstance(frame, fitdecode.FitDataMessage):
                continue
            
            if frame.name == 'record':
                record = parse_record_message(frame)
                
                # 收集IQ字段名
                all_iq_field_names.update(record.iq_fields.keys())
                
                if record.timestamp is not None or record.distance is not None:
                    records.append(record)
            
            elif frame.name == 'lap':
                lap_counter += 1
                lap = parse_lap_message(frame, lap_counter)
                laps.append(lap)
                all_iq_field_names.update(lap.iq_fields.keys())
            
            elif frame.name == 'session':
                session = parse_session_message(frame)
                all_iq_field_names.update(session.iq_fields.keys())
    
    # 计算 elapsed_time（如果缺失）
    if records:
        # 找到第一个有效的timestamp作为起点
        for r in records:
            if r.timestamp is not None:
                start_timestamp = r.timestamp
                break
        
        # 为每个record计算elapsed_time
        for i, record in enumerate(records):
            if record.elapsed_time is None:
                if record.timestamp is not None and start_timestamp is not None:
                    delta = record.timestamp - start_timestamp
                    record.elapsed_time = delta.total_seconds()
                elif record.distance is not None and session.avg_speed and session.avg_speed > 0:
                    # 根据距离和平均速度估算时间
                    record.elapsed_time = record.distance / session.avg_speed
                else:
                    # 使用索引作为秒数（假设1秒1条记录）
                    record.elapsed_time = float(i)
    
    # 收集可用字段
    available_fields, available_iq_fields = collect_available_fields(records, laps, session)
    
    # 创建Activity对象
    activity = Activity(
        id=activity_id,
        name=activity_name,
        file_name=file_name,
        created_at=datetime.now(),
        session=session,
        laps=laps,
        records=records,
        available_fields=available_fields,
        available_iq_fields=available_iq_fields
    )
    
    return activity
