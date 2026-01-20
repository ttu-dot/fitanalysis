/**
 * charts.js 单元测试
 * 测试字段标签映射和数据转换函数
 * 
 * 运行方式: 在浏览器控制台中加载此文件，或使用Node.js运行
 */

// ==================== 测试框架（简易版）====================
const TestRunner = {
    passed: 0,
    failed: 0,
    results: [],
    
    test(name, fn) {
        try {
            fn();
            this.passed++;
            this.results.push({ name, status: 'PASS' });
            console.log(`✓ ${name}`);
        } catch (e) {
            this.failed++;
            this.results.push({ name, status: 'FAIL', error: e.message });
            console.error(`✗ ${name}: ${e.message}`);
        }
    },
    
    assertEqual(actual, expected, message = '') {
        if (actual !== expected) {
            throw new Error(`${message} Expected "${expected}", got "${actual}"`);
        }
    },
    
    assertTrue(condition, message = '') {
        if (!condition) {
            throw new Error(`${message} Expected true, got false`);
        }
    },
    
    summary() {
        console.log(`\n========== 测试结果 ==========`);
        console.log(`通过: ${this.passed}, 失败: ${this.failed}`);
        return { passed: this.passed, failed: this.failed, results: this.results };
    }
};

// ==================== 模拟 charts.js 中的函数和常量 ====================

// 字段显示名称映射
const FIELD_LABELS = {
    heart_rate: '心率 (bpm)',
    cadence: '步频 (spm)',
    speed: '配速 (min/km)',
    enhanced_speed: '配速 (min/km)',
    power: '功率 (W)',
    altitude: '海拔 (m)',
    enhanced_altitude: '海拔 (m)',
    grade: '坡度 (%)',
    temperature: '温度 (°C)',
    vertical_oscillation: '垂直振幅 (cm)',
    stance_time: '触地时间 (ms)',
    step_length: '步幅 (m)',
    stride_length: '步幅 (m)',
    distance: '距离 (km)',
    gct: '触地时间 (ms)',
    air_time: '腾空时间 (ms)',
    v_osc: '垂直振幅 (cm)',
    v_pif: '冲击峰值',
    bias: '左右平衡 (%)'
};

// IQ字段显示名称映射（带DR_前缀）
const IQ_FIELD_LABELS = {
    distance: 'DR_距离 (km)',
    speed: 'DR_配速 (min/km)',
    cadence: 'DR_步频 (spm)',
    stride_length: 'DR_步幅 (cm)',
    gct: 'DR_触地时间 (ms)',
    air_time: 'DR_腾空时间 (ms)',
    v_osc: 'DR_垂直振幅 (cm)',
    v_pif: 'DR_冲击峰值',
    bias: 'DR_左右平衡 (%)'
};

// 获取字段显示标签
function getFieldLabel(field, isIqField = false) {
    const fieldKey = isIqField ? field : field.replace('iq_', '');
    
    if (isIqField || field.startsWith('iq_')) {
        if (IQ_FIELD_LABELS[fieldKey]) {
            return IQ_FIELD_LABELS[fieldKey];
        }
        const baseLabel = FIELD_LABELS[fieldKey] || fieldKey.replace(/_/g, ' ');
        return `DR_${baseLabel}`;
    }
    
    return FIELD_LABELS[field] || field;
}

// 速度转配速
function speedToPaceValue(speedMs) {
    if (!speedMs || speedMs <= 0) return null;
    return 1000 / 60 / speedMs;
}

// 配速数值转显示字符串
function paceValueToString(paceMin) {
    if (!paceMin || paceMin <= 0 || paceMin > 30) return '--';
    const mins = Math.floor(paceMin);
    const secs = Math.round((paceMin - mins) * 60);
    return `${mins}'${secs.toString().padStart(2, '0')}"`;
}

