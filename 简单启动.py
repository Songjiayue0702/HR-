#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单启动脚本 - 禁用OCR，直接启动
"""
import sys
import os
import traceback

# 设置工作目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# 禁用OCR，避免初始化问题
os.environ['OCR_ENABLED'] = 'false'

print("=" * 60)
print("智能简历数据库系统 - 启动中")
print("=" * 60)
print()

try:
    print("正在导入应用...")
    # 导入前先设置环境变量
    from app import app
    
    print("✓ 应用导入成功")
    print()
    print("=" * 60)
    print("服务器正在启动...")
    print("=" * 60)
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()
    
    # 启动服务器
    app.run(debug=True, host='127.0.0.1', port=5000, use_reloader=False)
    
except KeyboardInterrupt:
    print("\n服务器已停止")
except Exception as e:
    print(f"\n错误: {e}")
    print("\n详细错误信息:")
    traceback.print_exc()
    print()
    input("按回车键退出...")






