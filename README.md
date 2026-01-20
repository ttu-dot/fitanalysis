# FIT Running Data Analyzer

[![Build Release](https://github.com/ttu-dot/fitanalysis/actions/workflows/build-release.yml/badge.svg)](https://github.com/ttu-dot/fitanalysis/actions/workflows/build-release.yml)

A local web application for parsing FIT files from Garmin and other sports devices, providing an activity management experience similar to Garmin Connect.

**Supported Platforms**: Windows, macOS

## Download

Download pre-built packages from [GitHub Releases](https://github.com/ttu-dot/fitanalysis/releases):

- **Windows**: `fitanalysis-{VERSION}-windows.zip` - Extract and run `fitanalysis.exe` or `start_server.bat`
- **macOS**: `fitanalysis-{VERSION}-macos.zip` - Extract and run `fitanalysis.app` (first time: right-click → Open)

## Version Information

**Current Version**: v1.8.0  
**Release Date**: 2026-01-20

## Latest Update (v1.8.0)

### 🔧 Device Mapping System Refactor + Field Selector UI Optimization
- ✅ **Device Mapping System** - Unified field standardization, 23 standard fields based on DragonValue official mapping
- ✅ **Field Aliases** - Support for stance→gct, ssl→SSL case variants
- ✅ **Card Layout** - New card-based field selector with search filtering
- ✅ **Collapsible Panel** - Maximize chart space with collapsible field selector
- ✅ **Reset All** - One-click clear all activity data with double confirmation
- ✅ **GitHub Actions** - Automated Windows/macOS builds with ZIP packaging

For details see [RELEASE_v1.8.0.md](RELEASE_v1.8.0.md)

## Version History

- **v1.8.0** (2026-01-20) - Device mapping refactor, field selector UI optimization, GitHub Actions
- **v1.7.0** (2026-01-20) - 龙豆字段自动DR_前缀显示
- **v1.6.0** (2026-01-19) - macOS cross-platform support
- **v1.5.0** (2025-12-22) - IQ speed field pace display extended support
- **v1.4.1** (2025-12-17) - 心率合并浮点精度优化
- **v1.4.0** (2025-12-15) - 离线心率CSV合并功能
- **v1.3.0** - 多活动对比、字段单位系统重构
- **v1.2.0** - 龙豆22字段完整支持
- **v1.1.0** - 自动加载活动、多活动单字段对比
- **v1.0.0** - 初始版本

## 功能特性

### ✨ v1.1.0 新功能
- ✅ **页面自动加载活动列表** - 打开网页即自动展示所有本地活动，无需手动操作
- ✅ **多活动单字段对比** - 字段选择改为单选模式，更直观地对比多个活动的同一指标

### 核心功能
- ✅ FIT文件上传和解析（自动识别所有字段，包括IQ扩展字段和龙豆跑步dr_字段）
- ✅ 活动列表管理（排序、过滤、分页）
- ✅ 秒级趋势图展示（可选字段，悬停显示细节）
- ✅ **X轴时间/距离切换**（点击按钮即可切换）
- ✅ **配速自动转换**（速度字段自动转换为 min/km 显示）
- ✅ **IQ字段DR_前缀显示**（龙豆字段显示为"DR_触地时间"等格式）
- ✅ 每圈汇总数据表格
- ✅ 双字段叠加对比
- ✅ 多活动对比分析（时间/距离对齐可选）
- ✅ **多活动日期时间戳前缀**（图例显示为"20251208_546218476 - 字段名"格式）
- ✅ CSV数据导出（merged/categorized模式）
- ✅ **离线心率CSV合并**（把外部心率作为IQ扩展字段写入活动，支持原有两种对比）

## Quick Start

### System Requirements

- Python 3.8+ (3.11+ recommended)
- Modern browser (Chrome, Firefox, Edge, Safari)
- **Windows** 10/11 or **macOS** 10.15+

### Installation

#### Windows

1. Double-click `run.bat` to automatically setup environment and start server
2. Browser will open automatically at http://127.0.0.1:8082

Or manually:

```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r backend\requirements.txt

# Start server
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8082 --reload
```

#### macOS

1. Open Terminal and navigate to project folder
2. Run `chmod +x run.sh` (first time only)
3. Run `./run.sh` to start server
4. Browser will open automatically at http://127.0.0.1:8082

Or manually:

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start server
cd backend
python -m uvicorn main:app --host 127.0.0.1 --port 8082 --reload
```

### Packaged Distribution

#### Windows

1. Run `python build.py` to create standalone executable
2. Find `dist/fitanalysis/fitanalysis.exe`
3. Double-click to launch (browser opens automatically)

#### macOS

1. Run `python build.py` to create .app bundle
2. Find `dist/fitanalysis.app`
3. **First time**: Right-click → Open (to bypass Gatekeeper)
4. Subsequent launches: Double-click to run

**Note**: Unsigned apps require manual approval in macOS. If blocked:
- Go to System Preferences → Security & Privacy
- Click "Open Anyway" button

### Access Application

Browser opens automatically at: **http://127.0.0.1:8082**

## 目录结构

```
fitanalysis/
├── agent.md                 # 系统设计文档（SDD）
├── config.py                # 配置文件
├── run.bat                  # Windows启动脚本
├── README.md                # 本文件
├── .gitignore
├── backend/                 # 后端代码
│   ├── main.py              # FastAPI主应用
│   ├── fit_parser.py        # FIT文件解析器
│   ├── data_store.py        # 数据存储管理
│   ├── csv_exporter.py      # CSV导出功能
│   ├── models.py            # 数据模型
│   ├── requirements.txt     # Python依赖
│   └── test_api.py          # 后端单元测试
├── frontend/                # 前端代码
│   ├── index.html           # 主页面
│   ├── css/
│   │   └── styles.css       # 样式文件
│   └── js/
│       ├── app.js           # 主应用逻辑
│       ├── charts.js        # 图表模块
│       ├── charts.test.js   # 图表模块单元测试
│       └── export.js        # 导出模块
└── data/                    # 数据存储（自动创建）
    ├── activities/          # 活动数据JSON文件
    └── index.json           # 活动索引
```

## 使用说明

### 1. 上传FIT文件

点击 "📁 上传FIT文件" 按钮，选择Garmin手表或其他设备导出的.fit文件。

### 2. 查看活动列表

- 支持按日期、距离、时长、配速等排序
- 可按日期范围、距离范围过滤
- 点击活动行或"查看"按钮进入详情页

### 3. 查看活动详情

#### 趋势图
- 选择要展示的字段（心率、步频、功率、IQ字段等）
- **X轴切换**：点击“时间”或“距离”按钮切换横轴显示方式
- **配速自动转换**：速度字段自动转换为配速(min/km)显示
- 鼠标悬停显示该时间点/距离点所有选中字段的数值
- 支持缩放、平移操作
- 可导出为PNG图片

#### 合并离线心率CSV（独立工具模块）

**功能说明**：
- 将离线心率设备（如光学心率表、心率带）的CSV数据合并到FIT活动中
- **创建新活动副本**，原活动保持不变，便于对比和回滚
- 新活动名称：`[HR合并]{原活动名}`
- 导入字段命名：`imported_{device}_hr`（device名称会自动清理特殊字符）

**操作步骤**：
1. 在活动详情页点击"➕ 合并心率CSV"
2. 选择符合格式要求的CSV文件
3. 等待合并完成，系统会自动创建新活动
4. 返回活动列表查看新创建的`[HR合并]`活动

**支持的CSV格式**：
```csv
Name,Sport,Date,Start time,Duration,Device Name
MyRun,Running,2025-12-15,20:18:18,00:30:05,Polar H10
Time,Second,HR (bpm)
20:18:18,0,120
20:18:28,10,125
20:18:38,20,130
```

**必需列**：
- 元数据行（可选）：`Name, Sport, Date, Start time, Duration, Device Name`
- 数据表头：`Time, Second, HR (bpm)`
- 数据行：时间戳、秒数、心率值

**合并方式**：
- **元数据对齐**：CSV时间戳与FIT记录时间戳匹配度高时使用（≥85%）
- **线性插值**：时间戳不完全匹配时自动插值填充

**使用场景**：
- 单活动多心率源对比（例如：FIT内置心率 vs 外置心率带）
- 验证心率设备准确性
- 补充缺失的心率数据

**注意**：此功能为独立工具模块，删除后不影响FIT文件解析、图表显示等核心功能。

---

#### 每圈数据
- 查看每圈的汇总统计
- 包含时间、距离、配速、心率等

### 4. 多活动对比

- 在活动列表页勾选多个活动（至少2个）
- 点击"对比选中活动"按钮
- 选择对比字段和对齐方式（时间/距离）
- 查看多条曲线叠加对比图

### 5. 导出数据

点击"📥 导出CSV"按钮，选择导出模式：
- **合并CSV (秒级数据)**：单个CSV文件包含所有record数据
- **合并CSV (每圈数据)**：单个CSV文件包含每圈汇总
- **分类CSV (ZIP)**：ZIP包含records.csv、laps.csv、session.csv三个文件

## 技术栈

### 后端
- **FastAPI** - 现代Python Web框架
- **fitdecode** - FIT文件解析库
- **pandas** - 数据处理
- **pydantic** - 数据验证

### Frontend
- **HTML5 + CSS3 + JavaScript** - Pure frontend, no framework dependencies
- **Plotly.js** - Interactive chart library

### Data Storage
- **Local JSON Files** - Lightweight storage, no database required

## API Documentation

After starting server, visit: **http://127.0.0.1:8082/docs**

Provides complete interactive API documentation (Swagger UI).

## FAQ

### Q: Which FIT files are supported?
A: All FIT protocol compliant files, including activity files from Garmin, Wahoo, Suunto and other brands.

### Q: What are IQ fields?
A: IQ fields are extended data recorded by Garmin Connect IQ apps (such as DragonRun, Stryd Power Meter, etc.). This application automatically recognizes and displays them, including:
- 龙豆跑步 `dr_` 字段：gct(触地时间)、air_time(腾空时间)、v_osc(垂直振幅)、v_pif(冲击峰值)、stride_length(步幅)
- 标准开发者字段：Connect IQ应用记录的其他扩展数据

### Q: 数据存储在哪里？
A: 所有数据存储在 `data/` 目录下，以JSON格式保存，完全本地化，不会上传到任何服务器。

### Q: 如何备份数据？
A: 直接复制 `data/` 目录即可完整备份所有活动数据。

### Q: 可以导入CSV吗？
A: 支持“离线心率CSV合并到活动”（仅心率CSV，写入为IQ扩展字段）；其他CSV暂不支持作为活动导入。

### 离线心率CSV合并接口

- `POST /api/activity/{activity_id}/merge/hr_csv`
    - `multipart/form-data`
    - 字段：`file` (CSV)
    - 可选覆盖参数（Form字段）：
        - `auto_align_max_shift_sec`
        - `auto_align_match_tolerance_sec`
        - `auto_align_min_match_ratio`
        - `interpolate_max_gap_sec`
        - `allow_extrapolation`
    - 返回：更新后的 Activity JSON（包含 `merge_provenance`）

## 开发说明

详细的系统设计文档请查看 [agent.md](./agent.md)。

### 运行测试

#### 前端单元测试
```bash
node frontend/js/charts.test.js
```

#### 后端单元测试
```bash
cd backend
python test_api.py
python -m unittest test_hr_csv_merge.py
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**项目版本**: v1.1.0  
**最后更新**: 2025-12-08
