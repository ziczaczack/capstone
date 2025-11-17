import sqlite3

# 连接数据库
conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# 计算每种原料的总用量
cursor.execute('''
    SELECT i.sku, SUM(r.usage * 50) as total_usage
    FROM inventory i
    LEFT JOIN recipes r ON i.sku = r.ingredient_sku
    GROUP BY i.sku
''')
results = cursor.fetchall()

# 更新 current_stock
for sku, total_usage in results:
    if total_usage is None:
        total_usage = 0.0  # 如果没有配方使用，设为 0
    cursor.execute('UPDATE inventory SET current_stock = ? WHERE sku = ?', (total_usage, sku))

# 提交更改
conn.commit()
conn.close()

print("Inventory current_stock updated successfully!")