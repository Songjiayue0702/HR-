#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
详细诊断脚本 - 逐步测试每个模块的导入
"""
import sys
import os
import traceback

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("详细诊断脚本")
print("=" * 70)
print()

errors = []

# 测试1: Python基础
print("[1/15] 测试Python版本...")
print(f"  Python版本: {sys.version}")
print(f"  工作目录: {os.getcwd()}")
print()

# 测试2: 基础库
print("[2/15] 测试基础库导入...")
try:
    import io
    import json
    import os
    print("  ✓ 基础库导入成功")
except Exception as e:
    print(f"  ✗ 基础库导入失败: {e}")
    errors.append(f"基础库: {e}")

# 测试3: Flask
print("[3/15] 测试Flask...")
try:
    from flask import Flask
    print(f"  ✓ Flask导入成功")
except Exception as e:
    print(f"  ✗ Flask导入失败: {e}")
    print("  请运行: pip install flask")
    errors.append(f"Flask: {e}")

# 测试4: SQLAlchemy
print("[4/15] 测试SQLAlchemy...")
try:
    import sqlalchemy
    print(f"  ✓ SQLAlchemy导入成功")
except Exception as e:
    print(f"  ✗ SQLAlchemy导入失败: {e}")
    errors.append(f"SQLAlchemy: {e}")

# 测试5: config
print("[5/15] 测试config模块...")
try:
    from config import Config
    print("  ✓ config导入成功")
except Exception as e:
    print(f"  ✗ config导入失败: {e}")
    traceback.print_exc()
    errors.append(f"config: {e}")

# 测试6: models
print("[6/15] 测试models模块...")
try:
    from models import get_db_session
    print("  ✓ models导入成功")
except Exception as e:
    print(f"  ✗ models导入失败: {e}")
    traceback.print_exc()
    errors.append(f"models: {e}")

# 测试7: utils目录
print("[7/15] 检查utils目录...")
if os.path.exists('utils'):
    print("  ✓ utils目录存在")
    utils_files = os.listdir('utils')
    print(f"  包含文件: {', '.join([f for f in utils_files if f.endswith('.py')])}")
else:
    print("  ✗ utils目录不存在")
    errors.append("utils目录不存在")

# 测试8: file_parser
print("[8/15] 测试utils.file_parser...")
try:
    from utils.file_parser import extract_text
    print("  ✓ file_parser导入成功")
except Exception as e:
    print(f"  ✗ file_parser导入失败: {e}")
    traceback.print_exc()
    errors.append(f"file_parser: {e}")

# 测试9: info_extractor
print("[9/15] 测试utils.info_extractor...")
try:
    from utils.info_extractor import InfoExtractor
    print("  ✓ info_extractor导入成功")
except Exception as e:
    print(f"  ✗ info_extractor导入失败: {e}")
    traceback.print_exc()
    errors.append(f"info_extractor: {e}")

# 测试10: 其他依赖
print("[10/15] 测试其他依赖...")
deps = [
    ('PyPDF2', 'PyPDF2'),
    ('docx', 'python-docx'),
    ('openpyxl', 'openpyxl'),
    ('reportlab', 'reportlab'),
]
for module, name in deps:
    try:
        __import__(module)
        print(f"  ✓ {name}导入成功")
    except Exception as e:
        print(f"  ✗ {name}导入失败: {e}")
        errors.append(f"{name}: {e}")

print()

# 测试11: 尝试创建Flask应用
print("[11/15] 测试创建Flask应用...")
try:
    from flask import Flask
    test_app = Flask(__name__)
    print("  ✓ Flask应用创建成功")
except Exception as e:
    print(f"  ✗ Flask应用创建失败: {e}")
    errors.append(f"Flask应用创建: {e}")

print()

# 测试12: 尝试导入完整app
print("[12/15] 尝试导入完整app模块...")
print("  这可能需要一些时间，请稍候...")
try:
    # 捕获所有输出和错误
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    f = io.StringIO()
    e = io.StringIO()
    
    with redirect_stdout(f), redirect_stderr(e):
        from app import app
    
    output = f.getvalue()
    error_output = e.getvalue()
    
    if error_output:
        print(f"  警告: 有错误输出（可能不影响运行）")
        if len(error_output) < 500:
            print(f"  错误信息: {error_output}")
    
    print("  ✓ app模块导入成功")
    print(f"  应用名称: {app.name}")
except Exception as e:
    print(f"  ✗ app模块导入失败: {e}")
    print("\n  详细错误信息:")
    traceback.print_exc()
    errors.append(f"app导入: {e}")

print()

# 总结
print("=" * 70)
print("诊断结果总结")
print("=" * 70)

if errors:
    print(f"\n发现 {len(errors)} 个问题:\n")
    for i, error in enumerate(errors, 1):
        print(f"  {i}. {error}")
    print("\n请根据上述错误信息修复问题。")
else:
    print("\n✓ 所有检查通过！程序应该可以正常启动。")
    print("\n现在尝试启动服务器...")
    print("=" * 70)
    try:
        from app import app
        print("\n服务器正在启动...")
        print("访问地址: http://127.0.0.1:5000")
        print("按 Ctrl+C 停止服务器\n")
        app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n启动失败: {e}")
        traceback.print_exc()

print()
input("按回车键退出...")




