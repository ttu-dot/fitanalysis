"""
FIT跑步数据分析器 - 配置文件
"""
from pathlib import Path

# 项目根目录
BASE_DIR = Path(__file__).parent

# 数据存储目录
DATA_DIR = BASE_DIR / "data"
ACTIVITIES_DIR = DATA_DIR / "activities"

# 服务器配置
HOST = "127.0.0.1"
PORT = 8082

# CORS配置
ALLOWED_ORIGINS = [
    "http://localhost:8082",
    "http://127.0.0.1:8082",
]

# 版本信息
VERSION = "1.8.0"

# 文件上传配置
MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50 MB
ALLOWED_EXTENSIONS = {".fit"}

# 分页配置
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# ==================== 离线心率CSV合并配置 ====================
# 说明：以FIT record时间戳为基准输出，不改变采样间隔。
# 自动判定：优先尝试“元数据对齐”（固定偏移 + 高匹配率），失败则走“线性插值”。

# 自动对齐：允许尝试的最大固定偏移范围（秒）
HR_MERGE_AUTO_ALIGN_MAX_SHIFT_SEC = 8

# 自动对齐：认为“对齐成功”的时间匹配容忍（秒）
HR_MERGE_AUTO_ALIGN_MATCH_TOLERANCE_SEC = 1

# 自动对齐：最低匹配率（0~1）
HR_MERGE_AUTO_ALIGN_MIN_MATCH_RATIO = 0.85

# 线性插值：允许插值的最大间隔（秒）。超过该间隔则置空。
HR_MERGE_INTERPOLATE_MAX_GAP_SEC = 5

# 是否允许对CSV覆盖范围之外进行外推（默认不允许）
HR_MERGE_ALLOW_EXTRAPOLATION = False
