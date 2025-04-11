import sys
import pandas as pd
import sqlite3

def load_csv_to_sqlite(csv_file, db_file="data.db", table_name="organization"):
    print("Loading CSV file...")
    try:
        df = pd.read_csv(csv_file, low_memory=False)
    except Exception as e:
        raise Exception(f"Error reading CSV file: {e}")
    
    print(f"CSV loaded successfully with {len(df)} rows and {len(df.columns)} columns.")

    # Remove any rows where any column contains "Data Masked" (case-insensitive)
    mask = df.apply(lambda row: any("data masked" in str(row[col]).lower() for col in df.columns), axis=1)
    df = df[~mask]
    print(f"After removing 'Data Masked' rows, {len(df)} rows remain.")

    print(f"Creating SQLite database '{db_file}' and table '{table_name}'...")
    try:
        conn = sqlite3.connect(db_file)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        conn.commit()
        print(f"Data loaded successfully into table '{table_name}' in database '{db_file}'.")
    except Exception as e:
        raise Exception(f"Error loading data into SQLite: {e}")
    finally:
        conn.close()

def load_aircraft_csv_to_sqlite(csv_file, db_file="data.db", table_name="aircraft"):
    """
    Read the filtered aircraft CSV and write it into SQLite.
    """
    df = pd.read_csv(csv_file, low_memory=False)
    conn = sqlite3.connect(db_file)
    # Replace the table if it already exists
    df.to_sql(table_name, conn, if_exists="replace", index=False)
    # Create an index on assigned_unit_pas for fast lookups
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_assigned_pas ON {table_name}(assigned_unit_pas)")
    conn.commit()
    conn.close()
    print(f"Loaded {len(df)} rows into '{table_name}' table in '{db_file}'.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python db.py <path_to_csv_file>")
        sys.exit(1)
    csv_file = sys.argv[1]
    load_csv_to_sqlite(csv_file)
