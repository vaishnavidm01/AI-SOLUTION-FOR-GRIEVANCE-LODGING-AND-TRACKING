import sqlite3

conn = sqlite3.connect("database/grievances.db")
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

print("\n===== TABLES =====")

for table in tables:
    print("\nTable:", table[0])

    cursor.execute(f'SELECT * FROM "{table[0]}"')
    rows = cursor.fetchall()

    print("Records:")

    for row in rows:
        print(row)

conn.close()