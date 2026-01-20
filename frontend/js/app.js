// FIT跑步数据分析器 - 主应用逻辑

const API_BASE = '/api';

// 全局状态
const state = {
    currentView: 'list',
    currentActivityId: null,
    currentActivity: null,
    selectedActivityIds: new Set(),
    currentPage: 1,
    totalPages: 1,
    filters: {
        sortBy: 'date',
        sortOrder: 'desc',
        dateFrom: null,
        dateTo: null,
        distMin: null,
        distMax: null
    }
};

// ==================== 初始化 ====================
document.addEventListener('DOMContentLoaded', async () => {
    initEventListeners();
    initXAxisToggle();  // 初始化X轴切换按钮
    showLoadingState();  // 显示加载状态
    
    // v1.8.0: 优先加载设备配置（供动态字段标签使用）
    await loadDeviceFieldConfigs();
    
    loadActivities();
    loadVersion();  // Load and display version
});

// ==================== 事件监听器 ====================
function initEventListeners() {
    // 上传文件 - 现在使用label触发，无需手动监听按钮
    document.getElementById('fileInput').addEventListener('change', handleFileUpload);
    
    // 视图切换
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
    
    // 排序和过滤
    document.getElementById('sortBy').addEventListener('change', loadActivities);
    document.getElementById('sortOrder').addEventListener('change', loadActivities);
    document.getElementById('applyFilter').addEventListener('click', applyFilters);
    document.getElementById('resetFilter').addEventListener('click', resetFilters);
    
    // 分页
    document.getElementById('prevPage').addEventListener('click', () => changePage(-1));
    document.getElementById('nextPage').addEventListener('click', () => changePage(1));
    
    // 全选
    document.getElementById('selectAll').addEventListener('change', handleSelectAll);
    
    // 批量操作
    document.getElementById('compareSelected').addEventListener('click', compareSelectedActivities);
    document.getElementById('deleteSelected').addEventListener('click', deleteSelectedActivities);
    
    // v1.8.0: Reset All button
    const resetAllBtn = document.getElementById('resetAllBtn');
    if (resetAllBtn) {
        resetAllBtn.addEventListener('click', handleResetAll);
    }
    
    // 详情页
    document.getElementById('backToList').addEventListener('click', () => switchView('list'));
    document.getElementById('backToListFromCompare').addEventListener('click', () => switchView('list'));
    
    // 导出
    document.getElementById('exportCsvBtn').addEventListener('click', toggleExportDropdown);

    // 合并离线心率CSV - 现在使用label触发，只需监听文件选择
    const hrCsvInput = document.getElementById('hrCsvInput');
    if (hrCsvInput) {
        hrCsvInput.addEventListener('change', handleHrCsvMergeUpload);
    }
    
    // 内容标签页
    document.querySelectorAll('.content-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.content-tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.content-panel').forEach(p => p.classList.remove('active'));
            btn.classList.add('active');
            document.getElementById(btn.dataset.content + 'Content').classList.add('active');
        });
    });
    
    // v1.8.0: 字段选择器控制按钮
    // 趋势图控制
    const trendsSelectAll = document.getElementById('trendsSelectAll');
    const trendsDeselectAll = document.getElementById('trendsDeselectAll');
    const trendsTogglePanel = document.getElementById('trendsTogglePanel');
    const trendFieldSearch = document.getElementById('trendFieldSearch');
    
    if (trendsSelectAll) {
        trendsSelectAll.addEventListener('click', () => {
            document.querySelectorAll('#fieldCheckboxes .field-checkbox').forEach(cb => {
                if (!cb.checked) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change'));
                }
            });
        });
    }
    
    if (trendsDeselectAll) {
        trendsDeselectAll.addEventListener('click', () => {
            document.querySelectorAll('#fieldCheckboxes .field-checkbox').forEach(cb => {
                if (cb.checked) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change'));
                }
            });
        });
    }
    
    if (trendsTogglePanel) {
        trendsTogglePanel.addEventListener('click', () => toggleFieldSelectorPanel('trends'));
    }
    
    if (trendFieldSearch) {
        trendFieldSearch.addEventListener('input', (e) => handleFieldSearch(e.target, 'fieldCheckboxes'));
    }
    
    // 每圈数据控制
    const lapsSelectAll = document.getElementById('lapsSelectAll');
    const lapsDeselectAll = document.getElementById('lapsDeselectAll');
    const lapsTogglePanel = document.getElementById('lapsTogglePanel');
    const lapFieldSearch = document.getElementById('lapFieldSearch');
    
    if (lapsSelectAll) {
        lapsSelectAll.addEventListener('click', () => {
            document.querySelectorAll('#lapFieldCheckboxes .field-checkbox').forEach(cb => {
                if (!cb.checked) {
                    cb.checked = true;
                    cb.dispatchEvent(new Event('change'));
                }
            });
        });
    }
    
    if (lapsDeselectAll) {
        lapsDeselectAll.addEventListener('click', () => {
            document.querySelectorAll('#lapFieldCheckboxes .field-checkbox').forEach(cb => {
                if (cb.checked) {
                    cb.checked = false;
                    cb.dispatchEvent(new Event('change'));
                }
            });
        });
    }
    
    if (lapsTogglePanel) {
        lapsTogglePanel.addEventListener('click', () => toggleFieldSelectorPanel('laps'));
    }
    
    if (lapFieldSearch) {
        lapFieldSearch.addEventListener('input', (e) => handleFieldSearch(e.target, 'lapFieldCheckboxes'));
    }
    
    // 点击外部关闭下拉菜单
    document.addEventListener('click', (e) => {
        const dropdown = document.getElementById('exportDropdown');
        const exportBtn = document.getElementById('exportCsvBtn');
        if (!exportBtn.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = 'none';
        }
    });
}

