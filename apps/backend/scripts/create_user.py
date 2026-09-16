import sys
import uuid
from pathlib import Path

from sqlmodel import Session, create_engine, select

# Add backend directory to sys.path to allow imports from 'app'
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.append(str(backend_dir))

from app.core.security import validate_password  # noqa: E402
from app.models import User, UserRole  # noqa: E402

# Use a sync engine for the script to avoid aiosqlite dependency issues
# and complexity of async in a simple CLI script.
sqlite_file_name = backend_dir / "coffee.db"
DATABASE_URL = f"sqlite:///{sqlite_file_name}"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})


def create_user(
    username, password, role_str="student", name=None, phone=None, email=None
):
    """
    创建用户的主逻辑 (Main logic to create user)
    """
    print(f"🔄 正在尝试创建用户: {username}...")

    # 1. 验证角色 (Validate Role)
    try:
        role = UserRole(role_str.lower())
    except ValueError:
        print(f"❌ 角色错误: '{role_str}' 无效。")
        print(f"👉 可用角色: {', '.join([r.value for r in UserRole])}")
        return

    # 2. 检查密码复杂度 (Check Password Complexity)
    try:
        validate_password(password)
    except ValueError as e:
        print(f"❌ 密码错误: {e}")
        return

    # Ensure tables exist
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 3. 检查用户是否已存在 (Check Existence)
        existing_user = session.exec(
            select(User).where(User.username == username)
        ).first()
        if existing_user:
            print(
                f"❌ 创建失败: 用户名 '{username}' 已经存在! (ID: {existing_user.id})"
            )
            return

        # 4. 创建新用户对象 (Create Object)
        new_user = User(
            username=username,
            uuid=str(uuid.uuid4()),
            password=password,
            role=role,
            name=name,
            phone=phone,
            email=email,
            balance=0,
        )

        try:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            print("-" * 30)
            print("✅ 用户创建成功! (User Created Successfully)")
            print(f"   👤 ID: {new_user.id}")
            print(f"   🔑 用户名: {new_user.username}")
            print(f"   🛡️ 角色: {new_user.role.value}")
            print("-" * 30)
        except Exception as e:
            print(f"❌ 数据库错误: {e}")


if __name__ == "__main__":
    # 命令行入口
    # 如果没有命令行参数，改为交互式输入 (Interactive Mode)
    if len(sys.argv) < 3:
        print("\n--- 创建新用户 (交互模式) ---")
        try:
            username = input("请输入用户名 (Username): ").strip()
            if not username:
                print("❌ 用户名不能为空")
                sys.exit(1)

            password = input("请输入密码 (Password): ").strip()
            if not password:
                print("❌ 密码不能为空")
                sys.exit(1)

            role = input("请输入角色 (Role, 默认为 student): ").strip() or "student"
            name = input("请输入真实姓名 (Name, 可选): ").strip() or None
            phone = input("请输入手机号 (Phone, 可选): ").strip() or None
            email = input("请输入邮箱 (Email, 可选): ").strip() or None

            create_user(username, password, role, name, phone, email)

        except KeyboardInterrupt:
            print("\n已取消")
    else:
        # 命令行模式 (Command Line Mode)
        # Usage: python create_user.py <username> <password> [role]
        username = sys.argv[1]
        password = sys.argv[2]
        role = sys.argv[3] if len(sys.argv) > 3 else "student"
        create_user(username, password, role)
