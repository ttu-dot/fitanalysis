#!/usr/bin/env python3
"""
FIT Running Data Analyzer - Pre-Build Checklist
构建前检查清单 - 确保版本号一致性和关键文件完整性
"""
import sys
from pathlib import Path

def run_checks():
    """运行所有构建前检查"""
    print('=' * 60)
    print('v1.8.0+ 构建前检查清单')
    print('=' * 60)
    print()
    
    # 添加当前目录到路径
    sys.path.insert(0, str(Path.cwd()))
    
    # 导入配置
    try:
        from config import VERSION, HOST, PORT
    except ImportError as e:
        print(f'✗ 无法导入config.py: {e}')
        return False
    
    checks = []
    
    # ==================== 版本号检查 ====================
    print('【版本号检查】')
    
    # 1. config.py VERSION
    if VERSION:
        checks.append(('✓', f'config.py VERSION = {VERSION}'))
        current_version = VERSION
    else:
        checks.append(('✗', 'config.py VERSION 未定义'))
        return False
    
    # 2. fitanalysis.spec macOS版本号
    spec_file = Path('fitanalysis.spec')
    if spec_file.exists():
        spec_content = spec_file.read_text(encoding='utf-8')
        
        if f"'CFBundleShortVersionString': '{VERSION}'" in spec_content:
            checks.append(('✓', f'fitanalysis.spec CFBundleShortVersionString = {VERSION}'))
        else:
            checks.append(('✗', f'fitanalysis.spec CFBundleShortVersionString 不匹配'))
        
        if f"'CFBundleVersion': '{VERSION}'" in spec_content:
            checks.append(('✓', f'fitanalysis.spec CFBundleVersion = {VERSION}'))
        else:
            checks.append(('✗', f'fitanalysis.spec CFBundleVersion 不匹配'))
    else:
        checks.append(('✗', 'fitanalysis.spec 文件不存在'))
    
    # 3. RELEASE文档存在（可选，本地开发用）
    release_doc = Path(f'RELEASE_v{VERSION}.md')
    if release_doc.exists():
        checks.append(('✓', f'RELEASE_v{VERSION}.md 存在（本地）'))
    # 不检查RELEASE文档是否存在，因为这是内部文档
    
    print()
    
    # ==================== 配置检查 ====================
    print('【配置检查】')
    
    # 4. 端口配置
    if PORT == 8082:
        checks.append(('✓', f'config.py PORT = {PORT}'))
    else:
        checks.append(('✗', f'config.py PORT = {PORT} (应为8082)'))
    
    # 5. 主机配置
    if HOST in ['127.0.0.1', 'localhost']:
        checks.append(('✓', f'config.py HOST = {HOST}'))
    else:
        checks.append(('✗', f'config.py HOST = {HOST} (应为127.0.0.1)'))
    
    print()
    
    # ==================== 核心模块检查 ====================
    print('【核心模块检查】')
    
    backend_modules = [
        'backend/main.py',
        'backend/device_mappings.py',
        'backend/field_units.py',
        'backend/fit_parser.py',
        'backend/data_store.py',
        'backend/csv_exporter.py',
        'backend/models.py',
        'backend/hr_csv_merge.py',
    ]
    
    for module in backend_modules:
        if Path(module).exists():
            checks.append(('✓', f'{module} 存在'))
        else:
            checks.append(('✗', f'{module} 缺失'))
    
    # 6. 检查device_mappings可导入
    try:
        sys.path.insert(0, 'backend')
        from device_mappings import DeviceRegistry
        checks.append(('✓', 'backend/device_mappings.py 可导入'))
    except ImportError as e:
        checks.append(('✗', f'backend/device_mappings.py 导入失败: {e}'))
    
    print()
    
    # ==================== Frontend文件检查 ====================
    print('【Frontend文件检查】')
    
    frontend_files = [
        'frontend/index.html',
        'frontend/css/styles.css',
        'frontend/js/app.js',
        'frontend/js/charts.js',
        'frontend/js/export.js',
    ]
    
    for file in frontend_files:
        if Path(file).exists():
            checks.append(('✓', f'{file} 存在'))
        else:
            checks.append(('✗', f'{file} 缺失'))
    
    print()
    
    # ==================== 构建配置检查 ====================
    print('【构建配置检查】')
    
    # 7. fitanalysis.spec hiddenimports
    if spec_file.exists():
        required_imports = [
            'backend.device_mappings',
            'backend.field_units',
            'backend.fit_parser',
            'backend.data_store',
            'backend.csv_exporter',
        ]
        
        for imp in required_imports:
            if imp in spec_content:
                checks.append(('✓', f'fitanalysis.spec 包含 {imp}'))
            else:
                checks.append(('✗', f'fitanalysis.spec 缺少 {imp}'))
    
    # 8. 构建脚本存在
    build_files = [
        'build.py',
        'run.bat',
        'run.sh',
        'fitanalysis.spec',
    ]
    
    for file in build_files:
        if Path(file).exists():
            checks.append(('✓', f'{file} 存在'))
        else:
            checks.append(('✗', f'{file} 缺失'))
    
    print()
    
    # ==================== 文档检查 ====================
    print('【文档检查】')
    
    doc_files = [
        'README.md',
    ]
    
    for file in doc_files:
        if Path(file).exists():
            checks.append(('✓', f'{file} 存在'))
        else:
            checks.append(('✗', f'{file} 缺失'))
    
    print()
    
    # ==================== 打印结果 ====================
    for status, msg in checks:
        print(f'{status} {msg}')
    
    print()
    print('=' * 60)
    
    # 统计
    success = sum(1 for s, _ in checks if s == '✓')
    total = len(checks)
    failed = total - success
    
    if success == total:
        print(f'✓ 所有检查通过 ({success}/{total})')
        print(f'✓ 可以安全构建 v{VERSION}')
        print('=' * 60)
        print()
        print('执行构建命令:')
        print('  python build.py')
        print()
        return True
    else:
        print(f'✗ {failed} 个检查失败 ({success}/{total} 通过)')
        print('✗ 请修复问题后再构建')
        print('=' * 60)
        return False

if __name__ == '__main__':
    success = run_checks()
    sys.exit(0 if success else 1)