// ==================== 合并离线心率CSV ====================
async function handleHrCsvMergeUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    if (!state.currentActivityId) {
        showStatus('未选择活动，无法合并', 'error');
        e.target.value = '';
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showStatus('正在合并离线心率CSV...');

    try {
        const response = await fetch(`${API_BASE}/activity/${state.currentActivityId}/merge/hr_csv`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.detail || '合并失败');
        }

        // Show success message with link to activities list
        const newActivityName = result.new_activity_name || '[HR合并]活动';
        showStatus(`✓ 已创建新活动: ${newActivityName} - <a href="#" onclick="switchView('list'); return false;" style="color: white; text-decoration: underline;">查看活动列表</a>`, 'success');
        
        // Stay on current activity page (do not auto-navigate)
    } catch (error) {
        showStatus(`✗ 合并失败: ${error.message}`, 'error');
    } finally {
        e.target.value = '';
    }
}

// ==================== 视图切换 ====================
function switchView(view) {
    state.currentView = view;
    
    // 隐藏所有视图
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    
    // 显示目标视图
    document.getElementById(view + 'View').classList.add('active');
    document.querySelector(`[data-view="${view}"]`).classList.add('active');
}

// ==================== 文件上传 ====================
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    showStatus('正在上传和解析FIT文件...');
    
    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showStatus(`✓ ${result.message}`, 'success');
            loadActivities();
            
            // 清空文件输入
            e.target.value = '';
        } else {
            showStatus(`✗ ${result.error || '上传失败'}`, 'error');
        }
    } catch (error) {
        showStatus(`✗ 上传失败: ${error.message}`, 'error');
    }
}

// ==================== 加载活动列表 ====================
async function loadActivities() {
    const sortBy = document.getElementById('sortBy').value;
    const sortOrder = document.getElementById('sortOrder').value;
    
    const params = new URLSearchParams({
        sort: sortBy,
        order: sortOrder,
        page: state.currentPage,
        limit: 20
    });
    
    // 添加过滤参数
    if (state.filters.dateFrom) params.append('date_from', state.filters.dateFrom);
    if (state.filters.dateTo) params.append('date_to', state.filters.dateTo);
    if (state.filters.distMin !== null) params.append('distance_min', state.filters.distMin);
    if (state.filters.distMax !== null) params.append('distance_max', state.filters.distMax);
    
    try {
        const response = await fetch(`${API_BASE}/activities?${params}`);
        const data = await response.json();
        
        renderActivityTable(data.activities);
        updatePagination(data.page, data.total, data.limit);
    } catch (error) {
        console.error('Failed to load activities:', error);
        showStatus('加载活动列表失败', 'error');
    }
}

// ==================== 渲染活动表格 ====================
function showLoadingState() {
    const tbody = document.getElementById('activityTableBody');
    tbody.innerHTML = '<tr><td colspan="8" class="loading">加载中...</td></tr>';
}

