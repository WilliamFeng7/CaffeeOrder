#!/usr/bin/env python3
"""
数据库优化脚本 (Database Optimization Script)
定期运行以保持数据库性能

功能:
1. VACUUM - 压缩数据库，回收空间
2. ANALYZE - 更新统计信息，优化查询计划
3. WAL Checkpoint - 清理 WAL 日志
4. 完整性检查 - 确保数据完整
"""
import sqlite3
import os
import sys

# 数据库路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coffee.db")


def optimize_database():
    if not os.path.exists(DB_PATH):
        print("❌ 数据库文件不存在")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔧 开始数据库优化...")
    initial_size = os.path.getsize(DB_PATH) / 1024

    # 1. 完整性检查
    print("\n1️⃣ 执行完整性检查...")
    cursor.execute("PRAGMA integrity_check;")
    result = cursor.fetchone()[0]
    if result != "ok":
        print(f"   ⚠️ 发现问题: {result}")
        print("   建议: 考虑从备份恢复数据库")
        conn.close()
        sys.exit(1)
    print("   ✅ 数据库完整性: OK")

    # 2. WAL Checkpoint
    print("\n2️⃣ 执行 WAL Checkpoint...")
    cursor.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    print("   ✅ 完成")

    # 3. VACUUM
    print("\n3️⃣ 执行 VACUUM...")
    cursor.execute("VACUUM;")
    print("   ✅ 完成")

    # 4. ANALYZE
    print("\n4️⃣ 执行 ANALYZE...")
    cursor.execute("ANALYZE;")
    print("   ✅ 完成")

    # 5. 应用性能设置
    print("\n5️⃣ 应用性能优化设置...")
    cursor.execute("PRAGMA synchronous=NORMAL;")
    cursor.execute("PRAGMA cache_size=-8000;")  # 8MB
    cursor.execute("PRAGMA temp_store=MEMORY;")
    print("   ✅ 完成")

    conn.commit()
    conn.close()

    # 统计结果
    final_size = os.path.getsize(DB_PATH) / 1024
    saved = initial_size - final_size

    print("\n" + "=" * 40)
    print("✨ 优化完成!")
    print(f"   优化前: {initial_size:.1f} KB")
    print(f"   优化后: {final_size:.1f} KB")
    if saved > 0:
        print(f"   节省空间: {saved:.1f} KB")
    print("=" * 40)


if __name__ == "__main__":
    optimize_database()
