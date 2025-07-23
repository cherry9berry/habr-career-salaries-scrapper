"""
Utility script to update reference tables from Excel files
"""
import argparse
import pandas as pd
import psycopg2
from datetime import datetime
import json
import sys


def load_config():
    """Load database configuration"""
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    return config["database"]


def update_reference(table_name: str, file_path: str, db_config: dict):
    """Update reference table from Excel file"""
    valid_tables = ["specializations", "skills", "regions", "companies"]
    
    if table_name not in valid_tables:
        print(f"Invalid table: {table_name}")
        print(f"   Valid tables: {', '.join(valid_tables)}")
        return False
        
    try:
        # Read Excel file
        df = pd.read_excel(file_path, header=0)
        print(f"Read {len(df)} rows from {file_path}")
        
        # Validate columns
        required_columns = {"title", "alias"}
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            print(f"Missing columns: {missing}")
            return False
            
        # Clean data
        df = df[["title", "alias"]].dropna()
        df = df[df["title"].str.strip() != ""]
        df = df[df["alias"].str.strip() != ""]
        print(f"After cleaning: {len(df)} rows")
        
        # Connect to database
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Insert data
        inserted = 0
        current_time = datetime.now()
        
        for _, row in df.iterrows():
            try:
                cursor.execute(
                    f"INSERT INTO {table_name} (title, alias, created_at) VALUES (%s, %s, %s)",
                    (row["title"], row["alias"], current_time)
                )
                inserted += 1
            except Exception as e:
                print(f"Warning: Error inserting {row['title']}: {e}")
                
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"Updated {table_name}: {inserted} records added")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Update reference tables from Excel files"
    )
    parser.add_argument(
        "table",
        choices=["specializations", "skills", "regions", "companies"],
        help="Reference table to update"
    )
    parser.add_argument(
        "file",
        help="Excel file with reference data (must have 'title' and 'alias' columns)"
    )
    
    args = parser.parse_args()
    
    db_config = load_config()
    success = update_reference(args.table, args.file, db_config)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 