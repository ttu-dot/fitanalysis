# Release Notes v1.8.0 - 设备映射系统重构 + 字段选择器UI优化

**发布日期**: 2026-01-20  
**类型**: Major Update (重大更新)

---

## 🎯 核心更新

### 1. **设备映射系统重构**
- ✅ 后端统一字段标准化，解决v1.7.0的"DR_DR_"重复前缀问题
- ✅ 基于DragonValue官方映射表实现23个标准字段
- ✅ 支持字段别名映射（stance→gct、ssl→SSL等大小写变体）
- ✅ 引入storage_unit/display_unit分离设计，为speed→pace转换做准备
- ✅ 可扩展架构：5步添加新设备（Garmin、Stryd等）

### 2. **字段选择器UI全面优化**
- ✅ 采用**卡片布局**，取代旧的列表布局
- ✅ **搜索过滤**：实时搜索字段，高亮匹配项
- ✅ **整体可折叠**：收起面板最大化图表空间
- ✅ **4列响应式网格**（1400px→3列，1000px→2列）
- ✅ **平滑展开/折叠动画**
- ✅ **Sticky toolbar**：滚动时控制栏固定在顶部

### 3. **Reset All 功能**
- ✅ 一键清空所有活动数据（v1.8.0升级需要）
- ✅ 双重确认机制防止误操作
- ✅ DELETE /api/activities/all API端点

---

## 📦 主要功能

### Backend 更新

#### **device_mappings.py**
- 新增字段：`storage_unit`, `display_unit`, `requires_conversion`, `precision`
- 官方大小写：`dr_SSL`, `dr_LSS`, `dr_v_ILR`, `dr_v_PIF`, `dr_body_X_PIF` 等
- 16个别名映射：
  - 官方缩写：stance→gct, prop_power→propulsive_power
  - 大小写变体：ssl→SSL, lss→LSS, v_ilr→v_ILR 等
- API导出增强：`get_all_devices_config()` 包含转换元数据

### Frontend 更新

#### **index.html**
- 新的三层结构：
  ```
  .field-selector-container
    ├── .field-selector-toolbar  (搜索框 + 全选/全不选/收起按钮 + X轴切换)
    └── .field-selector-body
         └── .field-groups-grid  (4列卡片网格)
              └── .field-group-card  (单个分组卡片)
  ```
- Reset All按钮：活动列表工具栏右侧

#### **styles.css**
- 200+ 行新样式：
  - `.field-selector-toolbar`: sticky定位，flex布局
  - `.field-selector-search`: 圆角搜索框，内置🔍图标
  - `.field-group-card`: 卡片hover效果，阴影变化
  - `.field-group-card__content`: max-height过渡动画
  - `.btn-danger`: 红色危险按钮（已存在）
  - `.btn-sm`: 小尺寸按钮变体

#### **charts.js**
- 重写 `renderUnifiedFieldSelector()`: 生成卡片HTML
- 新增 `toggleFieldSelectorPanel(mode)`: 整体折叠控制
- 新增 `handleFieldSearch(input, containerId)`: 搜索过滤逻辑
- 新增 `getFieldGroupIcon(groupKey)`: Emoji图标映射
- 保存展开状态到 localStorage: `field_group_expanded_{groupKey}`

#### **app.js**
- 绑定toolbar按钮事件（全选/全不选/收起/搜索）
- 新增 `handleResetAll()`: 双重确认 + API调用 + 状态刷新
- 支持趋势图和每圈数据两套独立的字段选择器控制

### Test Infrastructure

#### **test/config/**
- `expected_fields.json`: 23个DragonRun字段完整配置
- `test_constants.py`: 性能阈值更新（API<50ms, FIT解析<2s）

---

## ⚠️ 破坏性变更 (Breaking Changes)

### **字段名称标准化**
旧数据中的字段名将被规范化：
- `dr_ssl` → `dr_SSL`
- `dr_lss` → `dr_LSS`
- `dr_v_ilr` → `dr_v_ILR`
- `dr_v_pif` → `dr_v_PIF`
- `dr_body_x_pif` → `dr_body_X_PIF`
- ... (共10个字段大小写变更)

### **迁移步骤**
1. **备份数据**：
   ```bash
   # 备份data目录
   cp -r data/ data_backup_v1.7.0/
   ```

2. **升级到v1.8.0**：
   ```bash
   git pull origin main
   git checkout v1.8.0
   ```

3. **重新上传FIT文件**：
   - 方案A（推荐）：使用Reset All按钮清空所有数据，重新上传
   - 方案B：保留旧数据（前端兼容旧字段名）

4. **验证**：
   - 上传一个FIT文件
   - 检查字段显示是否正确
   - 确认无"DR_DR_"前缀
   - 测试字段搜索功能

---

## 🚀 性能优化

- **API响应时间**: /api/device-mappings 目标 <50ms
- **FIT解析时间**: 大文件解析 <2s（从1s放宽）
- **CSS动画**: 使用cubic-bezier缓动函数，过渡时间200-300ms
- **搜索过滤**: 实时响应，无延迟

