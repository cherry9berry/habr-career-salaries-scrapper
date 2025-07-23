"""
Database cleanup script
"""
import psycopg2
import json
import sys

def load_config():
    """Load database configuration"""
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["database"]

def drop_test_table(db_config):
    """Drop test_table from database"""
    try:
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        print("Dropping test_table...")
        cursor.execute("DROP TABLE IF EXISTS test_table CASCADE")
        conn.commit()
        
        cursor.close()
        conn.close()
        
        print("test_table dropped successfully")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    db_config = load_config()
    success = drop_test_table(db_config)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 