#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 Flask 应用路由重定向功能
"""
import sys

def test_routes():
    """测试路由配置"""
    print("=" * 60)
    print("Flask 路由重定向测试")
    print("=" * 60)
    
    try:
        from app import app
        
        # 获取所有路由
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append({
                'path': str(rule),
                'methods': list(rule.methods),
                'endpoint': rule.endpoint
            })
        
        # 检查关键路由
        print("\n关键路由检查:")
        print("-" * 60)
        
        key_routes = {
            '/': 'index',
            '/login': 'login_page',
            '/app': 'app_index',
            '/system-status': 'system_status',
            '/health': 'health_check',
            '/api/status': 'api_status'
        }
        
        all_ok = True
        for path, endpoint in key_routes.items():
            found = False
            for route in routes:
                if route['path'] == path:
                    found = True
                    methods = ', '.join([m for m in route['methods'] if m != 'HEAD' and m != 'OPTIONS'])
                    print(f"✓ {path:20} -> {endpoint:20} [{methods}]")
                    break
            
            if not found:
                print(f"✗ {path:20} -> {endpoint:20} [未找到]")
                all_ok = False
        
        # 测试重定向逻辑（模拟）
        print("\n重定向逻辑测试:")
        print("-" * 60)
        
        with app.test_client() as client:
            # 测试 1: 未登录访问 /
            print("\n1. 测试未登录访问 /")
            response = client.get('/')
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if '/login' in location:
                    print(f"   ✓ 正确重定向到: {location}")
                else:
                    print(f"   ✗ 重定向错误: {location}")
                    all_ok = False
            else:
                print(f"   ✗ 期望 302 重定向，实际: {response.status_code}")
                all_ok = False
            
            # 测试 2: 访问 /login
            print("\n2. 测试访问 /login")
            response = client.get('/login')
            if response.status_code == 200:
                print(f"   ✓ 正常显示登录页面")
            else:
                print(f"   ✗ 状态码: {response.status_code}")
                all_ok = False
            
            # 测试 3: 访问 /system-status
            print("\n3. 测试访问 /system-status")
            response = client.get('/system-status')
            if response.status_code == 200:
                print(f"   ✓ 正常显示系统状态页面")
            else:
                print(f"   ✗ 状态码: {response.status_code}")
                all_ok = False
            
            # 测试 4: 访问 /app（未登录）
            print("\n4. 测试未登录访问 /app")
            response = client.get('/app')
            if response.status_code == 302:
                location = response.headers.get('Location', '')
                if '/login' in location:
                    print(f"   ✓ 正确重定向到登录页面: {location}")
                else:
                    print(f"   ✗ 重定向错误: {location}")
                    all_ok = False
            else:
                print(f"   ✗ 期望 302 重定向，实际: {response.status_code}")
                all_ok = False
            
            # 测试 5: 访问 /health
            print("\n5. 测试访问 /health")
            response = client.get('/health')
            if response.status_code in [200, 503]:
                print(f"   ✓ 健康检查端点正常 (状态码: {response.status_code})")
            else:
                print(f"   ✗ 状态码: {response.status_code}")
                all_ok = False
        
        # 总结
        print("\n" + "=" * 60)
        if all_ok:
            print("✓ 所有测试通过！")
            return 0
        else:
            print("✗ 部分测试失败，请检查代码")
            return 1
            
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(test_routes())

