#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
启动脚本 - 用于诊断和启动Flask应用
"""
import sys
import os
import socket

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def check_port(port):
    """检查端口是否被占用"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(('127.0.0.1', port))
    sock.close()
    return result == 0

def main():
    port = 5000
    
    print('=' * 60)
    print('智能简历数据库系统 - 启动诊断')
    print('=' * 60)
    print()
    
    # 检查端口
    if check_port(port):
        print(f'⚠️  警告: 端口 {port} 已被占用！')
        print('   请关闭占用该端口的程序，或修改端口号。')
        print()
        response = input('是否继续尝试启动？(y/n): ')
        if response.lower() != 'y':
            print('已取消启动。')
            return
    else:
        print(f'✓ 端口 {port} 可用')
    print()
    
    # 检查关键依赖
    print('正在检查依赖...')
    missing_deps = []
    try:
        import flask
        print(f'✓ Flask {flask.__version__}')
    except ImportError:
        missing_deps.append('flask')
        print('✗ Flask 未安装')
    
    try:
        import sqlalchemy
        print(f'✓ SQLAlchemy {sqlalchemy.__version__}')
    except ImportError:
        missing_deps.append('sqlalchemy')
        print('✗ SQLAlchemy 未安装')
    
    if missing_deps:
        print()
        print('❌ 缺少以下依赖，请运行:')
        print(f'   pip install {" ".join(missing_deps)}')
        return
    
    print()
    print('=' * 60)
    print('正在启动服务器...')
    print('=' * 60)
    print(f'服务器地址: http://127.0.0.1:{port}')
    print(f'局域网地址: http://0.0.0.0:{port}')
    print('=' * 60)
    print('按 Ctrl+C 停止服务器')
    print('=' * 60)
    print()
    
    # 启动应用
    try:
        from app import app
        app.run(debug=True, host='0.0.0.0', port=port, use_reloader=False)
    except Exception as e:
        print(f'❌ 启动失败: {e}')
        import traceback
        traceback.print_exc()
        input('\n按回车键退出...')

if __name__ == '__main__':
    main()

