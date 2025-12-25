#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
直接启动并显示所有错误
"""
import sys
import os
import traceback

# 确保输出立即显示
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None

os.chdir(os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("智能简历数据库系统 - 启动")
print("=" * 70)
print()
print(f"Python版本: {sys.version}")
print(f"工作目录: {os.getcwd()}")
print()

# 禁用OCR以避免初始化问题
print("设置环境变量: OCR_ENABLED=false")
os.environ['OCR_ENABLED'] = 'false'
print()

# 逐步导入
print("步骤1: 导入基础模块...")
try:
    import io
    import json
    print("  ✓ 基础模块导入成功")
except Exception as e:
    print(f"  ✗ 基础模块导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤2: 导入Flask...")
try:
    from flask import Flask
    print("  ✓ Flask导入成功")
except Exception as e:
    print(f"  ✗ Flask导入失败: {e}")
    print("\n请运行: pip install flask")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤3: 导入config...")
try:
    from config import Config
    print("  ✓ config导入成功")
except Exception as e:
    print(f"  ✗ config导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤4: 导入models...")
try:
    from models import get_db_session
    print("  ✓ models导入成功")
except Exception as e:
    print(f"  ✗ models导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤5: 导入app模块（这可能需要一些时间）...")
print("  如果程序在这里卡住，可能是OCR初始化的问题")
print()

try:
    # 尝试导入app
    from app import app
    print("  ✓ app模块导入成功")
    print(f"  应用名称: {app.name}")
except Exception as e:
    print(f"  ✗ app模块导入失败: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
    print()
    input("按回车键退出...")
    sys.exit(1)

print()
print("=" * 70)
print("所有模块导入成功！")
print("=" * 70)
print()

# 检查端口
print("检查端口5000...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port_check = sock.connect_ex(('127.0.0.1', 5000))
sock.close()

if port_check == 0:
    print("  ⚠ 警告: 端口5000已被占用")
    print("  请关闭占用该端口的程序")
    response = input("  是否尝试使用其他端口？(y/n): ")
    if response.lower() == 'y':
        port = 5001
        print(f"  使用端口 {port}")
    else:
        print("  请手动关闭占用端口的程序后重试")
        input("\n按回车键退出...")
        sys.exit(1)
else:
    port = 5000
    print(f"  ✓ 端口{port}可用")

print()
print("=" * 70)
print("正在启动服务器...")
print("=" * 70)
print(f"访问地址: http://127.0.0.1:{port}")
print("按 Ctrl+C 停止服务器")
print("=" * 70)
print()

try:
    app.run(debug=True, host='127.0.0.1', port=port, use_reloader=False)
except KeyboardInterrupt:
    print("\n\n服务器已停止")
except Exception as e:
    print(f"\n\n启动失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")








