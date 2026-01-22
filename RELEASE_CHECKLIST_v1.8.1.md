# FIT Running Data Analyzer v1.8.1 Release Checklist

## 📋 Pre-Release Checklist

### 1. Code Preparation
- [ ] Update version in `config.py`: VERSION = "1.8.1"
- [ ] Update version in `fitanalysis.spec`: CFBundleShortVersionString = "1.8.1"
- [ ] Update version in `agent.md`: Section 14版本发布记录
- [ ] Code committed to git
- [ ] Git tag: `git tag -a v1.8.1 -m "Release v1.8.1"`

### 2. Feature Implementation

#### 2.1 Bug #29 修复: IQ圈平均配速显示错误
- [x] 记录bug到BUGS.md（包含用户数据、根本原因、修复方案）
- [x] 更新formatFieldValue()：使用`fieldName.includes('speed')`检测所有速度字段
- [x] 重构renderLapsTable()：移除硬编码检查，统一使用formatFieldValue()
- [x] 添加🧮图标标记聚合字段（pattern: `/(avg|max|min)_\w+|_lap_avg_|_s_avg_/`）
- [x] 创建test_lap_calculated_fields.py测试套件
- [ ] 浏览器验证dr_lap_avg_speed显示"M:SS"格式
- [ ] 浏览器验证🧮图标显示在聚合字段表头
- [ ] 浏览器验证所有IQ速度变体正确转换

#### 2.2 测试套件建立
- [x] 创建TestLapCalculatedFields类（10个lap聚合字段测试）
- [x] 创建TestSessionCalculatedFields类（3个session聚合字段测试）
- [x] 创建TestFrontendFormatting类（3个前端格式化测试）
- [x] 创建TestAggregateFieldDetection类（1个模式检测测试）
- [x] 运行pytest验证100%单元测试通过
- [ ] 上传真实FIT文件完成集成测试
- [ ] 验证13个集成测试全部通过

#### 2.3 文档更新
- [x] 在agent.md添加Section 14（系统架构与数据流）
- [x] 创建7个mermaid图：
  - [x] 14.1 系统整体数据流
  - [x] 14.2 FIT文件解析流水线
  - [x] 14.3 字段分类决策树
  - [x] 14.4 单位转换与格式化流程
  - [x] 14.5 设备映射查询流程
  - [x] 14.6 测试覆盖矩阵
  - [x] 14.7 CSV导出数据流
- [x] 在agent.md添加Section 14.8（测试策略与CI/CD流程）
- [ ] 更新BUGS.md：Bug #29移至"已修复"
- [ ] 创建RELEASE_v1.8.1.md发布说明
- [ ] 更新README.md添加v1.8.1特性

### 3. Testing & Validation

