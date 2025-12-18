"""
测试登录功能
"""
from models import get_db_session, User

def test_login():
    """测试登录功能"""
    db = get_db_session()
    try:
        # 查找admin用户
        user = db.query(User).filter_by(username='admin').first()
        
        if not user:
            print("✗ 未找到admin用户")
            return
        
        print(f"找到用户: {user.username}")
        print(f"角色: {user.role}")
        print(f"激活状态: {user.is_active}")
        print(f"密码哈希: {user.password_hash[:50]}...")
        
        # 测试密码验证
        test_passwords = ['admin123', 'admin', 'Admin123', 'ADMIN123']
        for pwd in test_passwords:
            result = user.check_password(pwd)
            print(f"密码 '{pwd}' 验证结果: {result}")
        
        # 测试密码哈希生成
        from werkzeug.security import generate_password_hash, check_password_hash
        test_hash = generate_password_hash('admin123')
        print(f"\n新生成的密码哈希: {test_hash[:50]}...")
        print(f"验证新哈希: {check_password_hash(test_hash, 'admin123')}")
        print(f"验证旧哈希: {check_password_hash(user.password_hash, 'admin123')}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    test_login()

