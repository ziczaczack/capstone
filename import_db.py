import sqlite3
import pandas as pd

conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

# 注释掉建表
# with open('schema.sql', 'r', encoding='utf-8') as f:
#     cursor.executescript(f.read())

# 只导入数据
pd.read_csv('recipe.csv').to_sql('recipes', conn, if_exists='append', index=False)

conn.close()
print("数据库导入完成！")