function renderActivityTable(activities) {
    const tbody = document.getElementById('activityTableBody');
    
    if (activities.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">暂无活动数据</td></tr>';
        return;
    }
    
    tbody.innerHTML = activities.map(activity => `
        <tr data-id="${activity.id}">
            <td><input type="checkbox" class="activity-checkbox" data-id="${activity.id}"></td>
            <td>${formatDate(activity.date)}</td>
            <td class="activity-name">${activity.name}</td>
            <td>${activity.distance_km.toFixed(2)} km</td>
            <td>${formatDuration(activity.duration_sec)}</td>
            <td>${activity.avg_pace}</td>
            <td>${activity.avg_heart_rate || '--'} bpm</td>
            <td>
                <button class="btn btn-secondary btn-sm view-detail" data-id="${activity.id}">查看</button>
                <button class="btn btn-danger btn-sm delete-activity" data-id="${activity.id}">删除</button>
            </td>
        </tr>
    `).join('');
    
    // 添加事件监听器
    tbody.querySelectorAll('.view-detail').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            viewActivityDetail(btn.dataset.id);
        });
    });
    
    tbody.querySelectorAll('.delete-activity').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            deleteActivity(btn.dataset.id);
        });
    });
    
    tbody.querySelectorAll('.activity-checkbox').forEach(cb => {
        cb.addEventListener('change', handleActivitySelect);
    });
    
    // 行点击
    tbody.querySelectorAll('tr').forEach(row => {
        row.addEventListener('click', (e) => {
            if (!e.target.closest('button') && !e.target.closest('input')) {
                viewActivityDetail(row.dataset.id);
            }
        });
    });
}

// ==================== 分页 ====================
function updatePagination(page, total, limit) {
    state.currentPage = page;
    state.totalPages = Math.ceil(total / limit);
    
    document.getElementById('pageInfo').textContent = `第 ${page} / ${state.totalPages} 页 (共 ${total} 条)`;
    document.getElementById('prevPage').disabled = page <= 1;
    document.getElementById('nextPage').disabled = page >= state.totalPages;
}

function changePage(delta) {
    state.currentPage += delta;
    if (state.currentPage < 1) state.currentPage = 1;
    if (state.currentPage > state.totalPages) state.currentPage = state.totalPages;
    loadActivities();
}

// ==================== 过滤 ====================
function applyFilters() {
    state.filters.dateFrom = document.getElementById('filterDateFrom').value || null;
    state.filters.dateTo = document.getElementById('filterDateTo').value || null;
    state.filters.distMin = parseFloat(document.getElementById('filterDistMin').value) || null;
    state.filters.distMax = parseFloat(document.getElementById('filterDistMax').value) || null;
    
    state.currentPage = 1;
    loadActivities();
}

function resetFilters() {
    state.filters = {
        sortBy: 'date',
        sortOrder: 'desc',
        dateFrom: null,
        dateTo: null,
        distMin: null,
        distMax: null
    };
    
    document.getElementById('filterDateFrom').value = '';
    document.getElementById('filterDateTo').value = '';
    document.getElementById('filterDistMin').value = '';
    document.getElementById('filterDistMax').value = '';
    
    state.currentPage = 1;
    loadActivities();
}

// ==================== 活动选择 ====================
function handleSelectAll(e) {
    const checkboxes = document.querySelectorAll('.activity-checkbox');
    checkboxes.forEach(cb => {
        cb.checked = e.target.checked;
        if (e.target.checked) {
            state.selectedActivityIds.add(cb.dataset.id);
        } else {
            state.selectedActivityIds.delete(cb.dataset.id);
        }
    });
    updateBatchActions();
}

function handleActivitySelect(e) {
    if (e.target.checked) {
        // 检查是否超过10个活动限制
        if (state.selectedActivityIds.size >= 10) {
            e.target.checked = false;
            showStatus('最多只能选择10个活动进行对比', 'error');
            return;
        }
        state.selectedActivityIds.add(e.target.dataset.id);
    } else {
        state.selectedActivityIds.delete(e.target.dataset.id);
    }
    updateBatchActions();
    updateActivityCheckboxStates();
}

function updateBatchActions() {
    const count = state.selectedActivityIds.size;
    document.getElementById('compareSelected').style.display = count >= 2 ? 'inline-block' : 'none';
    document.getElementById('deleteSelected').style.display = count > 0 ? 'inline-block' : 'none';
    
    // 更新对比按钮文本，显示活动数提示
    const compareBtn = document.getElementById('compareSelected');
    if (count >= 10) {
        compareBtn.textContent = `对比选中活动 (${count}/10)`;
        compareBtn.style.color = '#e74c3c';
    } else {
        compareBtn.textContent = `对比选中活动 (${count})`;
        compareBtn.style.color = '';
    }
}

