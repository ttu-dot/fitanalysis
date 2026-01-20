// FIT跑步数据分析器 - 图表模块 (Plotly.js)

// ==================== v1.8.0: 全局设备配置 ====================

/**
 * 设备字段配置缓存（从API加载）
 * 结构: { dragonrun: { device_name, field_prefix, display_prefix, fields: [...] } }
 */
window.deviceConfigs = null;

/**
 * 字段配置Map（优化查找性能）
 * 结构: Map<field_name, FieldConfig>
 */
window.deviceFieldsMap = null;

// ==================== localStorage 持久化工具函数 ====================

/**
 * 保存字段选择到localStorage
 * @param {string} key - 存储键名
 * @param {Array} fields - 字段数组
 */
function saveFieldSelection(key, fields) {
    try {
        localStorage.setItem(key, JSON.stringify(fields));
    } catch (e) {
        console.warn('Failed to save field selection:', e);
    }
}

/**
 * 从localStorage加载字段选择
 * @param {string} key - 存储键名
 * @param {Array} defaultFields - 默认字段数组
 * @returns {Array} 保存的字段数组或默认值
 */
function loadFieldSelection(key, defaultFields) {
    try {
        const saved = localStorage.getItem(key);
        return saved ? JSON.parse(saved) : defaultFields;
    } catch (e) {
        console.warn('Failed to load field selection:', e);
        return defaultFields;
    }
}

// ==================== v1.8.0: 字段选择器UI控制函数 ====================

/**
 * 切换字段选择器面板的展开/折叠状态
 * @param {string} mode - 'trend' | 'lap'
 */
function toggleFieldSelectorPanel(mode) {
    const container = document.querySelector(`#${mode}Content .field-selector-container`);
    const button = document.getElementById(`${mode}TogglePanel`);
    if (!container || !button) return;
    
    const isCollapsed = container.getAttribute('data-collapsed') === 'true';
    container.setAttribute('data-collapsed', !isCollapsed);
    button.textContent = isCollapsed ? '▼ 收起面板' : '▲ 展开面板';
    
    // 保存状态到localStorage
    try {
        localStorage.setItem(`field_selector_collapsed_${mode}`, !isCollapsed);
    } catch (e) {
        console.warn('Failed to save panel state:', e);
    }
}

/**
 * 处理字段搜索过滤
 * @param {HTMLInputElement} input - 搜索输入框
 * @param {string} containerId - 字段容器ID
 */
function handleFieldSearch(input, containerId) {
    const searchTerm = input.value.toLowerCase().trim();
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const cards = container.querySelectorAll('.field-group-card');
    
    cards.forEach(card => {
        const labels = card.querySelectorAll('.field-group-card__content label');
        let hasMatch = false;
        
        labels.forEach(label => {
            const text = label.textContent.toLowerCase();
            const matches = !searchTerm || text.includes(searchTerm);
            
            if (matches) {
                hasMatch = true;
                label.classList.add('highlighted');
            } else {
                label.classList.remove('highlighted');
            }
            
            label.style.display = matches ? 'flex' : 'none';
        });
        
        // 隐藏没有匹配项的卡片
        card.classList.toggle('hidden', !hasMatch);
    });
}

/**
 * 获取字段分组图标 (Emoji)
 * @param {string} groupKey - 分组键名
 * @returns {string} 图标emoji
 */
function getFieldGroupIcon(groupKey) {
    const icons = {
        basic: '📊',
        pace: '⚡',
        heartRate: '💓',
        cadence: '👟',
        power: '⚡',
        elevation: '📈',
        environment: '🌡️',
        dynamics: '🏃',
        dragonPower: '⚡',
        dragonImpact: '💥',
        dragonDynamics: '🏃',
        dragonOther: '📈',
        imported: '📥',
        uncategorized: '📦',
        calories: '🔥'
    };
    return icons[groupKey] || '📁';
}

/**
 * v1.8.0: 从API加载设备字段配置
 * 在DOMContentLoaded时调用，缓存到全局变量
 */
async function loadDeviceFieldConfigs() {
    if (window.deviceConfigs) {
        return window.deviceConfigs; // 已加载
    }
    
    try {
        const response = await fetch(`${API_BASE}/device-mappings`);
        if (!response.ok) {
            throw new Error(`API returned ${response.status}`);
        }
        
        const configs = await response.json();
        window.deviceConfigs = configs;
        
        // 构建字段Map以优化查找性能
        window.deviceFieldsMap = new Map();
        for (const deviceId in configs) {
            const device = configs[deviceId];
            if (device.fields && Array.isArray(device.fields)) {
                device.fields.forEach(field => {
                    window.deviceFieldsMap.set(field.field_name, {
                        ...field,
                        device_id: deviceId,
                        device_prefix: device.field_prefix,
                        display_prefix: device.display_prefix
                    });
                });
            }
        }
        
        console.log(`✓ Loaded device configs: ${Object.keys(configs).length} devices, ${window.deviceFieldsMap.size} fields`);
        return configs;
    } catch (error) {
        console.error('Failed to load device configs:', error);
        // 降级到硬编码标签
        window.deviceConfigs = {};
        window.deviceFieldsMap = new Map();
        return {};
    }
}

/**
 * v1.8.0: 将速度(m/s)转换为配速(min/km)
 * @param {number} speedMs - 速度，单位m/s
 * @returns {string} 配速字符串，格式 "M:SS" 或 "M:SS/km"
 */
function speed_to_pace(speedMs) {
    if (!speedMs || speedMs <= 0) return '--:--';
    
    const paceSeconds = 1000 / speedMs; // 秒/公里
    const minutes = Math.floor(paceSeconds / 60);
    const seconds = Math.round(paceSeconds % 60);
    
    return `${minutes}:${seconds.toString().padStart(2, '0')}`;
}

/**
 * v1.8.0: 格式化字段值（处理单位转换）
 * @param {string} fieldName - 字段名
 * @param {number} value - 原始值
 * @param {number} precision - 小数位数（可选）
 * @returns {string} 格式化后的值
 */
function formatFieldValue(fieldName, value, precision = 2) {
    if (value === null || value === undefined) return '--';
    
    // 从设备配置中查找字段
    const fieldConfig = window.deviceFieldsMap ? window.deviceFieldsMap.get(fieldName) : null;
    
    if (fieldConfig && fieldConfig.requires_conversion) {
        // dr_speed需要转换为配速
        if (fieldName === 'dr_speed' || fieldName.includes('speed')) {
            return speed_to_pace(value);
        }
    }
    
    // 使用配置中的precision，或使用传入的precision
    const decimals = fieldConfig && fieldConfig.precision !== undefined 
        ? fieldConfig.precision 
        : precision;
    
    return typeof value === 'number' 
        ? value.toFixed(decimals) 
        : value.toString();
}

