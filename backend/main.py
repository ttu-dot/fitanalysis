"""
FIT跑步数据分析器 - FastAPI主应用
"""
import os
import sys
import uuid
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, StreamingResponse, FileResponse
import io

# 添加backend目录到路径
# 处理PyInstaller打包后的路径
if getattr(sys, 'frozen', False):
    # 打包后运行
    BASE_DIR = Path(sys.executable).parent
    backend_dir = BASE_DIR / '_internal' / 'backend'
    if backend_dir.exists():
        sys.path.insert(0, str(backend_dir))
    else:
        sys.path.insert(0, str(BASE_DIR))
    # 打包后的数据和前端目录
    DATA_DIR = BASE_DIR / "data"
    FRONTEND_DIR = BASE_DIR / "_internal" / "frontend"
else:
    # 开发环境
    BASE_DIR = Path(__file__).parent.parent
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(BASE_DIR))
    DATA_DIR = BASE_DIR / "data"
    FRONTEND_DIR = BASE_DIR / "frontend"

from models import (
    Activity, ActivityMeta, UploadResponse, ActivityListResponse,
    CompareRequest, CompareResponse, CompareActivityData, HrMergeOptions
)
from fit_parser import parse_fit_bytes, speed_to_pace
from data_store import DataStore
from csv_exporter import export_merged_csv, export_categorized_zip, export_laps_csv
from hr_csv_merge import merge_offline_hr_csv_into_activity
from device_mappings import DeviceRegistry