function updateActivityCheckboxStates() {
    const checkboxes = document.querySelectorAll('.activity-checkbox');
    checkboxes.forEach(cb => {
        // 如果已经选择了10个活动，并且当前复选框未选中，则禁用
        if (state.selectedActivityIds.size >= 10 && !cb.checked) {
            cb.disabled = true;
            cb.parentElement.parentElement.style.opacity = '0.5';
        } else {
            cb.disabled = false;
            cb.parentElement.parentElement.style.opacity = '1';
        }
    });
}

// ==================== 查看活动详情 ====================
async function viewActivityDetail(activityId) {
    state.currentActivityId = activityId;
    
    try {
        const response = await fetch(`${API_BASE}/activity/${activityId}`);
        const activity = await response.json();
        
        state.currentActivity = activity;
        
        renderActivityDetail(activity);
        document.getElementById('detailTab').style.display = 'block';
        switchView('detail');
    } catch (error) {
        console.error('Failed to load activity:', error);
        showStatus('加载活动详情失败', 'error');
    }
}

// ==================== 渲染活动详情 ====================
function renderActivityDetail(activity) {
    // 设置标题
    document.getElementById('activityName').textContent = activity.name;
    
    // 重新初始化X轴切换按钮
    initXAxisToggle();
    
    // 渲染汇总卡片
    const summaryCards = document.getElementById('summaryCards');
    const session = activity.session;
    const mergeMethodLabel = formatMergeMethod(activity.merge_provenance);
    
    summaryCards.innerHTML = `
        <div class="summary-card">
            <div class="label">距离</div>
            <div class="value">${((session.total_distance || 0) / 1000).toFixed(2)}<span class="unit">km</span></div>
        </div>
        <div class="summary-card">
            <div class="label">时长</div>
            <div class="value">${formatDuration(session.total_elapsed_time)}</div>
        </div>
        <div class="summary-card">
            <div class="label">配速</div>
            <div class="value">${speedToPace(session.avg_speed)}<span class="unit">min/km</span></div>
        </div>
        <div class="summary-card">
            <div class="label">平均心率</div>
            <div class="value">${session.avg_heart_rate || '--'}<span class="unit">bpm</span></div>
        </div>
        <div class="summary-card">
            <div class="label">平均步频</div>
            <div class="value">${session.avg_cadence || '--'}<span class="unit">spm</span></div>
        </div>
        <div class="summary-card">
            <div class="label">平均功率</div>
            <div class="value">${session.avg_power || '--'}<span class="unit">W</span></div>
        </div>
        <div class="summary-card">
            <div class="label">合并方式</div>
            <div class="value">${mergeMethodLabel}</div>
        </div>
    `;
    
    // 渲染字段选择器
    renderFieldSelector(activity.available_fields, activity.available_iq_fields);
    
    // 渲染单圈字段选择器和表格
    if (activity.laps && activity.laps.length > 0) {
        renderLapFieldSelector(activity.laps);
    } else {
        // 无单圈数据时直接渲染空表格
        renderLapsTable([], []);
    }
    
    // 初始化趋势图（默认选中心率和步频）
    const defaultFields = ['heart_rate', 'cadence'];
    updateTrendChart(activity, defaultFields);
}

// ==================== 单圈字段提取和过滤 ====================

/**
 * 提取单圈数据的可用字段（过滤100%为空的字段）
 * @param {Array} laps - 单圈数据数组
 * @returns {Object} {standardFields: Array, iqFields: Array}
 */
function extractAvailableLapFields(laps) {
    if (!laps || laps.length === 0) {
        return { standardFields: [], iqFields: [] };
    }
    
    // 定义所有可能的标准字段
    const allStandardFields = [
        'lap_number', 'start_time', 'total_elapsed_time', 'total_distance',
        'avg_speed', 'max_speed', 'avg_heart_rate', 'max_heart_rate',
        'avg_cadence', 'max_cadence', 'avg_power', 'max_power',
        'total_ascent', 'total_descent', 'avg_vertical_oscillation',
        'avg_stance_time', 'avg_step_length', 'total_calories'
    ];
    
    // 过滤100%为空的标准字段
    const availableStandardFields = allStandardFields.filter(field => 
        !laps.every(lap => lap[field] == null)
    );
    
    // 提取所有IQ字段并加iq_前缀
    const iqFieldSet = new Set();
    laps.forEach(lap => {
        if (lap.iq_fields) {
            Object.keys(lap.iq_fields).forEach(key => {
                iqFieldSet.add('iq_' + key);
            });
        }
    });
    
    // 过滤100%为空的IQ字段
    const availableIqFields = Array.from(iqFieldSet).filter(field => {
        const rawKey = field.replace('iq_', '');
        return !laps.every(lap => 
            !lap.iq_fields || lap.iq_fields[rawKey] == null
        );
    });
    
    return {
        standardFields: availableStandardFields,
        iqFields: availableIqFields
    };
}

