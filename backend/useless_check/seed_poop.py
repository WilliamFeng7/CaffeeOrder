import os
import sys

# 将 backend 目录添加到 sys.path 以支持各种运行方式
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from sqlmodel import Session, select
from app.database import engine
from app.models import MenuItem

def seed_poop_items():
    """
    填充可爱的"便便"主题菜单项 (Seed Poop Theme Menu Items)
    
    用于测试自定义图片和分类显示功能。
    """
    items = [
        {
            "name": "Cute Poop 3D",
            "name_cn": "3D 可爱便便",
            "description": "Cute 3D rendered character.",
            "price": 9900, # 99.00 元 (单位: 分)
            "category": "seasonal",
            "image_path": "/static/poop1.png"
        },
        {
            "name": "Pixel Poop",
            "name_cn": "像素便便",
            "description": "Retro game style art.",
            "price": 8800, # 88.00 元
            "category": "seasonal",
            "image_path": "/static/poop2.png"
        },
        {
            "name": "Neon Poop",
            "name_cn": "霓虹便便",
            "description": "Glowing neon sign style.",
            "price": 12000, # 120.00 元
            "category": "seasonal",
            "image_path": "/static/poop3.png"
        },
        {
            "name": "Sticker Poop",
            "name_cn": "便便贴纸",
            "description": "Cool sunglasses sticker.",
            "price": 50000, # 500.00 元
            "category": "seasonal",
            "image_path": "/static/poop4.png"
        },
        {
            "name": "Golden Trophy Poop",
            "name_cn": "黄金便便奖杯",
            "description": "First place trophy!",
            "price": 99900, # 999.00 元
            "category": "top",
            "image_path": "/static/poop5.png"
        }
    ]

    with Session(engine) as session:
        for item_data in items:
            # 检查同名商品是否存在
            existing = session.exec(select(MenuItem).where(MenuItem.name == item_data["name"])).first()
            if not existing:
                print(f"正在添加 {item_data['name']}...")
                item = MenuItem(
                    name=item_data["name"],
                    name_cn=item_data["name_cn"],
                    description=item_data["description"],
                    price=item_data["price"],
                    category=item_data["category"],
                    image_path=item_data["image_path"],
                    is_active=True
                )
                session.add(item)
            else:
                print(f"{item_data['name']} 已存在，更新图片路径... (Updating image)")
                existing.image_path = item_data["image_path"]
                existing.name_cn = item_data["name_cn"] # 同时也更新中文名
                existing.price = item_data["price"]     # 同时也更新价格
                session.add(existing)
        
        session.commit()
        print("菜单项填充完成 (Done seeding items).")

if __name__ == "__main__":
    seed_poop_items()
