import os
import sys
import uuid
import random
import datetime
import asyncio
from datetime import timedelta
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
import subprocess

# --- 1. 环境准备 (Environment Setup) ---
# 获取项目根目录 (This script is in backend/scripts/)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
backend_dir = os.path.join(project_root, "backend")

if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from app.database import engine
from app.models import (
    User,
    UserRole,
    MenuItem,
    Order,
    OrderItem,
    Transaction,
    OrderStatus,
)
from app.core.security import get_password_hash


async def reset_database():
    """
    一键重置数据库：物理清理文件 + 逻辑初始化结构 + 基础数据填充
    """
    print("🚀 正在一键重置数据库...")

    # --- 2. 物理清理 (Physical Cleanup) ---
    # 类似“格式化磁盘”：直接删除 .db 文件，彻底消除损坏或陈旧结构的可能
    print("\n[Step 1/3] 正在彻底清理数据库文件...")

    student_dir = os.path.join(project_root, "frontend", "Student")
    search_dirs = [
        backend_dir,
        project_root,
        student_dir,
        os.path.join(backend_dir, "app"),
    ]

    deleted_files = set()
    # 2.1 扫描常见位置
    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for ext in ["", "-shm", "-wal", "-journal"]:
            file_path = os.path.join(d, f"coffee.db{ext}")
            if os.path.exists(file_path):
                try:
                    os.chmod(file_path, 0o777)
                    os.remove(file_path)
                    print(f"   ✅ 已删除: {file_path}")
                    deleted_files.add(file_path)
                except Exception as e:
                    print(f"   ❌ 无法删除 {file_path}: {e}")

    # 2.2 深度扫描 (使用 find 命令)
    try:
        result = subprocess.run(
            ["find", project_root, "-name", "coffee.db*", "-type", "f"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        for line in result.stdout.strip().split("\n"):
            if line and line not in deleted_files:
                try:
                    os.remove(line)
                    print(f"   ✅ 已删除 (深度扫描): {line}")
                except:
                    pass
    except:
        pass

    # --- 3. 逻辑初始化 (Logical Initialization) ---
    # 类似“重新安装系统”：重建表结构并添加初始化数据
    print("\n[Step 2/3] 正在初始化数据库结构...")
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    print("   ✅ 数据库表已重新创建。")

    # --- 4. 基础数据填充 (Base Data Seeding) ---
    print("\n[Step 3/3] 正在填充基础演示数据...")

    # Create Local Async Session Factory
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # 4.1 管理员 (Admin)
        admin_user = User(
            username="admin",
            password=get_password_hash("89129885"),
            role=UserRole.ADMIN,
            uuid=str(uuid.uuid4()),
            name="Super Admin",
            balance=999999,
        )
        session.add(admin_user)

        # 4.2 默认学生 (Default Student)
        student_user = User(
            username="student",
            password=get_password_hash("89129885"),
            role=UserRole.STUDENT,
            uuid=str(uuid.uuid4()),
            name="Test Student",
            balance=50000,
        )
        session.add(student_user)

        # 4.3 开发测试账号
        user_1 = User(
            username="1",
            password=get_password_hash("89129885"),
            uuid=str(uuid.uuid4()),
            role=UserRole.STUDENT,
            name="Otiaer",
            balance=10000,
        )
        session.add(user_1)

        # 4.4 咖啡师 (Barista)
        barista_user = User(
            username="barista",
            password=get_password_hash("89129885"),
            uuid=str(uuid.uuid4()),
            role=UserRole.BARISTA,
            name="Barista Staff",
            balance=0,
        )
        session.add(barista_user)

        # 4.4 基础商品 (Base Products)
        session.add(
            MenuItem(
                name="1",
                name_cn="拿铁",
                price=12500,
                category="coffee",
                description="Classic Latte",
                inventory_count=100,
                is_active=True,
            )
        )
        session.add(
            MenuItem(
                name="2",
                name_cn="意式浓缩",
                price=1000,
                category="coffee",
                description="Strong",
                inventory_count=100,
                is_active=True,
            )
        )
        session.add(
            MenuItem(
                name="3",
                name_cn="绿茶",
                price=1200,
                category="fruit",
                description="Fresh",
                inventory_count=50,
                is_active=True,
            )
        )

        await session.commit()
        await session.refresh(student_user)
        # 4.3 user was user_1, refresh it
        await session.refresh(user_1)

    # --- 5. 财务数据填充 (Finance Data Seeding) ---
    print("\n[Step 4/4] 正在填充财务演示数据...")
    async with async_session() as session:
        # 获取用户和商品
        stmt_student = select(User).where(User.username == "student")
        result_student = await session.exec(stmt_student)
        student = result_student.first()

        stmt_items = select(MenuItem)
        result_items = await session.exec(stmt_items)
        items = result_items.all()

        if student and items:
            start_date = datetime.datetime.now() - timedelta(days=7)

            # 5.1 充值记录 (Deposits for past 7 days)
            print("   📥 创建充值记录...")
            for i in range(7):
                day_offset = start_date + timedelta(days=i)
                # 每天 1-2 笔充值
                for _ in range(random.randint(1, 2)):
                    amount = random.choice([5000, 10000, 20000, 50000])  # 50-500元
                    student.balance += amount

                    tx = Transaction(
                        user_id=student.id,
                        external_transaction_id=f"DEP{uuid.uuid4().hex[:8].upper()}",
                        amount=amount,
                        balance_after=student.balance,
                        type="deposit",
                        payment_method="wechat",
                        description="微信充值",
                        created_at=day_offset + timedelta(hours=random.randint(9, 18)),
                    )
                    session.add(tx)

            await session.commit()

            # 5.2 订单消费记录 (Orders for past 7 days)
            print("   📤 创建消费记录...")
            for i in range(7):
                day_offset = start_date + timedelta(days=i)
                # 每天 2-4 笔订单
                for _ in range(random.randint(2, 4)):
                    item = random.choice(items)
                    price = item.price

                    if student.balance < price:
                        student.balance += 50000  # 余额不足自动充值

                    student.balance -= price

                    order_time = day_offset + timedelta(
                        hours=random.randint(8, 20), minutes=random.randint(0, 59)
                    )
                    order_no = f"{order_time.strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
                    pickup_num = random.randint(1, 100)

                    order = Order(
                        user_id=student.id,
                        order_no=order_no,
                        status=OrderStatus.COMPLETED,
                        total_amount=price,
                        pickup_number=pickup_num,
                        is_completed=True,
                        created_at=order_time,
                        updated_at=order_time + timedelta(minutes=5),
                    )
                    session.add(order)
                    await session.flush()

                    oi = OrderItem(
                        order_id=order.id,
                        menu_item_id=item.id,
                        item_name=item.name_cn or item.name,
                        price_snap=price,
                        image_url=item.image_path,
                        quantity=1,
                        spec="{}",
                    )
                    session.add(oi)

                    # 消费交易记录
                    tx = Transaction(
                        user_id=student.id,
                        order_id=order.id,
                        external_transaction_id=f"PAY{uuid.uuid4().hex[:8].upper()}",
                        amount=-price,  # 消费为负数
                        balance_after=student.balance,
                        type="order",
                        payment_method="balance",
                        description=f"订单 #{pickup_num}",
                        created_at=order_time,
                    )
                    session.add(tx)

            session.add(student)
            await session.commit()
            print("   ✅ 财务数据创建完成！")
        else:
            print("   ⚠️ 未找到用户或商品，跳过财务数据")

    print("\n✨ 数据库重置完成！")
    print("--------------------------------")
    print("🔑 管理员: admin / 89129885")
    print("🔑 学生端: student / 89129885")
    print("🔑 开发者: 1 / 89129885")
    print("🔑 咖啡师: barista / 89129885")
    print("--------------------------------")


if __name__ == "__main__":
    asyncio.run(reset_database())
