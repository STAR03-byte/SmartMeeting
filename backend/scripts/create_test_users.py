"""创建测试用户用于负责人匹配验证。"""

import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.database import Base
from app.core.security import get_password_hash
from app.models.user import User


def create_test_users():
    """创建测试用户：wanglei 和 lina。"""
    
    # 根据配置选择数据库连接
    if settings.db_backend == "sqlite":
        database_url = settings.sqlite_database_uri
    else:
        database_url = settings.sqlalchemy_database_uri
    
    print(f"使用数据库: {settings.db_backend}")
    print(f"连接地址: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    
    engine = create_engine(database_url, echo=False)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # 创建所有表（如果不存在）
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # 检查用户是否已存在
        existing_wanglei = db.query(User).filter(User.username == "wanglei").first()
        existing_lina = db.query(User).filter(User.username == "lina").first()
        
        users_to_create = []
        
        if not existing_wanglei:
            users_to_create.append(User(
                username="wanglei",
                email="wanglei@example.com",
                password_hash=get_password_hash("password123"),
                full_name="王磊",
                role="member",
                is_active=True
            ))
            print("[+] 准备创建用户: wanglei (王磊)")
        else:
            print("[-] 用户 wanglei 已存在，跳过")
        
        if not existing_lina:
            users_to_create.append(User(
                username="lina",
                email="lina@example.com",
                password_hash=get_password_hash("password123"),
                full_name="李娜",
                role="member",
                is_active=True
            ))
            print("[+] 准备创建用户: lina (李娜)")
        else:
            print("[-] 用户 lina 已存在，跳过")
        
        if users_to_create:
            db.add_all(users_to_create)
            db.commit()
            print(f"\n[OK] 成功创建 {len(users_to_create)} 个测试用户")
        else:
            print("\n[!] 没有需要创建的用户")
        
        # 显示所有用户
        all_users = db.query(User).all()
        print(f"\n当前数据库中的用户 ({len(all_users)} 个):")
        print("-" * 80)
        print(f"{'ID':<5} {'用户名':<15} {'姓名':<10} {'邮箱':<25} {'状态'}")
        print("-" * 80)
        for u in all_users:
            status = "启用" if u.is_active else "禁用"
            print(f"{u.id:<5} {u.username:<15} {u.full_name:<10} {u.email:<25} {status}")
        print("-" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERR] 错误: {e}")
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    success = create_test_users()
    sys.exit(0 if success else 1)