# 初始化
app = FastAPI(
    title="FIT跑步数据分析器",
    description="解析FIT文件，展示趋势图，支持对比分析和CSV导出",
    version="1.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 数据存储
data_store = DataStore(str(DATA_DIR))


# ==================== API 路由 ====================

@app.post("/api/upload", response_model=UploadResponse)
async def upload_fit_file(
    file: UploadFile = File(...),
    name: Optional[str] = None
):
    """上传并解析FIT文件"""
    # 检查文件类型
    if not file.filename.lower().endswith('.fit'):
        raise HTTPException(status_code=400, detail="只支持.fit文件")
    
    try:
        # 读取文件内容
        file_bytes = await file.read()
        
        # 生成活动ID
        activity_id = str(uuid.uuid4())
        
        # 活动名称
        activity_name = name or Path(file.filename).stem
        
        # 解析FIT文件
        activity = parse_fit_bytes(file_bytes, file.filename, activity_id, activity_name)
        
        # 保存活动
        meta = data_store.save_activity(activity)
        
        return UploadResponse(
            success=True,
            activity_id=activity_id,
            message="活动导入成功",
            summary={
                "sport": activity.session.sport,
                "distance_km": meta.distance_km,
                "duration": f"{int(meta.duration_sec // 60)}:{int(meta.duration_sec % 60):02d}",
                "records_count": len(activity.records),
                "laps_count": len(activity.laps),
                "available_fields": activity.available_fields,
                "available_iq_fields": activity.available_iq_fields
            }
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"解析FIT文件失败: {str(e)}")


@app.get("/api/activities", response_model=ActivityListResponse)
async def get_activities(
    sort: str = Query("date", description="排序字段"),
    order: str = Query("desc", description="排序方向"),
    sport: Optional[str] = Query(None, description="运动类型"),
    date_from: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    distance_min: Optional[float] = Query(None, description="最小距离(km)"),
    distance_max: Optional[float] = Query(None, description="最大距离(km)"),
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取活动列表"""
    # 解析日期
    filter_date_from = None
    filter_date_to = None
    if date_from:
        try:
            filter_date_from = datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            pass
    if date_to:
        try:
            filter_date_to = datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            pass
    
    activities, total = data_store.list_activities(
        sort_by=sort,
        order=order,
        filter_sport=sport,
        filter_date_from=filter_date_from,
        filter_date_to=filter_date_to,
        filter_distance_min=distance_min,
        filter_distance_max=distance_max,
        page=page,
        limit=limit
    )
    
    return ActivityListResponse(
        activities=activities,
        total=total,
        page=page,
        limit=limit
    )


@app.get("/api/activity/{activity_id}")
async def get_activity(activity_id: str):
    """获取活动详情"""
    activity = data_store.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    
    return activity.model_dump(mode='json')


@app.delete("/api/activity/{activity_id}")
async def delete_activity(activity_id: str):
    """删除活动"""
    success = data_store.delete_activity(activity_id)
    if success:
        return {"success": True, "message": "活动已删除"}
    raise HTTPException(status_code=404, detail="活动不存在")


@app.post("/api/activity/{activity_id}/merge/hr_csv")
async def merge_hr_csv_into_activity(
    activity_id: str,
    file: UploadFile = File(...),
    auto_align_max_shift_sec: Optional[float] = Form(None),
    auto_align_match_tolerance_sec: Optional[float] = Form(None),
    auto_align_min_match_ratio: Optional[float] = Form(None),
    interpolate_max_gap_sec: Optional[float] = Form(None),
    allow_extrapolation: Optional[bool] = Form(None),
):
    """将离线心率CSV合并到指定活动，创建新活动副本（不修改原活动）"""
    if file.filename and not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail="只支持.csv文件")

    original_activity = data_store.get_activity(activity_id)
    if not original_activity:
        raise HTTPException(status_code=404, detail="活动不存在")

    try:
        # Create deep copy of original activity
        new_activity = deepcopy(original_activity)
        
        # Generate new ID and update name with prefix
        new_activity.id = str(uuid.uuid4())
        new_activity.name = f"[HR合并]{original_activity.name}"
        new_activity.created_at = datetime.now()
        
        # Read file and merge HR data
        file_bytes = await file.read()
        options = HrMergeOptions(
            auto_align_max_shift_sec=auto_align_max_shift_sec,
            auto_align_match_tolerance_sec=auto_align_match_tolerance_sec,
            auto_align_min_match_ratio=auto_align_min_match_ratio,
            interpolate_max_gap_sec=interpolate_max_gap_sec,
            allow_extrapolation=allow_extrapolation,
        )

        merge_offline_hr_csv_into_activity(
            new_activity,
            file_bytes=file_bytes,
            source_file_name=file.filename,
            options=options,
        )

        # Save new activity (original activity remains unchanged)
        data_store.save_activity(new_activity)
        
        return {
            "new_activity_id": new_activity.id,
            "new_activity_name": new_activity.name,
            "activity": new_activity.model_dump(mode='json')
        }
    except ValueError as e:
        # CSV format errors - return detailed message
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"合并离线心率CSV失败: {str(e)}")


@app.post("/api/compare", response_model=CompareResponse)
async def compare_activities(request: CompareRequest):
    """多活动对比"""
    activities = data_store.get_activities_for_compare(request.activity_ids)
    
    if not activities:
        raise HTTPException(status_code=404, detail="未找到活动")
    
    result_activities = []
    
    for activity in activities:
        # 提取对比数据
        data = []
        for record in activity.records:
            point = {}
            
            # X轴值
            if request.align_by == "distance":
                point["x"] = record.distance / 1000 if record.distance else 0  # km
            else:
                point["x"] = record.elapsed_time or 0  # 秒
            
            # 请求的字段
            for field in request.fields:
                if field.startswith("iq_"):
                    # IQ字段
                    iq_key = field[3:]  # 去掉 "iq_" 前缀
                    point[field] = record.iq_fields.get(iq_key)
                else:
                    # 标准字段
                    point[field] = getattr(record, field, None)
            
            data.append(point)
        
        result_activities.append(CompareActivityData(
            id=activity.id,
            name=activity.name,
            date=activity.session.start_time,
            data=data
        ))
    
    x_label = "距离 (km)" if request.align_by == "distance" else "时间 (秒)"
    
    return CompareResponse(
        activities=result_activities,
        align_by=request.align_by,
        x_label=x_label,
        fields=request.fields
    )


@app.get("/api/export/{activity_id}")
async def export_activity(
    activity_id: str,
    mode: str = Query("merged", description="导出模式: merged 或 categorized"),
    fields: Optional[str] = Query(None, description="字段列表，逗号分隔"),
    data_type: str = Query("records", description="数据类型: records 或 laps")
):
    """导出活动数据为CSV"""
    activity = data_store.get_activity(activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    
    # 解析字段列表
    include_fields = None
    if fields:
        include_fields = [f.strip() for f in fields.split(",")]
    
    if mode == "categorized":
        # 导出ZIP包含多个CSV
        zip_content = export_categorized_zip(activity)
        return Response(
            content=zip_content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=activity_{activity.name}.zip"
            }
        )
    else:
        # 导出单个CSV
        if data_type == "laps":
            csv_content = export_laps_csv(activity)
            filename = f"activity_{activity.name}_laps.csv"
        else:
            csv_content = export_merged_csv(activity, include_fields)
            filename = f"activity_{activity.name}_records.csv"
        
        return Response(
            content=csv_content.encode('utf-8-sig'),  # 使用BOM以支持Excel
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )


@app.get("/api/version")
async def get_version():
    """Get application version"""
    from config import VERSION
    return {"version": VERSION}


@app.get("/api/sports")
async def get_sports():
    """获取所有运动类型"""
    sports = data_store.get_all_sports()
    return {"sports": sports}


@app.get("/api/statistics")
async def get_statistics():
    """获取统计信息"""
    stats = data_store.get_statistics()
    return stats


@app.get("/api/device-mappings")
async def get_device_mappings():
    """
    获取所有设备的字段映射配置 (v1.8.0+)
    
    返回所有已注册设备的字段配置，包括字段名、显示标签、单位、分类等信息。
    前端使用此API动态加载字段配置，替代硬编码的IQ_FIELD_LABELS。
    
    Returns:
        {
            "dragonrun": {
                "device_id": "dragonrun",
                "display_name": "DragonRun",
                "prefix": "dr_",
                "fields": [
                    {
                        "field_name": "dr_gct",
                        "display_label": "DR_触地时间 (ms)",
                        "unit": "ms",
                        "category": "dynamics",
                        ...
                    },
                    ...
                ]
            }
        }
    """
    return DeviceRegistry.get_all_devices_config()


@app.delete("/api/activities/all")
async def delete_all_activities():
    """
    删除所有活动数据 (v1.8.0+)
    
    警告: 此操作不可逆！将删除data/activities/目录下的所有JSON文件和data/index.json。
    用于v1.8.0升级时清理旧数据，要求用户重新上传FIT文件以使用新的字段映射。
    
    Returns:
        {
            "success": true,
            "deleted_count": 42,
            "message": "成功删除42个活动"
        }
    """
    try:
        deleted_count = data_store.delete_all_activities()
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"成功删除{deleted_count}个活动"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 静态文件服务 ====================

# 挂载前端静态文件
if FRONTEND_DIR.exists():
    app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
    app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")


@app.get("/favicon.ico")
async def favicon():
    """Return favicon"""
    # Look for favicon in multiple locations
    icon_locations = [
        BASE_DIR / "app_icon.ico",
        BASE_DIR / "_internal" / "app_icon.ico",
        FRONTEND_DIR / "favicon.ico"
    ]
    
    for icon_path in icon_locations:
        if icon_path.exists():
            return FileResponse(str(icon_path), media_type="image/x-icon")
    
    # If no icon found, return 204 No Content instead of 404
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/")
async def index():
    """返回主页"""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "FIT跑步数据分析器 API", "docs": "/docs"}


# ==================== 启动 ====================

if __name__ == "__main__":
    import uvicorn
    import webbrowser
    import threading
    import os
    
    # Import config from parent directory
    sys.path.insert(0, str(BASE_DIR))
    from config import VERSION, HOST, PORT
    
    # 检查是否为打包环境
    is_frozen = getattr(sys, 'frozen', False)
    
    # 避免reload时重复打印 - 只在主进程打印
    # uvicorn的reload会创建子进程，通过环境变量检测
    is_main_process = os.environ.get('RUN_MAIN') != 'true'
    
    # 打印启动信息（英文，跨平台一致）- 只在主进程或打包版本打印
    if is_frozen or is_main_process:
        print("="*60)
        print("FIT Running Data Analyzer")
        print(f"Version: {VERSION}")
        print("="*60)
        print()
        print("Starting server...")
        print(f"Access at: http://{HOST}:{PORT}")
        print("Press Ctrl+C to stop server")
        print()
    
    # 延迟打开浏览器（等服务器启动完成）
    def open_browser():
        import time
        time.sleep(1.5)  # 等待1.5秒让服务器完全启动
        webbrowser.open(f'http://{HOST}:{PORT}')
    
    # 在后台线程中打开浏览器（仅打包版本）
    if is_frozen:
        threading.Thread(target=open_browser, daemon=True).start()
    
    # 降低日志级别，减少控制台输出
    uvicorn.run(
        app, 
        host=HOST, 
        port=PORT, 
        reload=not is_frozen,
        log_level="warning",  # 只显示警告和错误
        access_log=False  # 禁用访问日志
    )