#### 3.1 单元测试
- [x] TestFrontendFormatting::test_speed_to_pace_conversion - PASSED
- [x] TestFrontendFormatting::test_pace_format_validation - PASSED
- [x] TestFrontendFormatting::test_user_reported_bug_case - PASSED (Bug #29专项测试)
- [x] TestAggregateFieldDetection::test_aggregate_pattern_matching - PASSED

#### 3.2 集成测试（需上传FIT文件）
- [ ] TestLapCalculatedFields::test_lap_avg_speed - 验证avg_speed计算正确性
- [ ] TestLapCalculatedFields::test_lap_avg_cadence - 验证avg_cadence聚合值
- [ ] TestLapCalculatedFields::test_lap_avg_vertical_oscillation - 验证垂直振幅聚合
- [ ] TestLapCalculatedFields::test_lap_avg_step_length - 验证步幅聚合
- [ ] TestLapCalculatedFields::test_lap_max_speed - 验证max_speed聚合
- [ ] TestLapCalculatedFields::test_lap_max_cadence - 验证max_cadence聚合
- [ ] TestLapCalculatedFields::test_iq_dr_lap_avg_speed - 验证IQ圈平均速度
- [ ] TestLapCalculatedFields::test_iq_dr_lap_avg_cadence - 验证IQ圈平均步频
- [ ] TestLapCalculatedFields::test_iq_dr_max_speed - 验证IQ最大速度
- [ ] TestLapCalculatedFields::test_iq_dr_max_cadence - 验证IQ最大步频
- [ ] TestSessionCalculatedFields::test_session_avg_speed - 验证session平均速度
- [ ] TestSessionCalculatedFields::test_session_iq_dr_s_avg_speed - 验证session IQ平均速度
- [ ] TestSessionCalculatedFields::test_session_max_values - 验证session最大值

#### 3.3 Playwright E2E测试
- [ ] 上传包含龙豆IQ数据的FIT文件
- [ ] 导航到活动详情页
- [ ] 在单圈表格字段选择器中选择"iq_dr_lap_avg_speed"
- [ ] 验证"圈平均配速"列显示"6:05"格式，而非"2.76"
- [ ] 验证表头显示🧮图标和tooltip "FIT-native aggregate value"
- [ ] 验证其他IQ速度字段（dr_avg_speed, dr_max_speed）也正确转换
- [ ] 截图对比验证UI正确性

#### 3.4 浏览器兼容性测试
- [ ] Chrome最新版：字段选择器、表格渲染、速度转换
- [ ] Edge最新版：字段选择器、表格渲染、速度转换
- [ ] Firefox最新版：字段选择器、表格渲染、速度转换

### 4. Build & Package

#### 4.1 Pre-build检查
- [ ] 运行`python pre_build_check.py`
- [ ] 验证所有文件存在且无语法错误
- [ ] 验证backend/requirements.txt完整性

#### 4.2 构建可执行文件
- [ ] 运行`python build.py`
- [ ] 验证dist/fitanalysis.exe生成成功
- [ ] 检查build/fitanalysis/warn-fitanalysis.txt无严重警告
- [ ] 验证可执行文件大小合理（~50-100MB）

#### 4.3 打包测试
- [ ] 双击运行dist/fitanalysis.exe
- [ ] 验证服务器启动在127.0.0.1:8082
- [ ] 验证浏览器自动打开并显示主页
- [ ] 上传FIT文件测试完整流程
- [ ] 验证Bug #29修复生效（dr_lap_avg_speed显示正确配速格式）
- [ ] 测试CSV导出功能
- [ ] 测试字段选择器（展开/折叠/搜索）
- [ ] 测试图表渲染和交互

### 5. Documentation & Release

#### 5.1 发布说明
- [ ] 创建RELEASE_v1.8.1.md
- [ ] 包含Bug #29详细说明和修复前后对比
- [ ] 列出所有代码变更文件
- [ ] 添加测试结果截图
- [ ] 更新README.md的版本历史

#### 5.2 Git操作
- [ ] 提交所有变更：`git add -A`
- [ ] 提交commit：`git commit -m "Release v1.8.1: Fix Bug #29 IQ lap aggregate speed display"`
- [ ] 创建tag：`git tag -a v1.8.1 -m "Release v1.8.1"`
- [ ] 推送到GitHub：`git push origin main --tags`

#### 5.3 GitHub Release
- [ ] 创建GitHub Release v1.8.1
- [ ] 上传dist/fitanalysis.exe
- [ ] 复制RELEASE_v1.8.1.md内容到Release Notes
- [ ] 标记为Latest Release

### 6. Post-Release Validation

#### 6.1 下载验证
- [ ] 从GitHub下载fitanalysis.exe
- [ ] 在新环境运行验证功能正常
- [ ] 测试Bug #29已修复

#### 6.2 文档更新
- [ ] 更新README.md添加v1.8.1下载链接
- [ ] 更新BUGS.md确认Bug #29状态为"已修复"

---

## 📝 发布注意事项

### 关键改动
1. **formatFieldValue()** - 简化速度检测逻辑为`fieldName.includes('speed')`
2. **renderLapsTable()** - 移除硬编码字段检查，统一使用formatFieldValue()
3. **🧮图标** - 新增聚合字段视觉标识，提升用户体验
4. **测试套件** - 17个测试用例确保聚合字段正确性

### 向后兼容性
- ✅ 完全兼容v1.8.0数据格式
- ✅ 不需要重新上传FIT文件
- ✅ 不影响现有功能（CSV导出、图表、标准字段）

### 已知限制
- 集成测试需要真实FIT文件（546218476_ACTIVITY.fit未在仓库中）
- Playwright E2E测试需要手动执行验证

---

## ✅ Release Approval

- [ ] **开发者检查**: 所有功能已实现并测试通过
- [ ] **测试检查**: 单元测试100%通过，集成测试完成
- [ ] **文档检查**: RELEASE notes、BUGS.md、agent.md已更新
- [ ] **构建检查**: 可执行文件构建成功且运行正常
- [ ] **最终批准**: 准备发布到GitHub

---

**发布负责人**: _____________  
**发布日期**: 2026-01-22  
**版本**: v1.8.1
