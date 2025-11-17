import sqlite3
import bcrypt

conn = sqlite3.connect('cafe_inventory - Copy.db')
cursor = conn.cursor()

username = 'SuperAdmin'
password = 'Admin@@123' 
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
role = 'superadmin'

cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', (username, hashed, role))
conn.commit()
conn.close()
print("User added!")