/**
 * 渲染单圈字段选择器
 * @param {Array} laps - 单圈数据数组
 */
function renderLapFieldSelector(laps) {
    const { standardFields, iqFields } = extractAvailableLapFields(laps);
    
    if (standardFields.length === 0 && iqFields.length === 0) {
        return;
    }
    
    // 从localStorage加载保存的字段选择，如无则使用默认值
    const defaultSelected = loadFieldSelection('lap_selected_fields', [
        'lap_number', 'total_elapsed_time', 'total_distance', 'avg_speed', 'avg_heart_rate'
    ]);
    
    renderUnifiedFieldSelector({
        mode: 'single',
        standardFields: standardFields,
        iqFields: iqFields,
        fieldGroups: LAP_FIELD_GROUPS,  // 使用单圈字段分组配置
        selectionType: 'checkbox',
        defaultSelected: defaultSelected,
        onChange: () => {
            const container = document.getElementById('lapFieldCheckboxes');
            const selectedFields = Array.from(container.querySelectorAll('.field-checkbox:checked'))
                .map(cb => cb.value);
            
            // 保存字段选择到localStorage
            saveFieldSelection('lap_selected_fields', selectedFields);
            
            // 更新单圈表格
            renderLapsTable(laps, selectedFields);
        },
        containerId: 'lapFieldCheckboxes'
    });
    
    // 初始渲染表格
    const container = document.getElementById('lapFieldCheckboxes');
    const selectedFields = Array.from(container.querySelectorAll('.field-checkbox:checked'))
        .map(cb => cb.value);
    renderLapsTable(laps, selectedFields);
}

/**
 * 格式化相对时间（相对于基准时间）
 * @param {string} currentTime - 当前时间（ISO字符串）
 * @param {string} baseTime - 基准时间（ISO字符串）
 * @returns {string} 格式化的相对时间 (+MM:SS)
 */
function formatRelativeTime(currentTime, baseTime) {
    if (!currentTime || !baseTime) return '--';
    
    try {
        const diffMs = new Date(currentTime) - new Date(baseTime);
        const diffSec = Math.floor(diffMs / 1000);
        
        const minutes = Math.floor(diffSec / 60);
        const seconds = diffSec % 60;
        
        return `+${minutes}:${seconds.toString().padStart(2, '0')}`;
    } catch (e) {
        return '--';
    }
}

function formatMergeMethod(mergeProvenance) {
    if (!mergeProvenance || !mergeProvenance.method) return '--';
    switch (mergeProvenance.method) {
        case 'metadata_align':
            return '元数据对齐';
        case 'linear_interpolate':
            return '线性插值';
        default:
            return '--';
    }
}

// ==================== 工具函数 ====================
function formatDate(dateStr) {
    if (!dateStr) return '--';
    const date = new Date(dateStr);
    return date.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' });
}

function formatDuration(seconds) {
    if (!seconds) return '--:--';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
}

function speedToPace(speedMps) {
    if (!speedMps || speedMps <= 0) return '--:--';
    const paceSeconds = 1000 / speedMps;
    const minutes = Math.floor(paceSeconds / 60);
    const seconds = Math.floor(paceSeconds % 60);
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

function showStatus(message, type = 'info') {
    const statusDiv = document.getElementById('uploadStatus');
    const statusText = document.getElementById('uploadStatusText');
    
    statusText.innerHTML = message;  // Use innerHTML to support HTML links
    statusDiv.style.display = 'block';
    
    if (type === 'success' || type === 'error') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 3000);
    }
}

// ==================== 删除活动 ====================
async function deleteActivity(activityId) {
    if (!confirm('确定要删除这个活动吗？')) return;
    
    try {
        await fetch(`${API_BASE}/activity/${activityId}`, { method: 'DELETE' });
        showStatus('活动已删除', 'success');
        loadActivities();
    } catch (error) {
        showStatus('删除失败', 'error');
    }
}

