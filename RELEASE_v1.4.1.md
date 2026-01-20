# FIT跑步数据分析器 v1.4.1 发布说明

**发布日期**: 2025-12-17

## 🐛 Bug修复

### Bug #23: 心率合并时间偏移浮点精度优化

**问题描述**:
- 心率CSV合并时，offset检测使用整数舍入，导致亚秒级精度丢失
- 当真实offset包含小数秒（如0.7秒）时，被舍入为整数（1秒），产生系统性误差
- 在0.2秒exact_tol容限下，部分记录可能超出范围而被丢弃

**修复内容**:
1. **浮点offset检测**: 将`deltas: List[int]`改为`List[float]`，保留浮点精度
2. **0.1秒分辨率**: 使用`round(d * 10) / 10.0`进行0.1秒精度的bin分组
3. **内部精确对齐**: 所有offset计算和应用均使用浮点数
4. **向后兼容**: 对现有整数offset场景完全兼容

**影响范围**:
- 所有metadata_align模式的心率合并
- 提升时间对齐精度，减少dropped_ratio
- 用户无感知（前端不显示offset值）

**相关文件**:
- `backend/hr_csv_merge.py`: offset检测算法优化
- `backend/models.py`: MergeStats.offset_sec已为float类型

## ✅ 测试验证

- 所有13个现有单元测试通过，无回归
- 浮点offset检测机制已验证

## 📦 安装与使用

### Windows用户
1. 下载 `fitanalysis-v1.4.1-windows.zip`
2. 解压到任意目录
3. 双击 `启动服务器.bat` 或运行 `fitanalysis.exe`
4. 浏览器访问 http://127.0.0.1:8080

### 开发者
```bash
git pull origin main
pip install -r backend/requirements.txt
python backend/main.py
```

## 🔄 从v1.4.0升级

无需特殊操作，直接替换可执行文件即可。所有现有功能保持不变。

## 📝 完整更新日志

详见 [BUGS.md](BUGS.md) 中的Bug #23记录。

---

**上一版本**: [v1.4.0](RELEASE_v1.4.0.md)
