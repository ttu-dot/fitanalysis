"""
FIT跑步数据分析器 - 数据模型定义
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional
from datetime import datetime


class Record(BaseModel):
    """秒级记录数据"""
    timestamp: Optional[datetime] = None
    elapsed_time: Optional[float] = None  # 累计时间(秒)
    distance: Optional[float] = None  # 累计距离(米)
    heart_rate: Optional[int] = None  # 心率(bpm)
    speed: Optional[float] = None  # 速度(m/s)
    cadence: Optional[int] = None  # 步频(spm), 跑步时需要*2
    power: Optional[int] = None  # 功率(W)
    altitude: Optional[float] = None  # 海拔(米)
    position_lat: Optional[float] = None  # 纬度
    position_long: Optional[float] = None  # 经度
    grade: Optional[float] = None  # 坡度(%)
    temperature: Optional[int] = None  # 温度(°C)
    vertical_oscillation: Optional[float] = None  # 垂直振幅(cm)
    vertical_ratio: Optional[float] = None  # 垂直振幅比(%)
    stance_time: Optional[float] = None  # 触地时间(ms)
    stance_time_balance: Optional[float] = None  # 触地平衡(%)
    step_length: Optional[float] = None  # 步幅(m)
    fractional_cadence: Optional[float] = None  # 小数步频
    # 动态IQ字段 - 存储所有扩展字段
    iq_fields: Dict[str, Any] = Field(default_factory=dict)


class Lap(BaseModel):
    """每圈汇总数据"""
    lap_number: int = 0
    start_time: Optional[datetime] = None
    total_elapsed_time: Optional[float] = None  # 圈用时(秒)
    total_distance: Optional[float] = None  # 圈距离(米)
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    avg_cadence: Optional[int] = None
    max_cadence: Optional[int] = None
    avg_power: Optional[int] = None
    max_power: Optional[int] = None
    total_ascent: Optional[float] = None
    total_descent: Optional[float] = None
    avg_vertical_oscillation: Optional[float] = None
    avg_stance_time: Optional[float] = None
    avg_step_length: Optional[float] = None
    total_calories: Optional[int] = None
    # 动态IQ字段汇总
    iq_fields: Dict[str, Any] = Field(default_factory=dict)


class Session(BaseModel):
    """整体会话汇总"""
    sport: str = "running"
    sub_sport: Optional[str] = None
    start_time: Optional[datetime] = None
    total_elapsed_time: Optional[float] = None
    total_timer_time: Optional[float] = None
    total_distance: Optional[float] = None
    avg_heart_rate: Optional[int] = None
    max_heart_rate: Optional[int] = None
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    avg_cadence: Optional[int] = None
    max_cadence: Optional[int] = None
    avg_power: Optional[int] = None
    max_power: Optional[int] = None
    total_ascent: Optional[float] = None
    total_descent: Optional[float] = None
    total_calories: Optional[int] = None
    avg_temperature: Optional[int] = None
    avg_vertical_oscillation: Optional[float] = None
    avg_stance_time: Optional[float] = None
    avg_step_length: Optional[float] = None
    # 动态IQ字段
    iq_fields: Dict[str, Any] = Field(default_factory=dict)


class HrMergeOptions(BaseModel):
    """离线心率合并参数（可选覆盖默认配置）"""
    auto_align_max_shift_sec: Optional[float] = None
    auto_align_match_tolerance_sec: Optional[float] = None
    auto_align_min_match_ratio: Optional[float] = None
    interpolate_max_gap_sec: Optional[float] = None
    allow_extrapolation: Optional[bool] = None


class MergeSource(BaseModel):
    """合并来源信息（活动级别溯源）"""
    file_name: Optional[str] = None
    device_name: Optional[str] = None


class MergeCriteria(BaseModel):
    """本次合并生效的阈值配置（用于UI展示与回溯）"""
    auto_align_max_shift_sec: Optional[float] = None
    auto_align_match_tolerance_sec: Optional[float] = None
    auto_align_min_match_ratio: Optional[float] = None
    interpolate_max_gap_sec: Optional[float] = None
    allow_extrapolation: Optional[bool] = None


class MergeStats(BaseModel):
    """合并统计信息"""
    offset_sec: Optional[float] = None
    match_ratio: Optional[float] = None
    interp_ratio: Optional[float] = None
    dropped_ratio: Optional[float] = None


class MergeProvenance(BaseModel):
    """合并溯源（活动级别）"""
    version: str = "1"
    method: str = "none"  # metadata_align | linear_interpolate | none
    decision: str = "auto"  # auto | manual
    sources: List[MergeSource] = Field(default_factory=list)
    criteria: Optional[MergeCriteria] = None
    stats: Optional[MergeStats] = None


class Activity(BaseModel):
    """完整活动数据"""
    id: str
    name: str
    file_name: str
    created_at: datetime
    session: Session
    laps: List[Lap] = Field(default_factory=list)
    records: List[Record] = Field(default_factory=list)
    available_fields: List[str] = Field(default_factory=list)
    available_iq_fields: List[str] = Field(default_factory=list)
    merge_provenance: Optional[MergeProvenance] = None


class ActivityMeta(BaseModel):
    """活动索引元数据（用于列表展示）"""
    id: str
    name: str
    date: Optional[datetime] = None
    sport: str = "running"
    distance_km: float = 0.0
    duration_sec: float = 0.0
    avg_pace: str = "--:--"  # 格式: "5:30"
    avg_heart_rate: Optional[int] = None
    avg_cadence: Optional[int] = None
    avg_power: Optional[int] = None
    total_ascent: Optional[float] = None
    available_fields: List[str] = Field(default_factory=list)
    available_iq_fields: List[str] = Field(default_factory=list)


class ActivityIndex(BaseModel):
    """活动索引文件结构"""
    activities: List[ActivityMeta] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=datetime.now)


# API 请求/响应模型

class UploadResponse(BaseModel):
    """上传响应"""
    success: bool
    activity_id: Optional[str] = None
    message: str
    summary: Optional[Dict[str, Any]] = None


class ActivityListResponse(BaseModel):
    """活动列表响应"""
    activities: List[ActivityMeta]
    total: int
    page: int
    limit: int


class CompareRequest(BaseModel):
    """多活动对比请求"""
    activity_ids: List[str]
    fields: List[str]
    align_by: str = "time"  # "time" 或 "distance"


class CompareActivityData(BaseModel):
    """对比活动数据"""
    id: str
    name: str
    date: Optional[datetime] = None
    data: List[Dict[str, Any]]


class CompareResponse(BaseModel):
    """多活动对比响应"""
    activities: List[CompareActivityData]
    align_by: str
    x_label: str
    fields: List[str]


class ExportRequest(BaseModel):
    """导出请求参数"""
    mode: str = "merged"  # "merged" 或 "categorized"
    fields: Optional[List[str]] = None
    include_records: bool = True
    include_laps: bool = True
    include_session: bool = True
