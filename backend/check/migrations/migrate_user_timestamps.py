"""
Database Migration Script - Add User Timestamps (SQLite-Compatible)

This script safely adds created_at and updated_at columns to the User table using ALTER TABLE.
Works with existing SQLite database without data loss.

Usage:
    python3 backend/app/migrate_user_timestamps.py
"""

import sys
import os
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database import engine
from app.core import timezone
from datetime import datetime

def migrate_user_timestamps():
    """
    Add created_at and updated_at columns to User table using ALTER TABLE.
    
    SQLite Strategy:
    - Use ALTER TABLE to add columns
    - Set default values for existing records
    - Verify column addition
    """
    print("=" * 70)
    print("Database Migration: Adding User Timestamps (SQLite)")
    print("=" * 70)
    
    with engine.connect() as connection:
        # Check if columns already exist
        print("\n1. Checking existing schema...")
        
        # Get table info
        result = connection.execute(text("PRAGMA table_info(user)"))
        columns = {row[1] for row in result}  # row[1] is column name
        
        has_created_at = 'created_at' in columns
        has_updated_at = 'updated_at' in columns
        
        print(f"   - created_at exists: {has_created_at}")
        print(f"   - updated_at exists: {has_updated_at}")
        
        if has_created_at and has_updated_at:
            print("\n✓ Both timestamp columns already exist. Migration not needed.")
            return True
        
        # Get current timestamp in ISO format
        current_timestamp = timezone.now_cst().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n2. Adding missing columns with default timestamp: {current_timestamp}")
        
        # Add created_at if missing
        if not has_created_at:
            print("   - Adding created_at column...")
            connection.execute(text(
                f"ALTER TABLE user ADD COLUMN created_at TIMESTAMP DEFAULT '{current_timestamp}'"
            ))
            connection.commit()
            print("   ✓ created_at added")
        
        # Add updated_at if missing
        if not has_updated_at:
            print("   - Adding updated_at column...")
            connection.execute(text(
                f"ALTER TABLE user ADD COLUMN updated_at TIMESTAMP DEFAULT '{current_timestamp}'"
            ))
            connection.commit()
            print("   ✓ updated_at added")
        
        # Update all NULL values to current timestamp
        print("\n3. Updating NULL timestamps to current time...")
        
        result = connection.execute(text(
            f"UPDATE user SET created_at = '{current_timestamp}' WHERE created_at IS NULL"
        ))
        rows_updated_created = result.rowcount
        connection.commit()
        
        result = connection.execute(text(
            f"UPDATE user SET updated_at = '{current_timestamp}' WHERE updated_at IS NULL"
        ))
        rows_updated_updated = result.rowcount
        connection.commit()
        
        print(f"   - Updated {rows_updated_created} rows for created_at")
        print(f"   - Updated {rows_updated_updated} rows for updated_at")
        
        return True

def verify_migration():
    """Verify that columns were added successfully."""
    print("\n" + "=" * 70)
    print("Verifying Migration")
    print("=" * 70)
    
    with engine.connect() as connection:
        # Check schema
        result = connection.execute(text("PRAGMA table_info(user)"))
        columns = {row[1] for row in result}
        
        has_created_at = 'created_at' in columns
        has_updated_at = 'updated_at' in columns
        
        if not has_created_at or not has_updated_at:
            print(f"\n✗ FAILED: Missing columns")
            print(f"   - created_at: {has_created_at}")
            print(f"   - updated_at: {has_updated_at}")
            return False
        
        # Count users
        result = connection.execute(text("SELECT COUNT(*) FROM user"))
        user_count = result.scalar()
        
        # Count users with NULL timestamps
        result = connection.execute(text(
            "SELECT COUNT(*) FROM user WHERE created_at IS NULL OR updated_at IS NULL"
        ))
        null_count = result.scalar()
        
        if null_count > 0:
            print(f"\n⚠ WARNING: {null_count} out of {user_count} users have NULL timestamps")
            return False
        
        print(f"\n✓ SUCCESS: All columns added and {user_count} users have timestamps!")
        
        # Show sample data
        print("\nSample user timestamps:")
        result = connection.execute(text(
            "SELECT username, created_at, updated_at FROM user LIMIT 3"
        ))
        for row in result:
            print(f"   - {row[0]}: created={row[1]}, updated={row[2]}")
        
        return True

if __name__ == "__main__":
    print("\n🔄 Starting User Timestamp Migration (SQLite)...\n")
    
    try:
        # Run migration
        print("Step 1: Adding timestamp columns...")
        success = migrate_user_timestamps()
        
        if not success:
            print("\n❌ Migration failed!")
            sys.exit(1)
        
        # Verify
        print("\nStep 2: Verifying migration...")
        success = verify_migration()
        
        if success:
            print("\n" + "=" * 70)
            print("✅ Migration completed successfully!")
            print("=" * 70)
            print("\nNote: Existing users' timestamps reflect migration time,")
            print("      not actual registration time. Future users will have accurate timestamps.")
        else:
            print("\n" + "=" * 70)
            print("❌ Migration verification failed!")
            print("=" * 70)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Migration failed with error:")
        print(f"   {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
