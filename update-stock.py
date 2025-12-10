import sqlite3

# Connect to database
conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# Calculate total usage of each ingredient
cursor.execute('''
    SELECT i.sku, SUM(r.usage * 50) as total_usage
    FROM inventory i
    LEFT JOIN recipes r ON i.sku = r.ingredient_sku
    GROUP BY i.sku
''')
results = cursor.fetchall()

# Update current_stock
for sku, total_usage in results:
    if total_usage is None:
        total_usage = 0.0  # If no recipe uses it, set to 0
    cursor.execute('UPDATE inventory SET current_stock = ? WHERE sku = ?', (total_usage, sku))

# Commit changes
conn.commit()
conn.close()

print("Inventory current_stock updated successfully!")