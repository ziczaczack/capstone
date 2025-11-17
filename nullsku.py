import sqlite3

# 连接数据库
conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# 将 ingredient_sku 为空白或无效的值更新为 NULL
cursor.execute("UPDATE recipes SET ingredient_sku = NULL WHERE ingredient_sku = '' OR ingredient_sku IS NULL")

# 提交更改
conn.commit()
conn.close()

print("ingredient_sku 已更新为 NULL！")