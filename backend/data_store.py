"""
FIT跑步数据分析器 - 数据存储管理
管理活动数据的持久化存储和索引
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
import shutil

from models import Activity, ActivityMeta, ActivityIndex
from fit_parser import speed_to_pace


class DataStore:
    """活动数据存储管理器"""
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.activities_dir = self.data_dir / "activities"
        self.index_file = self.data_dir / "index.json"
        
        # 确保目录存在
        self.activities_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化索引
        if not self.index_file.exists():
            self._save_index(ActivityIndex())
    
    def _load_index(self) -> ActivityIndex:
        """加载活动索引，如果索引损坏则尝试从磁盘重建"""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                try:
                    return ActivityIndex(**data)
                except Exception as e:
                    # 兼容：index.json 可能被旧版本/异常写入为无效时间字符串（如 updated_at: ""）
                    print(f"警告: 索引文件验证失败: {e}，尝试修复...")
                    if isinstance(data, dict):
                        updated_at = data.get('updated_at')
                        if not updated_at:
                            data['updated_at'] = datetime.now().isoformat()
                        try:
                            index = ActivityIndex(**data)
                            # 尝试回写修复后的索引，避免后续启动再次失败
                            print(f"成功修复索引文件，包含 {len(index.activities)} 个活动")
                            self._save_index(index)
                            return index
                        except Exception as e2:
                            print(f"索引修复失败: {e2}，尝试从磁盘重建...")
                    # 如果修复失败，尝试从activities目录重建索引
                    return self._rebuild_index_from_disk()
        except FileNotFoundError:
            print("索引文件不存在，尝试从磁盘重建...")
            return self._rebuild_index_from_disk()
        except json.JSONDecodeError as e:
            print(f"索引文件JSON格式错误: {e}，尝试从磁盘重建...")
            return self._rebuild_index_from_disk()
    
    def _rebuild_index_from_disk(self) -> ActivityIndex:
        """从activities目录重建索引"""
        print("开始从磁盘重建索引...")
        index = ActivityIndex()
        
        # 扫描activities目录
        if not self.activities_dir.exists():
            print("activities目录不存在，返回空索引")
            return index
        
        rebuilt_count = 0
        for activity_file in self.activities_dir.glob("*.json"):
            try:
                with open(activity_file, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                    activity = Activity(**activity_data)
                    meta = self._activity_to_meta(activity)
                    index.activities.append(meta)
                    rebuilt_count += 1
            except Exception as e:
                print(f"警告: 无法加载活动文件 {activity_file.name}: {e}")
                continue
        
        if rebuilt_count > 0:
            print(f"成功重建索引，恢复了 {rebuilt_count} 个活动")
            # 保存重建的索引
            self._save_index(index)
        else:
            print("未找到有效的活动文件，返回空索引")
        
        return index
    
    def _save_index(self, index: ActivityIndex):
        """保存活动索引"""
        index.updated_at = datetime.now()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(index.model_dump(mode='json'), f, ensure_ascii=False, indent=2, default=str)
    
    def _activity_to_meta(self, activity: Activity) -> ActivityMeta:
        """将Activity转换为ActivityMeta"""
        session = activity.session
        
        # 计算配速
        avg_pace = "--:--"
        if session.avg_speed and session.avg_speed > 0:
            avg_pace = speed_to_pace(session.avg_speed)
        
        # 计算距离(km)和时长(sec)
        distance_km = (session.total_distance or 0) / 1000
        duration_sec = session.total_elapsed_time or session.total_timer_time or 0
        
        return ActivityMeta(
            id=activity.id,
            name=activity.name,
            date=session.start_time or activity.created_at,
            sport=session.sport or "running",
            distance_km=round(distance_km, 2),
            duration_sec=round(duration_sec, 1),
            avg_pace=avg_pace,
            avg_heart_rate=session.avg_heart_rate,
            avg_cadence=session.avg_cadence,
            avg_power=session.avg_power,
            total_ascent=session.total_ascent,
            available_fields=activity.available_fields,
            available_iq_fields=activity.available_iq_fields
        )
    
    def save_activity(self, activity: Activity) -> ActivityMeta:
        """
        保存活动到文件系统
        
        Args:
            activity: Activity对象
        
        Returns:
            ActivityMeta对象
        """
        # 保存活动详情
        activity_file = self.activities_dir / f"{activity.id}.json"
        with open(activity_file, 'w', encoding='utf-8') as f:
            json.dump(activity.model_dump(mode='json'), f, ensure_ascii=False, indent=2, default=str)
        
        # 更新索引
        meta = self._activity_to_meta(activity)
        index = self._load_index()
        
        # 检查是否已存在（更新）
        existing_idx = next((i for i, a in enumerate(index.activities) if a.id == activity.id), None)
        if existing_idx is not None:
            index.activities[existing_idx] = meta
        else:
            index.activities.insert(0, meta)  # 新活动放在最前面
        
        self._save_index(index)
        
        return meta
    
    def get_activity(self, activity_id: str) -> Optional[Activity]:
        """
        获取活动详情
        
        Args:
            activity_id: 活动ID
        
        Returns:
            Activity对象或None
        """
        activity_file = self.activities_dir / f"{activity_id}.json"
        if not activity_file.exists():
            return None
        
        try:
            with open(activity_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return Activity(**data)
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading activity {activity_id}: {e}")
            return None
    
    def delete_activity(self, activity_id: str) -> bool:
        """
        删除活动
        
        Args:
            activity_id: 活动ID
        
        Returns:
            是否删除成功
        """
        # 删除活动文件
        activity_file = self.activities_dir / f"{activity_id}.json"
        if activity_file.exists():
            activity_file.unlink()
        
        # 更新索引
        index = self._load_index()
        index.activities = [a for a in index.activities if a.id != activity_id]
        self._save_index(index)
        
        return True
    
    def delete_all_activities(self) -> int:
        """
        删除所有活动 (v1.8.0+)
        
        警告: 此操作不可逆！删除所有activities/*.json文件和index.json。
        
        Returns:
            删除的活动数量
        """
        # 获取当前活动数量
        index = self._load_index()
        deleted_count = len(index.activities)
        
        # 删除所有活动文件
        if self.activities_dir.exists():
            for activity_file in self.activities_dir.glob("*.json"):
                try:
                    activity_file.unlink()
                except Exception as e:
                    print(f"警告: 删除文件失败 {activity_file.name}: {e}")
        
        # 重置索引
        empty_index = ActivityIndex()
        self._save_index(empty_index)
        
        return deleted_count
    
    def list_activities(
        self,
        sort_by: str = "date",
        order: str = "desc",
        filter_sport: Optional[str] = None,
        filter_date_from: Optional[datetime] = None,
        filter_date_to: Optional[datetime] = None,
        filter_distance_min: Optional[float] = None,
        filter_distance_max: Optional[float] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[ActivityMeta], int]:
        """
        获取活动列表
        
        Args:
            sort_by: 排序字段 (date, distance, duration, avg_pace, avg_heart_rate)
            order: 排序方向 (asc, desc)
            filter_sport: 过滤运动类型
            filter_date_from: 开始日期
            filter_date_to: 结束日期
            filter_distance_min: 最小距离(km)
            filter_distance_max: 最大距离(km)
            page: 页码
            limit: 每页数量
        
        Returns:
            (活动列表, 总数)
        """
        index = self._load_index()
        activities = index.activities.copy()
        
        # 过滤
        if filter_sport:
            activities = [a for a in activities if a.sport == filter_sport]
        
        if filter_date_from:
            activities = [a for a in activities if a.date and a.date >= filter_date_from]
        
        if filter_date_to:
            activities = [a for a in activities if a.date and a.date <= filter_date_to]
        
        if filter_distance_min is not None:
            activities = [a for a in activities if a.distance_km >= filter_distance_min]
        
        if filter_distance_max is not None:
            activities = [a for a in activities if a.distance_km <= filter_distance_max]
        
        # 排序
        sort_key_map = {
            "date": lambda x: x.date or datetime.min,
            "distance": lambda x: x.distance_km,
            "duration": lambda x: x.duration_sec,
            "avg_pace": lambda x: x.avg_pace,
            "avg_heart_rate": lambda x: x.avg_heart_rate or 0,
            "avg_cadence": lambda x: x.avg_cadence or 0,
            "avg_power": lambda x: x.avg_power or 0,
        }
        
        if sort_by in sort_key_map:
            reverse = (order == "desc")
            activities.sort(key=sort_key_map[sort_by], reverse=reverse)
        
        # 分页
        total = len(activities)
        start = (page - 1) * limit
        end = start + limit
        activities = activities[start:end]
        
        return activities, total
    
    def get_activities_for_compare(self, activity_ids: List[str]) -> List[Activity]:
        """
        获取多个活动用于对比
        
        Args:
            activity_ids: 活动ID列表
        
        Returns:
            Activity对象列表
        """
        activities = []
        for aid in activity_ids:
            activity = self.get_activity(aid)
            if activity:
                activities.append(activity)
        return activities
    
    def search_activities(self, query: str) -> List[ActivityMeta]:
        """
        搜索活动（按名称）
        
        Args:
            query: 搜索关键词
        
        Returns:
            匹配的活动列表
        """
        index = self._load_index()
        query_lower = query.lower()
        return [a for a in index.activities if query_lower in a.name.lower()]
    
    def get_all_sports(self) -> List[str]:
        """获取所有运动类型"""
        index = self._load_index()
        sports = set(a.sport for a in index.activities if a.sport)
        return sorted(list(sports))
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        index = self._load_index()
        activities = index.activities
        
        if not activities:
            return {
                "total_activities": 0,
                "total_distance_km": 0,
                "total_duration_sec": 0,
                "sports": []
            }
        
        total_distance = sum(a.distance_km for a in activities)
        total_duration = sum(a.duration_sec for a in activities)
        sports = list(set(a.sport for a in activities))
        
        return {
            "total_activities": len(activities),
            "total_distance_km": round(total_distance, 2),
            "total_duration_sec": round(total_duration, 1),
            "sports": sports
        }