// ==================== 字段显示名称映射 ====================

const FIELD_LABELS = {
    // 心率
    heart_rate: '心率 (bpm)',
    avg_heart_rate: '平均心率 (bpm)',
    max_heart_rate: '最大心率 (bpm)',
    // 配速/速度
    speed: '配速 (min/km)',
    enhanced_speed: '配速 (min/km)',
    avg_speed: '平均配速 (min/km)',
    max_speed: '最快配速 (min/km)',
    // 功率
    power: '功率 (W)',
    avg_power: '平均功率 (W)',
    max_power: '最大功率 (W)',
    // 步频
    cadence: '步频 (spm)',
    avg_cadence: '平均步频 (spm)',
    max_cadence: '最大步频 (spm)',
    // 海拔
    altitude: '海拔 (m)',
    enhanced_altitude: '海拔 (m)',
    total_ascent: '累计爬升 (m)',
    total_descent: '累计下降 (m)',
    // 坡度/温度
    grade: '坡度 (%)',
    temperature: '温度 (°C)',
    avg_temperature: '平均温度 (°C)',
    // 跑步动态
    vertical_oscillation: '垂直振幅 (cm)',
    avg_vertical_oscillation: '平均垂直振幅 (cm)',
    stance_time: '触地时间 (ms)',
    avg_stance_time: '平均触地时间 (ms)',
    stance_time_balance: '触地平衡 (%)',
    step_length: '步幅 (m)',
    avg_step_length: '平均步幅 (m)',
    stride_length: '步幅 (m)',
    // 距离/热量
    distance: '距离 (km)',
    total_distance: '总距离 (km)',
    total_calories: '热量消耗 (kcal)',
    // IQ 常用字段（标准字段）
    gct: '触地时间 (ms)',
    air_time: '腾空时间 (ms)',
    v_osc: '垂直振幅 (cm)',
    v_pif: '冲击峰值',
    bias: '左右平衡 (%)'
};

// 获取字段显示标签（v1.8.0: 使用动态配置）
function getFieldLabel(field, isIqField = false) {
    // 移除iq_前缀获取实际字段名
    const fieldKey = field.replace('iq_', '');
    
    if (isIqField || field.startsWith('iq_')) {
        // v1.8.0: 优先从设备配置Map中查找
        if (window.deviceFieldsMap && window.deviceFieldsMap.has(fieldKey)) {
            const config = window.deviceFieldsMap.get(fieldKey);
            return config.full_label; // 已包含前缀，如 "DR_触地时间 (ms)"
        }
        
        // 处理Lap字段动态标签生成 (v1.8.0)
        if (fieldKey.startsWith('dr_lap_avg_')) {
            const baseField = fieldKey.replace('dr_lap_avg_', 'dr_');
            if (window.deviceFieldsMap && window.deviceFieldsMap.has(baseField)) {
                const baseConfig = window.deviceFieldsMap.get(baseField);
                return `圈平均${baseConfig.display_label} (${baseConfig.unit})`;
            }
        }
        
        // 导入字段：不使用DR_前缀
        if (fieldKey === 'imported_hr') {
            return '导入_心率 (bpm)';
        }
        if (fieldKey.startsWith('imported_') && fieldKey.endsWith('_hr')) {
            const device = fieldKey.substring('imported_'.length, fieldKey.length - '_hr'.length);
            return device ? `导入_${device}_心率 (bpm)` : '导入_心率 (bpm)';
        }
        
        // 未定义的IQ字段，自动添加DR_前缀（降级处理）
        const baseLabel = FIELD_LABELS[fieldKey] || fieldKey.replace(/_/g, ' ');
        return `DR_${baseLabel}`;
    }
    
    // 标准字段
    return FIELD_LABELS[field] || field;
}

// 需要转换为配速的字段
const PACE_FIELDS = [
    'speed', 'enhanced_speed', 'avg_speed', 'max_speed',
    // IQ字段速度变体
    'dr_speed', 'dr_avg_speed', 'dr_max_speed',
    'dr_lap_avg_speed', 'dr_s_avg_speed'
];

// 字段单位类型映射 - 相同单位类型的字段共享Y轴
const FIELD_UNIT_TYPES = {
    // 配速类型
    speed: 'pace',
    enhanced_speed: 'pace',
    avg_speed: 'pace',
    max_speed: 'pace',
    // IQ字段速度变体
    dr_speed: 'pace',
    dr_avg_speed: 'pace',
    dr_max_speed: 'pace',
    dr_lap_avg_speed: 'pace',
    dr_s_avg_speed: 'pace',
    // 心率类型
    heart_rate: 'heart_rate',
    avg_heart_rate: 'heart_rate',
    max_heart_rate: 'heart_rate',
    // 步频类型
    cadence: 'cadence',
    avg_cadence: 'cadence',
    max_cadence: 'cadence',
    // 功率类型
    power: 'power',
    avg_power: 'power',
    max_power: 'power',
    // 海拔类型
    altitude: 'altitude',
    enhanced_altitude: 'altitude',
    total_ascent: 'altitude',
    total_descent: 'altitude',
    // 步幅类型
    step_length: 'step_length',
    avg_step_length: 'step_length',
    stride_length: 'step_length',
    // 触地时间类型
    stance_time: 'ground_contact',
    avg_stance_time: 'ground_contact',
    gct: 'ground_contact',
    // 触地平衡类型
    stance_time_balance: 'stance_balance',
    // 腾空时间类型
    air_time: 'air_time',
    // 垂直振幅类型
    vertical_oscillation: 'vertical_oscillation',
    avg_vertical_oscillation: 'vertical_oscillation',
    v_osc: 'vertical_oscillation',
    // 其他
    grade: 'grade',
    temperature: 'temperature',
    avg_temperature: 'temperature',
    v_pif: 'v_pif',
    bias: 'bias',
    distance: 'distance',
    total_distance: 'distance',
    total_calories: 'calories'
};

// ==================== 字段分组配置 ====================

/**
 * 统一字段分组配置（趋势图和单圈表格共用）
 * 按语义对字段进行分组，提高用户查找效率
 */
