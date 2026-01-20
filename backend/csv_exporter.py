"""
FIT跑步数据分析器 - CSV导出模块
支持merged和categorized两种导出模式
"""
import csv
import io
import zipfile
from datetime import datetime
from typing import List, Optional, Dict, Any

from models import Activity, Record, Lap, Session


def format_timestamp(ts: datetime) -> str:
    """格式化时间戳"""
    if ts is None:
        return ""
    return ts.strftime("%Y-%m-%d %H:%M:%S")


def format_pace(speed_mps: float) -> str:
    """将速度(m/s)转换为配速(min/km)"""
    if speed_mps is None or speed_mps <= 0:
        return ""
    pace_seconds = 1000 / speed_mps
    minutes = int(pace_seconds // 60)
    seconds = int(pace_seconds % 60)
    return f"{minutes}:{seconds:02d}"


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds is None:
        return ""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def record_to_dict(record: Record, include_fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """将Record转换为字典"""
    data = {
        "timestamp": format_timestamp(record.timestamp),
        "elapsed_time": record.elapsed_time,
        "elapsed_time_formatted": format_duration(record.elapsed_time) if record.elapsed_time is not None else "",
        "distance_m": record.distance,
        "distance_km": round(record.distance / 1000, 3) if record.distance is not None else None,
        "heart_rate_bpm": record.heart_rate,
        "speed_mps": record.speed,
        "pace_min_km": format_pace(record.speed) if record.speed is not None else "",
        "cadence_spm": record.cadence,
        "power_w": record.power,
        "altitude_m": record.altitude,
        "latitude": record.position_lat,
        "longitude": record.position_long,
        "grade_percent": record.grade,
        "temperature_c": record.temperature,
        "vertical_oscillation_cm": record.vertical_oscillation,
        "stance_time_ms": record.stance_time,
        "stance_time_balance_percent": record.stance_time_balance,
        "step_length_m": record.step_length,
    }
    
    # 添加IQ字段
    for key, value in record.iq_fields.items():
        data[f"iq_{key}"] = value
    
    # 如果指定了字段列表，只返回这些字段
    if include_fields:
        data = {k: v for k, v in data.items() if k in include_fields or k == "timestamp" or k == "elapsed_time"}
    
    return data


def lap_to_dict(lap: Lap) -> Dict[str, Any]:
    """将Lap转换为字典"""
    data = {
        "lap_number": lap.lap_number,
        "start_time": format_timestamp(lap.start_time),
        "total_elapsed_time_sec": lap.total_elapsed_time,
        "total_elapsed_time_formatted": format_duration(lap.total_elapsed_time) if lap.total_elapsed_time else "",
        "total_distance_m": lap.total_distance,
        "total_distance_km": round(lap.total_distance / 1000, 3) if lap.total_distance else None,
        "avg_pace_min_km": format_pace(lap.avg_speed) if lap.avg_speed else "",
        "avg_heart_rate_bpm": lap.avg_heart_rate,
        "max_heart_rate_bpm": lap.max_heart_rate,
        "avg_speed_mps": lap.avg_speed,
        "max_speed_mps": lap.max_speed,
        "avg_cadence_spm": lap.avg_cadence,
        "max_cadence_spm": lap.max_cadence,
        "avg_power_w": lap.avg_power,
        "max_power_w": lap.max_power,
        "total_ascent_m": lap.total_ascent,
        "total_descent_m": lap.total_descent,
        "avg_vertical_oscillation_cm": lap.avg_vertical_oscillation,
        "avg_stance_time_ms": lap.avg_stance_time,
        "avg_step_length_m": lap.avg_step_length,
        "total_calories": lap.total_calories,
    }
    
    # 添加IQ字段
    for key, value in lap.iq_fields.items():
        data[f"iq_{key}"] = value
    
    return data


def session_to_dict(session: Session) -> Dict[str, Any]:
    """将Session转换为字典"""
    data = {
        "sport": session.sport,
        "sub_sport": session.sub_sport,
        "start_time": format_timestamp(session.start_time),
        "total_elapsed_time_sec": session.total_elapsed_time,
        "total_elapsed_time_formatted": format_duration(session.total_elapsed_time) if session.total_elapsed_time else "",
        "total_timer_time_sec": session.total_timer_time,
        "total_distance_m": session.total_distance,
        "total_distance_km": round(session.total_distance / 1000, 3) if session.total_distance else None,
        "avg_pace_min_km": format_pace(session.avg_speed) if session.avg_speed else "",
        "avg_heart_rate_bpm": session.avg_heart_rate,
        "max_heart_rate_bpm": session.max_heart_rate,
        "avg_speed_mps": session.avg_speed,
        "max_speed_mps": session.max_speed,
        "avg_cadence_spm": session.avg_cadence,
        "max_cadence_spm": session.max_cadence,
        "avg_power_w": session.avg_power,
        "max_power_w": session.max_power,
        "total_ascent_m": session.total_ascent,
        "total_descent_m": session.total_descent,
        "total_calories": session.total_calories,
        "avg_temperature_c": session.avg_temperature,
        "avg_vertical_oscillation_cm": session.avg_vertical_oscillation,
        "avg_stance_time_ms": session.avg_stance_time,
        "avg_step_length_m": session.avg_step_length,
    }
    
    # 添加IQ字段
    for key, value in session.iq_fields.items():
        data[f"iq_{key}"] = value
    
    return data


def write_csv(data: List[Dict[str, Any]], output: io.StringIO):
    """将数据写入CSV"""
    if not data:
        return
    
    # 获取所有字段（合并所有记录的keys，因为不同记录可能有不同的IQ字段）
    fieldnames_set = set()
    for record in data:
        fieldnames_set.update(record.keys())
    fieldnames = sorted(list(fieldnames_set))
    
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)


def export_merged_csv(activity: Activity, include_fields: Optional[List[str]] = None) -> str:
    """
    导出合并的CSV文件（只包含records）
    
    Args:
        activity: Activity对象
        include_fields: 要包含的字段列表（可选）
    
    Returns:
        CSV内容字符串
    """
    output = io.StringIO()
    records_data = [record_to_dict(r, include_fields) for r in activity.records]
    write_csv(records_data, output)
    return output.getvalue()


def export_categorized_zip(activity: Activity) -> bytes:
    """
    导出分类的ZIP文件（包含records.csv, laps.csv, session.csv）
    
    Args:
        activity: Activity对象
    
    Returns:
        ZIP文件字节内容
    """
    zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Records CSV
        records_output = io.StringIO()
        records_data = [record_to_dict(r) for r in activity.records]
        write_csv(records_data, records_output)
        zip_file.writestr("records.csv", records_output.getvalue())
        
        # Laps CSV
        laps_output = io.StringIO()
        laps_data = [lap_to_dict(lap) for lap in activity.laps]
        write_csv(laps_data, laps_output)
        zip_file.writestr("laps.csv", laps_output.getvalue())
        
        # Session CSV
        session_output = io.StringIO()
        session_data = [session_to_dict(activity.session)]
        write_csv(session_data, session_output)
        zip_file.writestr("session.csv", session_output.getvalue())
    
    return zip_buffer.getvalue()


def export_laps_csv(activity: Activity) -> str:
    """
    导出每圈数据CSV
    
    Args:
        activity: Activity对象
    
    Returns:
        CSV内容字符串
    """
    output = io.StringIO()
    laps_data = [lap_to_dict(lap) for lap in activity.laps]
    write_csv(laps_data, output)
    return output.getvalue()