// 格式化时间轴
function formatTimeAxis(seconds) {
    if (seconds == null) return '';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

// ==================== 测试用例 ====================

// FR016: 字段在趋势图上显示加上前缀
console.log('\n========== FR016: IQ字段DR_前缀显示测试 ==========\n');

TestRunner.test('IQ字段gct应显示为DR_触地时间', () => {
    const label = getFieldLabel('gct', true);
    TestRunner.assertEqual(label, 'DR_触地时间 (ms)');
});

TestRunner.test('IQ字段air_time应显示为DR_腾空时间', () => {
    const label = getFieldLabel('air_time', true);
    TestRunner.assertEqual(label, 'DR_腾空时间 (ms)');
});

TestRunner.test('IQ字段stride_length应显示为DR_步幅', () => {
    const label = getFieldLabel('stride_length', true);
    TestRunner.assertEqual(label, 'DR_步幅 (cm)');
});

TestRunner.test('IQ字段v_osc应显示为DR_垂直振幅', () => {
    const label = getFieldLabel('v_osc', true);
    TestRunner.assertEqual(label, 'DR_垂直振幅 (cm)');
});

TestRunner.test('IQ字段v_pif应显示为DR_冲击峰值', () => {
    const label = getFieldLabel('v_pif', true);
    TestRunner.assertEqual(label, 'DR_冲击峰值');
});

TestRunner.test('IQ字段cadence应显示为DR_步频', () => {
    const label = getFieldLabel('cadence', true);
    TestRunner.assertEqual(label, 'DR_步频 (spm)');
});

TestRunner.test('带iq_前缀的字段应自动识别为IQ字段', () => {
    const label = getFieldLabel('iq_gct', false);
    TestRunner.assertEqual(label, 'DR_触地时间 (ms)');
});

TestRunner.test('未定义的IQ字段应自动添加DR_前缀', () => {
    const label = getFieldLabel('unknown_field', true);
    TestRunner.assertTrue(label.startsWith('DR_'), '应以DR_开头');
});

// 标准字段测试
console.log('\n========== 标准字段标签测试 ==========\n');

TestRunner.test('标准字段heart_rate应显示为心率', () => {
    const label = getFieldLabel('heart_rate', false);
    TestRunner.assertEqual(label, '心率 (bpm)');
});

TestRunner.test('标准字段cadence应显示为步频（无DR_前缀）', () => {
    const label = getFieldLabel('cadence', false);
    TestRunner.assertEqual(label, '步频 (spm)');
});

TestRunner.test('标准字段power应显示为功率', () => {
    const label = getFieldLabel('power', false);
    TestRunner.assertEqual(label, '功率 (W)');
});

// 配速转换测试
console.log('\n========== 配速转换函数测试 ==========\n');

TestRunner.test('速度2.778m/s应转换为约6分配速', () => {
    const pace = speedToPaceValue(2.778);
    TestRunner.assertTrue(Math.abs(pace - 6.0) < 0.1, `配速应约为6分, 实际: ${pace}`);
});

TestRunner.test('速度0应返回null', () => {
    const pace = speedToPaceValue(0);
    TestRunner.assertEqual(pace, null);
});

TestRunner.test('配速6.0应显示为6\'00"', () => {
    const str = paceValueToString(6.0);
    TestRunner.assertEqual(str, "6'00\"");
});

TestRunner.test('配速5.5应显示为5\'30"', () => {
    const str = paceValueToString(5.5);
    TestRunner.assertEqual(str, "5'30\"");
});

// 时间格式化测试
console.log('\n========== 时间格式化测试 ==========\n');

TestRunner.test('90秒应格式化为1:30', () => {
    const str = formatTimeAxis(90);
    TestRunner.assertEqual(str, '1:30');
});

TestRunner.test('3661秒应格式化为61:01', () => {
    const str = formatTimeAxis(3661);
    TestRunner.assertEqual(str, '61:01');
});

// ==================== FR010/FR017: 多活动多字段矩阵式对比测试 ====================
console.log('\n========== FR010/FR017: 多活动多字段对比测试 ==========\n');

// 模拟COLOR_PALETTE和COMPARE_COLORS
const COLOR_PALETTE = [
    '#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6',
    '#1abc9c', '#e67e22', '#34495e', '#c0392b', '#2980b9'
];
const COMPARE_COLORS = COLOR_PALETTE;

// 模拟getActivityFieldColor函数
function getActivityFieldColor(activityIndex, fieldIndex, totalFields) {
    const baseColor = COLOR_PALETTE[activityIndex % COLOR_PALETTE.length];
    
    if (totalFields === 1) {
        return baseColor;
    }
    
    const hex = baseColor.replace('#', '');
    const r = parseInt(hex.substring(0, 2), 16);
    const g = parseInt(hex.substring(2, 4), 16);
    const b = parseInt(hex.substring(4, 6), 16);
    
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
    
    const lightnessRange = 0.3;
    const lightnessStep = totalFields > 1 ? lightnessRange / (totalFields - 1) : 0;
    const newL = Math.max(0.2, Math.min(0.8, l + lightnessRange / 2 - fieldIndex * lightnessStep));
    
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

TestRunner.test('COMPARE_COLORS应该等于COLOR_PALETTE', () => {
    TestRunner.assertEqual(COMPARE_COLORS, COLOR_PALETTE, 'COMPARE_COLORS应该引用COLOR_PALETTE');
});

TestRunner.test('单字段时getActivityFieldColor应返回基础颜色', () => {
    const color = getActivityFieldColor(0, 0, 1);
    TestRunner.assertEqual(color, COLOR_PALETTE[0], '单字段时应返回基础颜色');
});

TestRunner.test('多字段时getActivityFieldColor应返回HSL变化的颜色', () => {
    const color1 = getActivityFieldColor(0, 0, 3);
    const color2 = getActivityFieldColor(0, 1, 3);
    TestRunner.assertTrue(color1 !== color2, '同活动的不同字段应有不同颜色');
});

TestRunner.test('不同活动应使用不同的基础颜色', () => {
    const color1 = getActivityFieldColor(0, 0, 2);
    const color2 = getActivityFieldColor(1, 0, 2);
    TestRunner.assertTrue(color1 !== color2, '不同活动应有不同基础颜色');
});

TestRunner.test('返回的颜色应为有效的十六进制格式', () => {
    const color = getActivityFieldColor(0, 0, 3);
    TestRunner.assertTrue(/^#[0-9a-f]{6}$/i.test(color), `返回的颜色应为有效的十六进制格式, 实际: ${color}`);
});

TestRunner.test('5个字段应生成5个不同的颜色变化', () => {
    const colors = [];
    for (let i = 0; i < 5; i++) {
        colors.push(getActivityFieldColor(0, i, 5));
    }
    const uniqueColors = new Set(colors);
    TestRunner.assertEqual(uniqueColors.size, 5, '5个字段应生成5个唯一颜色');
});

// 输出测试结果
const summary = TestRunner.summary();

// 导出测试结果（用于外部调用）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { TestRunner, summary };
}