const FIELD_GROUPS = {
    // 标准字段分组
    standard: {
        basic: {
            title: '基础数据',
            fields: ['elapsed_time', 'distance']
        },
        pace: {
            title: '配速',
            fields: ['speed', 'avg_speed', 'max_speed']
        },
        heartRate: {
            title: '心率',
            fields: ['heart_rate', 'avg_heart_rate', 'max_heart_rate']
        },
        cadence: {
            title: '步频',
            fields: ['cadence', 'avg_cadence', 'max_cadence']
        },
        power: {
            title: '功率',
            fields: ['power', 'avg_power', 'max_power']
        },
        elevation: {
            title: '海拔/爬升',
            fields: ['altitude', 'total_ascent', 'total_descent']
        },
        environment: {
            title: '环境',
            fields: ['temperature', 'grade']
        },
        dynamics: {
            title: '跑步动态',
            fields: ['vertical_oscillation', 'avg_vertical_oscillation', 
                     'stance_time', 'avg_stance_time', 
                     'step_length', 'avg_step_length',
                     'stance_time_balance', 'vertical_ratio']
        }
    },
    // IQ字段分组
    iq: {
        dragonPower: {
            title: '龙豆-功率',
            fields: ['dr_vertical_power', 'dr_propulsive_power', 
                     'dr_slope_power', 'dr_total_power']
        },
        dragonImpact: {
            title: '龙豆-冲击力',
            fields: ['dr_v_pif', 'dr_h_pif', 'dr_v_ilr', 'dr_h_ilr',
                     'dr_body_x_pif', 'dr_body_y_pif', 'dr_body_z_pif']
        },
        dragonDynamics: {
            title: '龙豆-跑步动态',
            fields: ['dr_gct', 'dr_air_time', 'dr_v_osc', 'dr_vertical_ratio',
                     'dr_stride', 'dr_cadence', 'dr_lss']
        },
        dragonOther: {
            title: '龙豆-其他',
            fields: ['dr_timestamp', 'dr_distance', 'dr_speed', 'dr_ssl', 
                     'dr_ssl_percent']
        },
        imported: {
            title: '导入数据',
            fieldPattern: /^imported_/  // 动态匹配imported_*字段
        },
        uncategorized: {
            title: '未分类IQ字段',
            fields: []  // 运行时动态填充
        }
    }
};

/**
 * 单圈专用字段分组（扩展标准分组）
 */
const LAP_FIELD_GROUPS = {
    standard: {
        ...FIELD_GROUPS.standard,
        basic: {
            title: '基础信息',
            fields: ['lap_number', 'start_time', 'total_elapsed_time', 'total_distance']
        },
        calories: {
            title: '热量',
            fields: ['total_calories']
        }
    },
    iq: FIELD_GROUPS.iq  // 复用IQ分组配置
};

// 获取字段的单位类型
function getFieldUnitType(field) {
    const fieldKey = field.startsWith('iq_') ? field.substring(3) : field;
    if (fieldKey === 'imported_hr' || (fieldKey.startsWith('imported_') && fieldKey.endsWith('_hr'))) {
        return 'heart_rate';
    }
    return FIELD_UNIT_TYPES[fieldKey] || fieldKey;
}

// 速度(m/s)转配速(min/km)，返回数值（分钟）
function speedToPaceValue(speedMs) {
    if (!speedMs || speedMs <= 0) return null;
    return 1000 / 60 / speedMs; // min/km
}

// 配速数值转显示字符串
function paceValueToString(paceMin) {
    if (!paceMin || paceMin <= 0 || paceMin > 30) return '--';
    const mins = Math.floor(paceMin);
    const secs = Math.round((paceMin - mins) * 60);
    return `${mins}'${secs.toString().padStart(2, '0')}"` ;
}

