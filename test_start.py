#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试启动脚本 - 检查所有依赖和配置
"""
import sys
import os

print("=" * 60)
print("智能简历数据库系统 - 启动诊断")
print("=" * 60)
print()

# 检查Python版本
print(f"Python版本: {sys.version}")
print()

# 检查关键依赖
print("检查依赖包...")
missing_deps = []
deps_to_check = [
    ('flask', 'Flask'),
    ('sqlalchemy', 'SQLAlchemy'),
    ('PyPDF2', 'PyPDF2'),
    ('docx', 'python-docx'),
    ('openpyxl', 'openpyxl'),
    ('reportlab', 'reportlab'),
]

for module_name, display_name in deps_to_check:
    try:
        mod = __import__(module_name)
        version = getattr(mod, '__version__', '未知版本')
        print(f"✓ {display_name}: {version}")
    except ImportError:
        print(f"✗ {display_name}: 未安装")
        missing_deps.append(display_name)

print()

# 检查文件
print("检查必要文件...")
files_to_check = [
    'app.py',
    'models.py',
    'config.py',
    'database.db'
]

for file in files_to_check:
    if os.path.exists(file):
        print(f"✓ {file}")
    else:
        print(f"✗ {file}: 不存在")

print()

# 检查目录
print("检查必要目录...")
dirs_to_check = [
    'templates',
    'static',
    'uploads',
    'exports'
]

for dir_name in dirs_to_check:
    if os.path.exists(dir_name):
        print(f"✓ {dir_name}/")
    else:
        print(f"✗ {dir_name}/: 不存在")
        if dir_name in ['uploads', 'exports']:
            try:
                os.makedirs(dir_name, exist_ok=True)
                print(f"  → 已创建目录 {dir_name}/")
            except Exception as e:
                print(f"  → 创建失败: {e}")

print()

# 尝试导入app
print("尝试导入应用...")
try:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from app import app
    print("✓ 应用导入成功")
    print(f"✓ Flask应用已创建: {app}")
except Exception as e:
    print(f"✗ 应用导入失败: {e}")
    import traceback
    traceback.print_exc()
    print()
    print("=" * 60)
    print("请检查上述错误并修复后重试")
    print("=" * 60)
    sys.exit(1)

print()
print("=" * 60)
if missing_deps:
    print(f"缺少依赖: {', '.join(missing_deps)}")
    print(f"请运行: pip install {' '.join(missing_deps)}")
    print("=" * 60)
else:
    print("所有检查通过！可以启动应用。")
    print("=" * 60)
    print()
    print("正在启动服务器...")
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print()
    try:
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        import traceback
        traceback.print_exc()






