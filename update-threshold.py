import sqlite3

conn = sqlite3.connect('cafe_inventory - Copy.db')  # 替换为你的数据库路径
cursor = conn.cursor()

cursor.execute("""
    UPDATE inventory 
    SET threshold = 600 
    WHERE category IN ('Flavour Syrup', 'SO Chocolate') 
    AND threshold = 0.0;
""")

updated_count = cursor.rowcount
conn.commit()
conn.close()

print(f"Updated {updated_count} records!")