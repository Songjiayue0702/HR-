#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查 Cloudflare Worker 代码是否符合要求
"""
import ast
import inspect
import sys

def check_worker_code(filename='worker.py'):
    """检查 Worker 代码"""
    print("=" * 60)
    print("Cloudflare Worker 代码检查")
    print("=" * 60)
    
    errors = []
    warnings = []
    
    try:
        # 读取文件
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 解析 AST
        tree = ast.parse(code)
        
        # 检查是否有 fetch 函数
        has_fetch = False
        fetch_is_async = False
        fetch_signature = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef) and node.name == 'fetch':
                has_fetch = True
                fetch_is_async = True
                # 检查参数
                args = [arg.arg for arg in node.args.args]
                if len(args) >= 2 and args[0] == 'request' and args[1] == 'env':
                    fetch_signature = f"async def fetch({', '.join(args)})"
                else:
                    errors.append(f"fetch 函数参数不正确，应该是: async def fetch(request, env)")
                break
            elif isinstance(node, ast.FunctionDef) and node.name == 'fetch':
                has_fetch = True
                errors.append("fetch 函数必须是异步函数 (async def)")
                break
        
        # 检查 export
        has_export = False
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == 'export':
                        has_export = True
                        warnings.append("发现 export 变量，Python Workers 可能不需要它")
                        break
        
        # 输出结果
        print(f"\n1. fetch 函数检查:")
        if has_fetch:
            print(f"   ✓ fetch 函数存在")
            if fetch_is_async:
                print(f"   ✓ fetch 函数是异步的")
            else:
                print(f"   ✗ fetch 函数不是异步的")
            if fetch_signature:
                print(f"   ✓ 函数签名: {fetch_signature}")
        else:
            print(f"   ✗ fetch 函数不存在")
            errors.append("必须定义 async def fetch(request, env) 函数")
        
        print(f"\n2. export 变量检查:")
        if has_export:
            print(f"   ⚠ 发现 export 变量（Python Workers 可能不需要）")
        else:
            print(f"   ✓ 没有 export 变量（正确）")
        
        # 导入模块检查
        print(f"\n3. 模块导入检查:")
        try:
            import worker
            if hasattr(worker, 'fetch'):
                func = getattr(worker, 'fetch')
                print(f"   ✓ 可以导入 fetch 函数")
                print(f"   ✓ 是异步函数: {inspect.iscoroutinefunction(func)}")
                sig = inspect.signature(func)
                print(f"   ✓ 函数签名: {sig}")
            else:
                print(f"   ✗ 无法导入 fetch 函数")
                errors.append("无法从模块导入 fetch 函数")
        except Exception as e:
            print(f"   ✗ 导入失败: {e}")
            errors.append(f"模块导入失败: {e}")
        
        # 总结
        print("\n" + "=" * 60)
        print("检查总结")
        print("=" * 60)
        
        if errors:
            print("\n✗ 发现错误:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        
        if warnings:
            print("\n⚠ 警告:")
            for i, warning in enumerate(warnings, 1):
                print(f"  {i}. {warning}")
        
        if not errors and not warnings:
            print("\n✓ 所有检查通过！代码应该可以正常部署。")
            return 0
        elif not errors:
            print("\n⚠ 有警告，但应该可以部署。")
            return 0
        else:
            print("\n✗ 发现错误，请修复后重新部署。")
            return 1
            
    except SyntaxError as e:
        print(f"\n✗ 语法错误: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(check_worker_code())

