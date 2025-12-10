import sqlite3
import pandas as pd

conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# Commented out table creation
# with open('schema.sql', 'r', encoding='utf-8') as f:
#     cursor.executescript(f.read())

# Only import data
pd.read_csv('suppliers.csv').to_sql('suppliers', conn, if_exists='append', index=False)

conn.close()
print("Database import completed!")