// 格式化时间轴（秒 -> mm:ss）
function formatTimeAxis(seconds) {
    if (seconds == null) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// 高对比度颜色池 - 确保相邻颜色有明显色差
const COLOR_PALETTE = [
    '#e74c3c',  // 红色
    '#3498db',  // 蓝色
    '#2ecc71',  // 绿色
    '#f39c12',  // 橙色
    '#9b59b6',  // 紫色
    '#1abc9c',  // 青色
    '#e67e22',  // 深橙色
    '#34495e',  // 深灰蓝
    '#c0392b',  // 深红色
    '#2980b9',  // 深蓝色
    '#27ae60',  // 深绿色
    '#8e44ad',  // 深紫色
    '#d35400',  // 棕橙色
    '#16a085',  // 深青色
    '#f1c40f',  // 黄色
    '#7f8c8d'   // 灰色
];

// ==================== 公共工具函数 ====================

// 统一颜色分配函数
function getTraceColor(index) {
    return COLOR_PALETTE[index % COLOR_PALETTE.length];
}

// 获取字段颜色 - 基于索引分配，确保每条曲线颜色不同（向后兼容）
function getFieldColor(field, index) {
    return getTraceColor(index);
}

// 对比视图颜色 - 使用相同的COLOR_PALETTE
const COMPARE_COLORS = COLOR_PALETTE;

// Plotly配置工厂函数
function createPlotlyConfig(filename) {
    return {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        displaylogo: false,
        toImageButtonOptions: {
            format: 'png',
            filename: filename,
            height: 800,
            width: 1200,
            scale: 2
        }
    };
}

// Y轴配置函数
function createYAxisConfig(title, color, isPaceField, side = null) {
    const config = {
        title: title,
        titlefont: { color: color },
        gridcolor: '#ecf0f1',
        zeroline: false,
        autorange: isPaceField ? 'reversed' : true
    };
    
    if (side) {
        config.side = side;
        config.overlaying = 'y';
    }
    
    return config;
}

// 字段分类函数 - 分离标准字段和IQ字段
function separateFieldTypes(allFields) {
    const standardFields = [];
    const iqFields = [];
    
    allFields.forEach(field => {
        // IQ字段判断规则：
        // 1. 有iq_或dr_前缀的字段
        // 2. 在IQ_FIELD_LABELS配置中定义的字段（无前缀的旧版IQ字段）
        const fieldKey = field.replace('iq_', '').replace('dr_', '');
        if (field.startsWith('iq_') || field.startsWith('dr_') || IQ_FIELD_LABELS[fieldKey]) {
            iqFields.push(field);
        } else {
            standardFields.push(field);
        }
    });
    
    return {
        standardFields: standardFields.sort(),
        iqFields: iqFields.sort()
    };
}

// 过滤特殊字段（时间、GPS坐标）
function shouldSkipField(field) {
    const skipFields = ['elapsed_time', 'timestamp', 'position_lat', 'position_long'];
    return skipFields.includes(field);
}

// 获取活动字段颜色 - 活动分组，字段使用同组内的颜色变化
// activityIndex: 活动索引, fieldIndex: 该活动内的字段索引, totalFields: 该活动的总字段数
function getActivityFieldColor(activityIndex, fieldIndex, totalFields) {
    const baseColor = COLOR_PALETTE[activityIndex % COLOR_PALETTE.length];
    
    // 如果只有一个字段，直接返回基础颜色
    if (totalFields === 1) {
        return baseColor;
    }
    
    // 解析基础颜色的RGB值
    const hex = baseColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
    // 转换为HSL
    const rNorm = r / 255;
    const gNorm = g / 255;
    const bNorm = b / 255;
    const max = Math.max(rNorm, gNorm, bNorm);
    const min = Math.min(rNorm, gNorm, bNorm);
    const l = (max + min) / 2;
    
    let h, s;
    if (max === min) {
        h = s = 0;
    } else {
        const d = max - min;
        s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
        switch (max) {
            case rNorm: h = ((gNorm - bNorm) / d + (gNorm < bNorm ? 6 : 0)) / 6; break;
            case gNorm: h = ((bNorm - rNorm) / d + 2) / 6; break;
            case bNorm: h = ((rNorm - gNorm) / d + 4) / 6; break;
        }
    }
    
    // 调整亮度：fieldIndex=0最亮，最后一个最暗
    // 亮度范围：从 l+0.15 到 l-0.15
    const lightnessRange = 0.3;
    const lightnessStep = totalFields > 1 ? lightnessRange / (totalFields - 1) : 0;
    const newL = Math.max(0.2, Math.min(0.8, l + lightnessRange / 2 - fieldIndex * lightnessStep));
    
    // 转换回RGB
    function hslToRgb(h, s, l) {
        let r, g, b;
        if (s === 0) {
            r = g = b = l;
        } else {
            const hue2rgb = (p, q, t) => {
                if (t < 0) t += 1;
                if (t > 1) t -= 1;
                if (t < 1/6) return p + (q - p) * 6 * t;
                if (t < 1/2) return q;
                if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
                return p;
            };
            const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
            const p = 2 * l - q;
            r = hue2rgb(p, q, h + 1/3);
            g = hue2rgb(p, q, h);
            b = hue2rgb(p, q, h - 1/3);
        }
        return [Math.round(r * 255), Math.round(g * 255), Math.round(b * 255)];
    }
    
    const [newR, newG, newB] = hslToRgb(h, s, newL);
    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`;
}

// X轴模式状态: 'time' 或 'distance'
let xAxisMode = 'time';

// 格式化距离轴（米 -> km）
function formatDistanceAxis(meters) {
    if (meters == null) return '';
    return (meters / 1000).toFixed(2);
}

// 初始化X轴切换按钮
function initXAxisToggle() {
    const timeBtn = document.getElementById('xAxisTime');
    const distBtn = document.getElementById('xAxisDist');
    
    if (!timeBtn || !distBtn) return;
    
    // 重置为默认状态
    xAxisMode = 'time';
    timeBtn.className = 'btn btn-sm btn-primary';
    distBtn.className = 'btn btn-sm btn-secondary';
    
    // 移除旧的事件监听器，避免重复绑定
    const newTimeBtn = timeBtn.cloneNode(true);
    const newDistBtn = distBtn.cloneNode(true);
    timeBtn.parentNode.replaceChild(newTimeBtn, timeBtn);
    distBtn.parentNode.replaceChild(newDistBtn, distBtn);
    
    newTimeBtn.addEventListener('click', () => {
        if (xAxisMode !== 'time') {
            xAxisMode = 'time';
            newTimeBtn.className = 'btn btn-sm btn-primary';
            newDistBtn.className = 'btn btn-sm btn-secondary';
            refreshTrendChart();
        }
    });
    
    newDistBtn.addEventListener('click', () => {
        if (xAxisMode !== 'distance') {
            xAxisMode = 'distance';
            newTimeBtn.className = 'btn btn-sm btn-secondary';
            newDistBtn.className = 'btn btn-sm btn-primary';
            refreshTrendChart();
        }
    });
}

// 刷新趋势图（使用当前选中的字段）
function refreshTrendChart() {
    const container = document.getElementById('fieldCheckboxes');
    if (!container) return;
    
    const selectedFields = Array.from(container.querySelectorAll('.field-checkbox:checked'))
        .map(cb => cb.value);
    
    if (state.currentActivity && selectedFields.length > 0) {
        updateTrendChart(state.currentActivity, selectedFields);
    }
}

// ==================== 统一字段选择器 ====================

/**
 * 根据分组配置对字段进行分组
 * @param {Array} fields - 字段列表
 * @param {Object} groupsConfig - 分组配置对象
 * @param {boolean} isIqField - 是否为IQ字段
 * @returns {Object} 分组结果 {groupKey: [fields]}
 */
function groupFieldsByConfig(fields, groupsConfig, isIqField = false) {
    const grouped = {};
    const uncategorized = [];
    
    // 遍历每个字段，找到所属分组
    fields.forEach(field => {
        const fieldKey = field.replace('iq_', '');
        let assigned = false;
        
        // 遍历分组配置查找匹配
        for (const [groupKey, groupConfig] of Object.entries(groupsConfig)) {
            // 检查字段是否在分组的fields数组中
            if (groupConfig.fields && groupConfig.fields.includes(fieldKey)) {
                if (!grouped[groupKey]) {
                    grouped[groupKey] = { ...groupConfig, fields: [] };
                }
                grouped[groupKey].fields.push(field);
                assigned = true;
                break;
            }
            
            // 检查是否匹配fieldPattern（如imported_*）
            if (groupConfig.fieldPattern && groupConfig.fieldPattern.test(fieldKey)) {
                if (!grouped[groupKey]) {
                    grouped[groupKey] = { ...groupConfig, fields: [] };
                }
                grouped[groupKey].fields.push(field);
                assigned = true;
                break;
            }
        }
        
        // 未分类的字段放入uncategorized
        if (!assigned) {
            uncategorized.push(field);
        }
    });
    
    // 如果有未分类字段，添加到uncategorized组
    if (uncategorized.length > 0 && isIqField) {
        grouped['uncategorized'] = {
            title: '未分类IQ字段',
            fields: uncategorized
        };
    }
    
    return grouped;
}

/**
 * 渲染字段选择器（v1.8.0: 卡片布局 + 搜索过滤 + 整体折叠）
 * @param {Object} options - 配置对象
 * @param {string} options.mode - 'single' | 'compare'
 * @param {Array} options.standardFields - 标准字段列表
 * @param {Array} options.iqFields - IQ字段列表
 * @param {Object} options.fieldGroups - 字段分组配置对象（可选）
 * @param {string} options.selectionType - 'checkbox' | 'radio'
 * @param {Array} options.defaultSelected - 默认选中字段
 * @param {Function} options.onChange - 选择变化回调
 * @param {string} options.containerId - 容器ID
 */
function renderUnifiedFieldSelector(options) {
    const {
        mode,
        standardFields,
        iqFields,
        fieldGroups,
        selectionType,
        defaultSelected = [],
        onChange,
        containerId
    } = options;
    
    const container = document.getElementById(containerId);
    if (!container) return;
    
    let html = '';
    
    // 如果提供了fieldGroups配置，使用卡片布局
    if (fieldGroups) {
        // 渲染标准字段分组卡片
        if (standardFields && standardFields.length > 0 && fieldGroups.standard) {
            const standardGroups = groupFieldsByConfig(standardFields, fieldGroups.standard, false);
            
            for (const [groupKey, groupData] of Object.entries(standardGroups)) {
                if (!groupData.fields || groupData.fields.length === 0) continue;
                
                const icon = getFieldGroupIcon(groupKey);
                html += `
                    <div class="field-group-card expanded" data-group="${groupKey}">
                        <div class="field-group-card__header">
                            <span class="field-group-card__icon">${icon}</span>
                            <span class="field-group-card__title">${groupData.title}</span>
                            <span class="field-group-card__toggle">▶</span>
                        </div>
                        <div class="field-group-card__content">
                `;
                
                groupData.fields.forEach(field => {
                    if (shouldSkipField(field)) return;
                    
                    const label = FIELD_LABELS[field] || field;
                    const isDefault = defaultSelected.includes(field);
                    const checked = isDefault ? 'checked' : '';
                    
                    if (selectionType === 'checkbox') {
                        html += `
                            <label>
                                <input type="checkbox" class="field-checkbox" value="${field}" ${checked}>
                                <span>${label}</span>
                            </label>
                        `;
                    } else {
                        html += `
                            <label>
                                <input type="radio" name="compareField" value="${field}" ${checked}>
                                <span>${label}</span>
                            </label>
                        `;
                    }
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
        
        // 渲染IQ字段分组卡片
        if (iqFields && iqFields.length > 0 && fieldGroups.iq) {
            const iqGroups = groupFieldsByConfig(iqFields, fieldGroups.iq, true);
            
            for (const [groupKey, groupData] of Object.entries(iqGroups)) {
                if (!groupData.fields || groupData.fields.length === 0) continue;
                
                const icon = getFieldGroupIcon(groupKey);
                html += `
                    <div class="field-group-card expanded" data-group="iq_${groupKey}">
                        <div class="field-group-card__header">
                            <span class="field-group-card__icon">${icon}</span>
                            <span class="field-group-card__title">${groupData.title}</span>
                            <span class="field-group-card__toggle">▶</span>
                        </div>
                        <div class="field-group-card__content">
                `;
                
                groupData.fields.forEach(field => {
                    const fieldKey = field.replace('iq_', '');
                    const displayName = getFieldLabel(fieldKey, true);
                    const isDefault = defaultSelected.includes(field);
                    const checked = isDefault ? 'checked' : '';
                    
                    if (selectionType === 'checkbox') {
                        html += `
                            <label>
                                <input type="checkbox" class="field-checkbox" value="${field}" ${checked}>
                                <span>${displayName}</span>
                            </label>
                        `;
                    } else {
                        html += `
                            <label>
                                <input type="radio" name="compareField" value="${field}" ${checked}>
                                <span>${displayName}</span>
                            </label>
                        `;
                    }
                });
                
                html += `
                        </div>
                    </div>
                `;
            }
        }
    } else {
        // 向后兼容：无分组配置时使用旧的简单分组
        // 渲染标准字段分组
        if (standardFields && standardFields.length > 0) {
            html += '<div class="field-group">';
            html += '<div class="field-group-title">标准字段</div>';
            
            standardFields.forEach(field => {
                if (shouldSkipField(field)) return;
                
                const label = FIELD_LABELS[field] || field;
                const isDefault = defaultSelected.includes(field);
                const checked = isDefault ? 'checked' : '';
                
                if (selectionType === 'checkbox') {
                    html += `
                        <label>
                            <input type="checkbox" class="field-checkbox" value="${field}" ${checked}>
                            <span>${label}</span>
                        </label>
                    `;
                } else {
                    html += `
                        <label class="field-checkbox-label">
                            <input type="radio" name="compareField" value="${field}" ${checked}>
                            <span>${label}</span>
                        </label>
                    `;
                }
            });
            
            html += '</div>';
        }
        
        // 渲染IQ字段分组
        if (iqFields && iqFields.length > 0) {
            html += '<div class="field-group">';
            html += '<div class="field-group-title">IQ扩展字段 (龙豆)</div>';
            
            iqFields.forEach(field => {
                const fieldKey = field.replace('iq_', '');
                const displayName = getFieldLabel(fieldKey, true);
                const isDefault = defaultSelected.includes(field);
                const checked = isDefault ? 'checked' : '';
                
                if (selectionType === 'checkbox') {
                    html += `
                        <label>
                            <input type="checkbox" class="field-checkbox" value="${field}" ${checked}>
                            <span>${displayName}</span>
                        </label>
                    `;
                } else {
                    html += `
                        <label class="field-checkbox-label">
                            <input type="radio" name="compareField" value="${field}" ${checked}>
                            <span>${displayName}</span>
                        </label>
                    `;
                }
            });
            
            html += '</div>';
        }
    }
    
    container.innerHTML = html;
    
    // v1.8.0: 绑定卡片展开/折叠事件
    container.querySelectorAll('.field-group-card__header').forEach(header => {
        header.addEventListener('click', () => {
            const card = header.closest('.field-group-card');
            card.classList.toggle('expanded');
            
            // 保存展开状态到localStorage
            const groupKey = card.getAttribute('data-group');
            try {
                const isExpanded = card.classList.contains('expanded');
                localStorage.setItem(`field_group_expanded_${groupKey}`, isExpanded);
            } catch (e) {
                console.warn('Failed to save group state:', e);
            }
        });
    });
    
    // 绑定字段选择事件监听器
    if (selectionType === 'checkbox') {
        container.querySelectorAll('.field-checkbox').forEach(cb => {
            cb.addEventListener('change', onChange);
        });
    } else {
        container.querySelectorAll('input[type="radio"]').forEach(radio => {
            radio.addEventListener('change', onChange);
        });
    }
}

// ==================== 单活动字段选择器（向后兼容）====================
function renderFieldSelector(standardFields, iqFields) {
    // 给IQ字段加上iq_前缀，与多活动对比保持一致
    const prefixedIqFields = iqFields ? iqFields.map(field => 'iq_' + field) : [];
    
    // 从localStorage加载保存的字段选择，如无则使用默认值
    const defaultSelected = loadFieldSelection('trend_selected_fields', ['heart_rate', 'cadence']);
    
    renderUnifiedFieldSelector({
        mode: 'single',
        standardFields: standardFields,
        iqFields: prefixedIqFields,
        fieldGroups: FIELD_GROUPS,  // 使用分组配置
        selectionType: 'checkbox',
        defaultSelected: defaultSelected,
        onChange: () => {
            const container = document.getElementById('fieldCheckboxes');
            const selectedFields = Array.from(container.querySelectorAll('.field-checkbox:checked'))
                .map(cb => cb.value);
            
            // 保存字段选择到localStorage
            saveFieldSelection('trend_selected_fields', selectedFields);
            
            // 更新趋势图
            updateTrendChart(state.currentActivity, selectedFields);
        },
        containerId: 'fieldCheckboxes'
    });
}

// ==================== 更新趋势图 ====================
function updateTrendChart(activity, selectedFields) {
    if (!activity || !activity.records || activity.records.length === 0) {
        document.getElementById('trendChart').innerHTML = '<p class="text-center text-muted">无数据</p>';
        return;
    }
    
    const records = activity.records;
    const traces = [];
    
    // 根据X轴模式选择数据源
    const useDistance = xAxisMode === 'distance';
    
    // 按单位类型分组，确定Y轴分配
    const unitTypeToAxisIndex = new Map();
    let axisCounter = 0;
    
    // 预处理：为每个字段分配Y轴索引
    const fieldAxisInfo = selectedFields.map(field => {
        const unitType = getFieldUnitType(field);
        if (!unitTypeToAxisIndex.has(unitType)) {
            unitTypeToAxisIndex.set(unitType, axisCounter);
            axisCounter++;
        }
        return {
            field,
            unitType,
            axisIndex: unitTypeToAxisIndex.get(unitType)
        };
    });
    
    // 为每个选中的字段创建一个trace
    selectedFields.forEach((field, index) => {
        const isIqField = field.startsWith('iq_');
        const fieldKey = isIqField ? field.substring(3) : field;
        const isPaceField = PACE_FIELDS.includes(fieldKey) || PACE_FIELDS.includes(field);
        const axisIndex = fieldAxisInfo[index].axisIndex;
        
        // X轴数据：时间或距离
        const xData = useDistance 
            ? records.map(r => r.distance || 0)
            : records.map(r => r.elapsed_time || 0);
            
        const yData = records.map(r => {
            let val;
            if (isIqField) {
                val = r.iq_fields ? r.iq_fields[fieldKey] : null;
            } else {
                val = r[fieldKey];
            }
            // 如果是速度字段，转换为配速
            if (isPaceField && val) {
                return speedToPaceValue(val);
            }
            return val;
        });
        
        // X轴格式化标签
        const xLabels = useDistance 
            ? xData.map(d => formatDistanceAxis(d) + ' km')
            : xData.map(t => formatTimeAxis(t));
        
        // 过滤掉null值
        const validData = xData.map((x, i) => ({ x, xLabel: xLabels[i], y: yData[i] }))
            .filter(d => d.y !== null && d.y !== undefined);
        
        if (validData.length === 0) return;
        
        const color = getFieldColor(field, index);
        const label = getFieldLabel(field, isIqField);
        
        // 构建hover文本
        const xAxisLabel = useDistance ? '距离' : '时间';
        let hoverTemplate;
        if (isPaceField) {
            // 配速字段特殊处理hover显示
            hoverTemplate = validData.map(d => {
                const paceStr = paceValueToString(d.y);
                return `${xAxisLabel}: ${d.xLabel}<br>${label}: ${paceStr}`;
            });
        }
        
        const trace = {
            x: validData.map(d => d.x),
            y: validData.map(d => d.y),
            name: label,
            type: 'scatter',
            mode: 'lines',
            line: {
                color: color,
                width: 2
            },
            yaxis: axisIndex === 0 ? 'y' : `y${axisIndex + 1}`
        };
        
        if (isPaceField) {
            trace.text = hoverTemplate;
            trace.hoverinfo = 'text';
        } else {
            trace.customdata = validData.map(d => d.xLabel);
            trace.hovertemplate = `${xAxisLabel}: %{customdata}<br>${label}: %{y:.2f}<extra></extra>`;
        }
        
        traces.push(trace);
    });
    
    if (traces.length === 0) {
        document.getElementById('trendChart').innerHTML = '<p class="text-center text-muted">请选择至少一个字段</p>';
        return;
    }
    
    // 生成X轴刻度值和标签
    const maxX = Math.max(...traces[0].x);
    let tickVals = [];
    let tickTexts = [];
    
    if (useDistance) {
        // 距离模式：每0.5km或1km一个刻度
        const tickInterval = maxX > 10000 ? 2000 : (maxX > 5000 ? 1000 : 500);
        for (let d = 0; d <= maxX; d += tickInterval) {
            tickVals.push(d);
            tickTexts.push((d / 1000).toFixed(1));
        }
    } else {
        // 时间模式
        const tickInterval = maxX > 3600 ? 600 : (maxX > 600 ? 60 : 30);
        for (let t = 0; t <= maxX; t += tickInterval) {
            tickVals.push(t);
            tickTexts.push(formatTimeAxis(t));
        }
    }
    
    // 布局配置
    const layout = {
        title: {
            text: '运动数据趋势',
            font: { size: 18, color: '#2c3e50' }
        },
        xaxis: {
            title: useDistance ? '距离 (km)' : '运动时间',
            gridcolor: '#ecf0f1',
            zeroline: false,
            tickmode: 'array',
            tickvals: tickVals,
            ticktext: tickTexts
        },
        yaxis: (() => {
            // 找到所有使用主Y轴(axisIndex=0)的trace
            const mainAxisTraces = traces.filter(t => t.yaxis === 'y');
            const mainAxisTitle = mainAxisTraces.length > 1 
                ? mainAxisTraces.map(t => t.name).join(' / ')
                : (mainAxisTraces[0]?.name || '');
            
            // 检查主轴是否为配速类型
            const firstMainField = fieldAxisInfo.find(info => info.axisIndex === 0);
            const isMainAxisPace = firstMainField && PACE_FIELDS.includes(
                firstMainField.field.startsWith('iq_') 
                    ? firstMainField.field.substring(3) 
                    : firstMainField.field
            );
            
            return {
                title: mainAxisTitle,
                gridcolor: '#ecf0f1',
                zeroline: false,
                titlefont: { color: mainAxisTraces[0]?.line.color || '#333' },
                autorange: isMainAxisPace ? 'reversed' : true
            };
        })(),
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2,
            x: 0.5,
            xanchor: 'center'
        },
        margin: { l: 60, r: 60, t: 60, b: 80 },
        height: 500,
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff'
    };
    
    // 如果有多个不同单位类型，添加额外的Y轴
    const uniqueAxisCount = unitTypeToAxisIndex.size;
    if (uniqueAxisCount > 1) {
        // 为每个额外的Y轴找到该轴的第一个trace作为代表
        for (let axisIdx = 1; axisIdx < uniqueAxisCount; axisIdx++) {
            // 找到使用这个轴的第一个trace
            const representativeTrace = traces.find(t => {
                const yaxis = t.yaxis;
                return yaxis === `y${axisIdx + 1}`;
            });
            
            if (representativeTrace) {
                // 找到使用这个轴的所有trace的名称，合并作为标题
                const axisTraces = traces.filter(t => t.yaxis === `y${axisIdx + 1}`);
                const axisTitle = axisTraces.length > 1 
                    ? axisTraces.map(t => t.name).join(' / ')
                    : representativeTrace.name;
                
                // 检查该轴是否为配速类型
                const firstFieldInfo = fieldAxisInfo.find(info => info.axisIndex === axisIdx);
                const isPaceAxis = firstFieldInfo && PACE_FIELDS.includes(
                    firstFieldInfo.field.startsWith('iq_') 
                        ? firstFieldInfo.field.substring(3) 
                        : firstFieldInfo.field
                );
                
                layout[`yaxis${axisIdx + 1}`] = {
                    title: axisTitle,
                    overlaying: 'y',
                    side: axisIdx % 2 === 0 ? 'left' : 'right',
                    position: axisIdx % 2 === 0 ? 0.05 * Math.floor(axisIdx / 2) : 1 - 0.05 * Math.floor(axisIdx / 2),
                    titlefont: { color: representativeTrace.line.color },
                    tickfont: { color: representativeTrace.line.color },
                    autorange: isPaceAxis ? 'reversed' : true
                };
            }
        }
        
        // 调整边距
        layout.margin.l = 60 + 50 * Math.floor((uniqueAxisCount - 1) / 2);
        layout.margin.r = 60 + 50 * Math.floor(uniqueAxisCount / 2);
    }
    
    // 配置选项
    const config = createPlotlyConfig(`${activity.name}_trend`);
    
    Plotly.newPlot('trendChart', traces, layout, config);
}

// ==================== 渲染每圈数据表格 ====================
/**
 * 渲染单圈数据表格（动态列）
 * @param {Array} laps - 单圈数据数组
 * @param {Array} selectedFields - 选中要显示的字段
 */
function renderLapsTable(laps, selectedFields) {
    const tbody = document.getElementById('lapsTableBody');
    const thead = document.getElementById('lapsTableHead');
    
    if (!laps || laps.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">无每圈数据</td></tr>';
        thead.innerHTML = '';
        return;
    }
    
    if (!selectedFields || selectedFields.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="text-center">请选择要显示的字段</td></tr>';
        thead.innerHTML = '';
        return;
    }
    
    // 动态生成表头
    const headerCells = selectedFields.map(field => {
        const isIqField = field.startsWith('iq_');
        const label = isIqField ? 
            getFieldLabel(field.replace('iq_', ''), true) :
            (FIELD_LABELS[field] || field);
        return `<th>${label}</th>`;
    }).join('');
    
    thead.innerHTML = `<tr>${headerCells}</tr>`;
    
    // 动态生成表体
    const baseTime = laps[0]?.start_time;
    const rows = laps.map((lap, index) => {
        const cells = selectedFields.map(field => {
            let value;
            
            // 获取字段值
            if (field.startsWith('iq_')) {
                // IQ字段从iq_fields中提取
                const rawKey = field.replace('iq_', '');
                value = lap.iq_fields?.[rawKey];
            } else {
                // 标准字段直接访问
                value = lap[field];
            }
            
            // 格式化值
            let formatted = '--';
            if (value != null) {
                if (field === 'start_time') {
                    formatted = formatRelativeTime(value, baseTime);
                } else if (field === 'total_elapsed_time') {
                    formatted = formatDuration(value);
                } else if (field === 'total_distance') {
                    formatted = (value / 1000).toFixed(2) + ' km';
                } else if (field === 'avg_speed' || field === 'max_speed' || field === 'iq_dr_speed') {
                    // v1.8.0: 使用新的速度→配速转换函数
                    formatted = speed_to_pace(value);
                } else if (field === 'total_ascent' || field === 'total_descent') {
                    formatted = value.toFixed(0) + 'm';
                } else if (typeof value === 'number') {
                    // v1.8.0: 优先使用formatFieldValue处理IQ字段
                    const fieldKey = field.startsWith('iq_') ? field.replace('iq_', '') : field;
                    if (field.startsWith('iq_') && window.deviceFieldsMap && window.deviceFieldsMap.has(fieldKey)) {
                        formatted = formatFieldValue(fieldKey, value);
                    } else {
                        // 数值类型保留合适精度
                        formatted = value % 1 === 0 ? value.toString() : value.toFixed(2);
                    }
                } else {
                    formatted = value;
                }
            }
            
            return `<td>${formatted}</td>`;
        }).join('');
        
        return `<tr>${cells}</tr>`;
    }).join('');
    
    tbody.innerHTML = rows;
}

// ==================== 多活动对比图表 ====================
// 防抖定时器
let compareDebounceTimer = null;

// 获取选中的字段（单选模式）
function getSelectedCompareFields() {
    const radio = document.querySelector('#compareFieldCheckboxes input[type="radio"]:checked');
    return radio ? [radio.value] : [];
}

// 加载字段选择器 - 获取所有选中活动的字段并集（改进版：分组显示）
async function loadCompareFieldSelector() {
    const container = document.getElementById('compareFieldCheckboxes');
    container.innerHTML = '<p class="text-muted">正在加载字段...</p>';
    
    try {
        // 获取所有选中活动的元数据
        const activityIds = Array.from(state.selectedActivityIds);
        const metadataPromises = activityIds.map(id => 
            fetch(`${API_BASE}/activity/${id}`).then(r => r.json())
        );
        
        const activities = await Promise.all(metadataPromises);
        
        // 合并所有字段（并集）
        const allFieldsSet = new Set();
        const allIQFieldsSet = new Set();
        activities.forEach(activity => {
            if (activity.available_fields) {
                activity.available_fields.forEach(field => allFieldsSet.add(field));
            }
            if (activity.available_iq_fields) {
                activity.available_iq_fields.forEach(field => allIQFieldsSet.add('iq_' + field));
            }
        });
        
        const allFields = Array.from(allFieldsSet).concat(Array.from(allIQFieldsSet));
        
        if (allFields.length === 0) {
            container.innerHTML = '<p class="text-muted">没有可用的字段</p>';
            return;
        }
        
        // 分离标准字段和IQ字段
        const { standardFields, iqFields } = separateFieldTypes(allFields);
        
        // 确定默认选中的字段
        const defaultSelected = [];
        if (standardFields.includes('speed')) {
            defaultSelected.push('speed');
        } else if (standardFields.includes('enhanced_speed')) {
            defaultSelected.push('enhanced_speed');
        } else if (standardFields.length > 0) {
            defaultSelected.push(standardFields[0]);
        }
        
        // 使用统一字段选择器渲染（分组显示）
        renderUnifiedFieldSelector({
            mode: 'compare',
            standardFields: standardFields,
            iqFields: iqFields,
            selectionType: 'radio',
            defaultSelected: defaultSelected,
            onChange: () => triggerCompareChartUpdate(),
            containerId: 'compareFieldCheckboxes'
        });
        
        // 如果有默认选中的字段，触发图表更新
        if (getSelectedCompareFields().length > 0) {
            triggerCompareChartUpdate();
        }
        
    } catch (error) {
        console.error('Failed to load field selector:', error);
        container.innerHTML = '<p class="text-danger">加载字段失败</p>';
    }
}

// 触发图表更新（带防抖）
function triggerCompareChartUpdate() {
    if (compareDebounceTimer) {
        clearTimeout(compareDebounceTimer);
    }
    
    compareDebounceTimer = setTimeout(() => {
        updateCompareChart();
    }, 300);
}

// 更新对比图表 - 支持多字段
async function updateCompareChart() {
    const selectedFields = getSelectedCompareFields();
    const alignBy = document.querySelector('input[name="alignBy"]:checked').value;
    
    if (state.selectedActivityIds.size < 2) {
        document.getElementById('compareChart').innerHTML = '<p class="text-center text-muted">请至少选择2个活动</p>';
        return;
    }
    
    if (selectedFields.length === 0) {
        document.getElementById('compareChart').innerHTML = '<p class="text-center text-muted">请至少选择1个字段</p>';
        return;
    }
    
    showStatus('正在加载对比数据...');
    
    try {
        const response = await fetch(`${API_BASE}/compare`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                activity_ids: Array.from(state.selectedActivityIds),
                fields: selectedFields,
                align_by: alignBy
            })
        });
        
        const data = await response.json();
        renderCompareChart(data, selectedFields);
        
        showStatus('对比图表已更新', 'success');
    } catch (error) {
        console.error('Failed to load compare data:', error);
        showStatus('加载对比数据失败', 'error');
    }
}

// 格式化活动日期时间戳前缀：YYYYMMDD_FileID
function formatActivityPrefix(activity) {
    let datePrefix = '';
    let fileId = '';
    
    // 提取日期：从activity.date (ISO格式: 2025-12-08T11:52:42Z)
    if (activity.date) {
        const date = new Date(activity.date);
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        datePrefix = `${year}${month}${day}`;
    }
    
    // 提取文件ID：从activity.name (格式: 546564164_ACTIVITY)
    if (activity.name) {
        const match = activity.name.match(/^(\d+)/);
        if (match) {
            fileId = match[1];
        }
    }
    
    // 组合前缀
    if (datePrefix && fileId) {
        return `${datePrefix}_${fileId}`;
    } else if (datePrefix) {
        return datePrefix;
    } else if (fileId) {
        return fileId;
    }
    
    return activity.name || 'Unknown';
}

// 渲染对比图表 - 多活动 × 单字段对比
function renderCompareChart(data, fields) {
    const traces = [];
    const yAxisAssignments = {};
    let yAxisIndex = 1;
    
    // 单字段模式：只处理第一个字段（实际上fields数组应该只有一个元素）
    const field = fields[0];
    if (!field) {
        document.getElementById('compareChart').innerHTML = '<p class="text-center text-muted">请选择一个字段</p>';
        return;
    }
    
    const isIqField = field.startsWith('iq_');
    const fieldLabel = getFieldLabel(field, isIqField);
    const isPaceField = PACE_FIELDS.includes(field) || (isIqField && PACE_FIELDS.includes(field.substring(3)));
    const unitType = getFieldUnitType(field);
    
    // 为该字段分配Y轴
    yAxisAssignments[unitType] = 'y';
    
    // 遍历活动生成traces（每个活动一条曲线）
    data.activities.forEach((activity, activityIndex) => {
        // 生成活动前缀：日期_文件ID
        const activityPrefix = formatActivityPrefix(activity);
        
        // 获取颜色：每个活动使用不同颜色
        const color = COLOR_PALETTE[activityIndex % COLOR_PALETTE.length];
        
        // 获取数据，如果活动缺少该字段，数据为null
        let yData = activity.data.map(d => {
            const value = d[field];
            if (value === undefined || value === null) return null;
            // 配速字段转换
            if (isPaceField) {
                return speedToPaceValue(value);
            }
            return value;
        });
        
        // 曲线命名：日期_文件ID - 字段名
        const traceName = `${activityPrefix} - ${fieldLabel}`;
        
        const trace = {
            x: activity.data.map(d => d.x),
            y: yData,
            name: traceName,
            type: 'scatter',
            mode: 'lines',
            line: {
                color: color,
                width: 2
            },
            yaxis: 'y',
            connectgaps: false, // 缺失数据显示为间断
            hovertemplate: isPaceField 
                ? `${traceName}<br>%{x}<br>%{y:.2f} min/km<extra></extra>`
                : `${traceName}<br>%{x}<br>%{y:.2f}<extra></extra>`
        };
        
        traces.push(trace);
    });
    
    // 构建布局 - 单Y轴配置
    const isPaceType = unitType === 'pace';
    
    const layout = {
        title: {
            text: `多活动单字段对比分析 - ${fieldLabel}`,
            font: { size: 18, color: '#2c3e50' }
        },
        xaxis: {
            title: data.x_label,
            gridcolor: '#ecf0f1',
            zeroline: false
        },
        yaxis: {
            title: fieldLabel,
            gridcolor: '#ecf0f1',
            zeroline: false,
            autorange: isPaceType ? 'reversed' : true,
            tickformat: isPaceType ? '.2f' : undefined
        },
        hovermode: 'x unified',
        showlegend: true,
        legend: {
            orientation: 'v',
            y: 1,
            x: 1.02,
            xanchor: 'left'
        },
        margin: { l: 60, r: 200, t: 60, b: 60 },
        height: 600,
        plot_bgcolor: '#ffffff',
        paper_bgcolor: '#ffffff'
    };
    
    const config = createPlotlyConfig('activity_compare');
    
    Plotly.newPlot('compareChart', traces, layout, config);
}

// 渲染选中的活动列表（带颜色标记）
function renderSelectedActivitiesWithColors(activities) {
    const container = document.getElementById('selectedActivitiesList');
    
    if (activities.length === 0) {
        container.innerHTML = '<p class="text-muted">未选中任何活动</p>';
        return;
    }
    
    container.innerHTML = '<p><strong>选中的活动:</strong></p>' + 
        activities.map((activity, index) => {
            const color = COMPARE_COLORS[index % COMPARE_COLORS.length];
            return `
                <div class="activity-chip">
                    <span class="color-dot" style="background-color: ${color}"></span>
                    <span>${activity.name}</span>
                </div>
            `;
        }).join('');
}
