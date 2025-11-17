import bcrypt
password = 'Admin@@123'  # 替换你的密码
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))  # 复制输出