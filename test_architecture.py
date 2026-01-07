#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Cloudflare D1 + Railway 架构功能
"""
import os
import sys

def test_database_manager():
    """测试数据库管理器"""
    print("=" * 60)
    print("测试 DatabaseManager")
    print("=" * 60)
    
    try:
        from database_manager import get_database_manager
        
        db_manager = get_database_manager()
        print(f"✓ DatabaseManager 初始化成功")
        print(f"  数据库类型: {db_manager.db_type}")
        
        # 测试连接
        test_result = db_manager.test_connection()
        print(f"  连接测试: {'✓ 成功' if test_result['success'] else '✗ 失败'}")
        print(f"  消息: {test_result.get('message', 'N/A')}")
        
        # 获取状态
        status = db_manager.get_status()
        print(f"  初始化状态: {'✓ 已初始化' if status['initialized'] else '✗ 未初始化'}")
        if status.get('tables'):
            print(f"  数据表数量: {len(status['tables'])}")
        
        return True
    except Exception as e:
        print(f"✗ DatabaseManager 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routes():
    """测试路由"""
    print("\n" + "=" * 60)
    print("测试路由")
    print("=" * 60)
    
    try:
        from app import app
        
        routes = [
            '/',
            '/health',
            '/api/status',
            '/init-db',
            '/test-d1',
            '/env-check'
        ]
        
        with app.test_client() as client:
            for route in routes:
                try:
                    response = client.get(route)
                    status = '✓' if response.status_code < 500 else '✗'
                    print(f"  {status} {route}: {response.status_code}")
                except Exception as e:
                    print(f"  ✗ {route}: {str(e)[:50]}")
        
        return True
    except Exception as e:
        print(f"✗ 路由测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """测试环境变量"""
    print("\n" + "=" * 60)
    print("环境变量检查")
    print("=" * 60)
    
    env_vars = {
        'PORT': os.environ.get('PORT', '未设置'),
        'HOST': os.environ.get('HOST', '未设置'),
        'CF_ACCOUNT_ID': '已设置' if os.environ.get('CF_ACCOUNT_ID') else '未设置',
        'CF_D1_DATABASE_ID': '已设置' if os.environ.get('CF_D1_DATABASE_ID') else '未设置',
        'DATABASE_PATH': os.environ.get('DATABASE_PATH', '使用默认值'),
    }
    
    for key, value in env_vars.items():
        status = '✓' if value != '未设置' else '○'
        print(f"  {status} {key}: {value}")
    
    return True

def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("Cloudflare D1 + Railway 架构测试")
    print("=" * 60 + "\n")
    
    results = []
    
    # 测试数据库管理器
    results.append(("DatabaseManager", test_database_manager()))
    
    # 测试路由
    results.append(("路由", test_routes()))
    
    # 测试环境变量
    results.append(("环境变量", test_environment()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    if all_passed:
        print("\n✓ 所有测试通过！")
        return 0
    else:
        print("\n✗ 部分测试失败，请检查错误信息")
        return 1

if __name__ == '__main__':
    sys.exit(main())