---

## 📊 技术细节

### DragonRun字段映射表（23个字段）

| 字段名 | 显示标签 | 单位 | 分类 | 说明 |
|--------|----------|------|------|------|
| dr_timestamp | 时间戳 | ms | basic | 步态数据记录时间点 |
| dr_distance | 距离 | m | basic | 跑步累计距离 |
| dr_speed | 配速 | min/km | pace | 当前配速（存储为m/s） |
| dr_cadence | 步频 | spm | dynamics | 每分钟步数 |
| dr_stride | 步幅 | cm | dynamics | 单步距离 |
| dr_gct | 触地时间 | ms | dynamics | 地面接触时间 |
| dr_air_time | 腾空时间 | ms | dynamics | 双脚离地时间 |
| dr_v_osc | 垂直振幅 | cm | dynamics | 身体重心上下振幅 |
| dr_vertical_ratio | 垂直步幅比 | % | dynamics | 垂直振幅/步幅 |
| dr_SSL | 步速损失 | cm/s | dynamics | 着地速度损失量 |
| dr_SSL_percent | 步速损失占比 | % | dynamics | 占当前速度百分比 |
| dr_vertical_power | 垂直功率 | W | power | 克服重力做功功率 |
| dr_propulsive_power | 前进功率 | W | power | 前进方向有效功率 |
| dr_slope_power | 坡度功率 | W | power | 上坡/下坡功率 |
| dr_total_power | 总功率 | W | power | 总功率 |
| dr_LSS | 下肢刚度 | kN/m | biomechanics | 腿部弹性系数 |
| dr_v_ILR | 垂直冲击力 | bw/s | impact | 垂直冲击负荷率 |
| dr_h_ILR | 水平冲击力 | bw/s | impact | 水平冲击负荷率 |
| dr_v_PIF | 垂直冲击峰值 | g | impact | 垂直最大加速度 |
| dr_h_PIF | 水平冲击峰值 | g | impact | 水平最大加速度 |
| dr_body_X_PIF | 传感器X轴冲击 | g | impact | X轴冲击峰值 |
| dr_body_Y_PIF | 传感器Y轴冲击 | g | impact | Y轴冲击峰值 |
| dr_body_Z_PIF | 传感器Z轴冲击 | g | impact | Z轴冲击峰值 |

### 字段别名映射（16个）
```python
{
    'dr_stance': 'dr_gct',                 # 官方缩写
    'dr_air': 'dr_air_time',
    'dr_at': 'dr_air_time',
    'dr_vertical_osc': 'dr_v_osc',
    'dr_vert_osc': 'dr_v_osc',
    'dr_prop_power': 'dr_propulsive_power',
    
    'dr_ssl': 'dr_SSL',                    # 大小写变体
    'dr_ssl%': 'dr_SSL_percent',
    'dr_SSL%': 'dr_SSL_percent',
    'dr_lss': 'dr_LSS',
    'dr_v_ilr': 'dr_v_ILR',
    'dr_h_ilr': 'dr_h_ILR',
    'dr_v_pif': 'dr_v_PIF',
    'dr_h_pif': 'dr_h_PIF',
    'dr_body_x_pif': 'dr_body_X_PIF',
    'dr_body_y_pif': 'dr_body_Y_PIF',
    'dr_body_z_pif': 'dr_body_Z_PIF',
    
    'dr_slop_power': 'dr_slope_power'      # 拼写修正
}
```

---

## 📝 文档更新

- ✅ `config.py`: VERSION = "1.8.0"
- ✅ `RELEASE_v1.8.0.md`: 本文档
- 🔄 `agent.md`: 待添加 Section 13.3 设备映射系统设计
- 🔄 `agent.md`: 待更新 Section 14 发布记录

---

## 🔮 未来考虑 (v1.9.0+)

### Lap字段动态生成
- 检测`dr_lap_avg_xxx`格式
- 提取基础字段名→查找配置→生成"圈平均{display_label}"
- 单位和转换规则继承基础字段

### 未知字段降级处理
- 遇到未知`dr_`前缀字段时返回原始field_name
- 前端显示降级标签`"DR_{field_name}"`

### 前端动态配置加载（v1.8.0计划中，v1.9.0实现）
- `loadDeviceFieldConfigs()`: 从API加载配置
- 删除硬编码`IQ_FIELD_LABELS`
- `formatFieldValue()`: 处理`requires_conversion`字段
- `speed_to_pace(m/s)`: 1000/speed → MM:SS转换

### 性能优化
- `Cache-Control: max-age=3600` 响应头
- 前端缓存fields数组转Map
- ETag支持304条件请求

---

## 🙏 致谢

感谢DragonValue团队提供的官方字段映射表。

---

**完整变更**: [v1.7.0...v1.8.0](https://github.com/your-repo/compare/v1.7.0...v1.8.0)
