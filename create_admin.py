"""
创建或重置管理员账户脚本
"""
import sys
print("开始执行脚本...", file=sys.stderr)
sys.stderr.flush()

try:
    from models import get_db_session, User
    print("成功导入models模块", file=sys.stderr)
    sys.stderr.flush()
except Exception as e:
    print(f"导入models失败: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc()
    sys.exit(1)

def create_admin():
    """创建或重置管理员账户"""
    print("开始创建管理员账户...", file=sys.stderr)
    sys.stderr.flush()
    
    db = get_db_session()
    try:
        # 检查是否已存在admin用户
        admin = db.query(User).filter_by(username='admin').first()
        
        if admin:
            print(f"管理员账户已存在，ID: {admin.id}")
            print(f"当前密码哈希: {admin.password_hash[:20]}...")
            # 重置密码
            admin.set_password('admin123')
            db.commit()
            print("密码已重置为: admin123")
            
            # 重新查询验证
            db.refresh(admin)
            print(f"新密码哈希: {admin.password_hash[:20]}...")
        else:
            # 创建新的管理员账户
            print("创建新的管理员账户...")
            admin = User(
                username='admin',
                role='admin',
                real_name='系统管理员',
                is_active=1
            )
            admin.set_password('admin123')
            db.add(admin)
            db.commit()
            print("管理员账户创建成功！")
            print("用户名: admin")
            print("密码: admin123")
        
        # 验证密码
        test_admin = db.query(User).filter_by(username='admin').first()
        if test_admin:
            print(f"找到管理员账户，ID: {test_admin.id}")
            if test_admin.check_password('admin123'):
                print("✓ 密码验证成功！")
            else:
                print("✗ 密码验证失败！")
                print(f"密码哈希: {test_admin.password_hash[:50]}...")
        else:
            print("✗ 未找到管理员账户！")
            
    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
    finally:
        db.close()
        print("数据库连接已关闭")

if __name__ == '__main__':
    create_admin()
    print("脚本执行完成")

