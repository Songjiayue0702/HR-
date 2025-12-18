#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试启动脚本 - 显示所有错误信息
"""
import sys
import os
import traceback

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 禁用OCR
os.environ['OCR_ENABLED'] = 'false'

print("=" * 70)
print("测试启动 - 显示所有错误信息")
print("=" * 70)
print()
print(f"Python版本: {sys.version}")
print(f"工作目录: {os.getcwd()}")
print()

# 逐步测试导入
print("步骤1: 测试导入Flask...")
try:
    from flask import Flask
    print("  ✓ Flask导入成功")
except Exception as e:
    print(f"  ✗ Flask导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤2: 测试导入config...")
try:
    from config import Config
    print("  ✓ config导入成功")
except Exception as e:
    print(f"  ✗ config导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤3: 测试导入models...")
try:
    from models import get_db_session
    print("  ✓ models导入成功")
except Exception as e:
    print(f"  ✗ models导入失败: {e}")
    traceback.print_exc()
    input("\n按回车键退出...")
    sys.exit(1)

print()
print("步骤4: 测试导入app模块...")
print("  这可能需要一些时间，请稍候...")
print()
try:
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
print("步骤5: 检查端口...")
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
port = 5000
result = sock.connect_ex(('127.0.0.1', port))
sock.close()

if result == 0:
    print(f"  ⚠ 警告: 端口{port}已被占用")
    print("  请关闭占用该端口的程序")
    response = input("  是否尝试使用端口5001？(y/n): ")
    if response.lower() == 'y':
        port = 5001
        print(f"  使用端口 {port}")
    else:
        print("  请手动关闭占用端口的程序后重试")
        input("\n按回车键退出...")
        sys.exit(1)
else:
    print(f"  ✓ 端口{port}可用")

print()
print("=" * 70)
print("所有检查通过！正在启动服务器...")
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
