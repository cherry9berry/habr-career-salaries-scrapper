#!/usr/bin/env python3
"""
Скрипт для миграции структуры БД и данных в Supabase
"""

import os
import sys
import traceback
import psycopg2
from pathlib import Path

# Supabase connection params
SUPABASE_HOST = "db.cehitgienxwzplcxbfdk.supabase.co"
SUPABASE_PORT = 5432
SUPABASE_DB = "postgres"
SUPABASE_USER = "postgres"
SUPABASE_PASSWORD = "!!!!QQQQ2222"

def execute_sql_file(conn, file_path):
    """Execute SQL file on database connection"""
    cursor = conn.cursor()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            sql = f.read()
            print(f"Executing {file_path}...")
            cursor.execute(sql)
            conn.commit()
            print(f"✅ Success: {file_path}")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error in {file_path}: {str(e)}")
        traceback.print_exc()
    finally:
        cursor.close()

def main():
    print("Connecting to Supabase...")
    print(f"Host: {SUPABASE_HOST}")
    print(f"Port: {SUPABASE_PORT}")
    print(f"Database: {SUPABASE_DB}")
    print(f"User: {SUPABASE_USER}")
    
    try:
        # First method - connection string
        conn_str = f"postgresql://{SUPABASE_USER}:{SUPABASE_PASSWORD}@{SUPABASE_HOST}:{SUPABASE_PORT}/{SUPABASE_DB}"
        print(f"Trying connection string: {conn_str.replace(SUPABASE_PASSWORD, '********')}")
        conn = psycopg2.connect(conn_str)
        print("Connected successfully!")
    except Exception as e:
        print(f"❌ Method 1 failed: {str(e)}")
        traceback.print_exc()
        
        try:
            # Second method - separate parameters
            print("\nTrying method 2 with separate parameters...")
            conn = psycopg2.connect(
                host=SUPABASE_HOST,
                port=SUPABASE_PORT,
                dbname=SUPABASE_DB,
                user=SUPABASE_USER,
                password=SUPABASE_PASSWORD
            )
            print("Connected successfully!")
        except Exception as e:
            print(f"❌ Method 2 failed: {str(e)}")
            traceback.print_exc()
            sys.exit(1)
    
    # Get path to SQL files
    sql_dir = Path(__file__).parent.parent / "sql queries"
    print(f"\nSQL directory: {sql_dir}")
    
    # Execute files in correct order
    try:
        sql_files = [
            sql_dir / "01_create_tables.sql",
            sql_dir / "03_initial_data.sql"
        ]
        
        for sql_file in sql_files:
            if not sql_file.exists():
                print(f"❌ File not found: {sql_file}")
                continue
                
            execute_sql_file(conn, sql_file)
            
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    main() 