async function deleteSelectedActivities() {
    if (!confirm(`确定要删除选中的 ${state.selectedActivityIds.size} 个活动吗？`)) return;
    
    for (const id of state.selectedActivityIds) {
        try {
            await fetch(`${API_BASE}/activity/${id}`, { method: 'DELETE' });
        } catch (error) {
            console.error(`Failed to delete ${id}:`, error);
        }
    }
    
    state.selectedActivityIds.clear();
    showStatus('已删除选中的活动', 'success');
    loadActivities();
}

// ==================== v1.8.0: Reset All (删除所有活动) ====================
async function handleResetAll() {
    const confirmMsg = '⚠️ 警告：此操作将删除所有活动数据，且不可恢复！\n\n确定要继续吗？';
    if (!confirm(confirmMsg)) return;
    
    // 二次确认
    const doubleConfirm = '再次确认：真的要删除所有活动吗？';
    if (!confirm(doubleConfirm)) return;
    
    showStatus('正在删除所有活动...', 'warning');
    
    try {
        const response = await fetch(`${API_BASE}/activities/all`, { 
            method: 'DELETE' 
        });
        
        if (!response.ok) {
            throw new Error('删除失败');
        }
        
        const result = await response.json();
        const deletedCount = result.deleted_count || 0;
        
        showStatus(`✓ 成功删除 ${deletedCount} 个活动`, 'success');
        
        // 清空选中状态并刷新列表
        state.selectedActivityIds.clear();
        loadActivities();
    } catch (error) {
        console.error('Reset all failed:', error);
        showStatus(`✗ 删除失败: ${error.message}`, 'error');
    }
}

// ==================== 多活动对比 ====================
function compareSelectedActivities() {
    if (state.selectedActivityIds.size < 2) {
        alert('请至少选择2个活动进行对比');
        return;
    }
    
    if (state.selectedActivityIds.size > 10) {
        alert('最多只能选择10个活动进行对比');
        return;
    }
    
    document.getElementById('compareTab').style.display = 'block';
    switchView('compare');
    
    // 重新初始化X轴切换按钮
    initXAxisToggle();
    
    // 显示选中的活动（带颜色标记）
    renderSelectedActivitiesForCompare();
    
    // 加载字段选择器
    loadCompareFieldSelector();
    
    // 添加对齐方式change事件监听器
    document.querySelectorAll('input[name="alignBy"]').forEach(radio => {
        radio.addEventListener('change', () => {
            triggerCompareChartUpdate();
        });
    });
}

async function renderSelectedActivitiesForCompare() {
    const container = document.getElementById('selectedActivitiesList');
    
    // 获取选中活动的详细信息
    try {
        const activityIds = Array.from(state.selectedActivityIds);
        const activities = await Promise.all(
            activityIds.map(id => fetch(`${API_BASE}/activity/${id}`).then(r => r.json()))
        );
        
        renderSelectedActivitiesWithColors(activities);
    } catch (error) {
        console.error('Failed to load activity details:', error);
        container.innerHTML = `<p>已选中 ${state.selectedActivityIds.size} 个活动进行对比</p>`;
    }
}

// 导出下拉菜单
function toggleExportDropdown() {
    const dropdown = document.getElementById('exportDropdown');
    dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    
    // 添加点击事件
    if (dropdown.style.display === 'block') {
        dropdown.querySelectorAll('.dropdown-item').forEach(item => {
            item.onclick = () => {
                const mode = item.dataset.mode;
                const dataType = item.dataset.type || 'records';
                exportActivity(state.currentActivityId, mode, dataType);
                dropdown.style.display = 'none';
            };
        });
    }
}

async function exportActivity(activityId, mode, dataType) {
    const url = `${API_BASE}/export/${activityId}?mode=${mode}&data_type=${dataType}`;
    window.open(url, '_blank');
    showStatus('导出已开始...', 'success');
}

// ==================== Version Display ====================
async function loadVersion() {
    try {
        const response = await fetch(`${API_BASE}/version`);
        const data = await response.json();
        const versionDisplay = document.getElementById('versionDisplay');
        if (versionDisplay && data.version) {
            versionDisplay.textContent = `v${data.version}`;
        }
    } catch (error) {
        console.error('Failed to load version:', error);
    }
}

