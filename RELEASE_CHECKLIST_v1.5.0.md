# FIT跑步数据分析器 v1.5.0 发布检查清单

## 📋 发布前检查

### 1. 代码准备
- [x] 更新版本号 `config.py`: VERSION = "1.5.0"
- [x] 扩展PACE_FIELDS数组（frontend/js/charts.js L111-117）
- [x] 扩展FIELD_UNIT_TYPES映射（frontend/js/charts.js L120-129）
- [x] 新增IQ速度字段支持：dr_avg_speed, dr_max_speed, dr_lap_avg_speed, dr_s_avg_speed

### 2. 测试验证
- [x] MCP Playwright自动化测试
  - [x] 场景1: 单独显示dr_speed - Y轴标签、配速格式验证
  - [x] 场景2: 叠加speed + dr_speed - Y轴共享验证
  - [x] JavaScript验证: 只有1个Y轴
- [x] 功能回归测试
  - [x] 活动列表加载正常
  - [x] 字段选择器显示正常
  - [x] 图表渲染正常
  - [x] 多活动对比功能正常

### 3. 文档更新
- [x] 创建 `RELEASE_v1.5.0.md`
- [x] 更新 `README.md` 版本信息和最新更新
- [x] 更新 `agent.md` FR025和US-008状态为已完成
- [x] 更新 `BUGS.md` 添加Issue #25验证记录
- [x] 创建 `RELEASE_CHECKLIST_v1.5.0.md` (本文件)

### 4. 清理工作
- [x] 删除临时测试脚本
  - [x] test_iq_pace_display.py
  - [x] USER_STORY_IQ_PACE.md
  - [x] diagnose_fit.py
  - [x] verify_vosc_fix.py
  - [x] test_fractional_cadence_fix.py
- [x] 删除缓存目录
  - [x] __pycache__/
  - [x] .pytest_cache/
  - [x] .playwright-mcp/
- [x] 删除旧版本打包文件
  - [x] fitanalysis_v1.1.0.zip
  - [x] fitanalysis-v1.4.1-windows.zip

### 5. 打包发布
- [x] 运行 `python build.py`
- [x] 复制 `RELEASE_v1.5.0.md` 到 `dist/fitanalysis/`
- [x] 创建发布压缩包 `fitanalysis-v1.5.0-windows.zip`
- [x] 验证压缩包大小：38.5 MB
- [x] 验证包含文件：
  - [x] fitanalysis.exe
  - [x] frontend/ 目录
  - [x] data/ 目录（空）
  - [x] 启动服务器.bat
  - [x] README.md
  - [x] RELEASE_v1.5.0.md

## 📦 发布包信息

- **文件名**: fitanalysis-v1.5.0-windows.zip
- **大小**: 38,514,437 字节 (约 36.7 MB)
- **包含内容**: 
  - 可执行文件和依赖库
  - 前端资源文件
  - 启动脚本
  - 使用文档

## 🚀 发布步骤

### 1. GitHub发布
```bash
git add .
git commit -m "Release v1.5.0: IQ速度字段配速显示完整支持"
git tag -a v1.5.0 -m "Release v1.5.0"
git push origin main
git push origin v1.5.0
```

### 2. 创建GitHub Release
- 标题: `v1.5.0 - IQ速度字段配速显示完整支持`
- 标签: `v1.5.0`
- 描述: 复制 `RELEASE_v1.5.0.md` 内容
- 附件: `fitanalysis-v1.5.0-windows.zip`

### 3. 通知用户
- 更新项目主页
- 发布更新说明
- 通知测试用户升级

## ✅ 发布后验证

- [ ] GitHub Release页面正常显示
- [ ] 下载链接可用
- [ ] 下载的压缩包可以正常解压和运行
- [ ] 版本号在UI中正确显示
- [ ] 所有新功能正常工作

## 📝 已知问题

无

## 🔄 下一版本计划

待定

---

**发布负责人**: AI Assistant  
**发布日期**: 2025-12-22  
**审核状态**: ✅ 通过
