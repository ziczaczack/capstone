import sqlite3

# Connect to database
conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# Update ingredient_sku values that are blank or invalid to NULL
cursor.execute("UPDATE recipes SET ingredient_sku = NULL WHERE ingredient_sku = '' OR ingredient_sku IS NULL")

# Commit changes
conn.commit()
conn.close()

print("ingredient_sku has been updated to NULL!")