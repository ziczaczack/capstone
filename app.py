from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your_secret_key'  # 替换为随机密钥

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('cafe_inventory - Copy.db')
    conn.row_factory = sqlite3.Row
    return conn

# 用户类
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

# 加载用户
@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    if user_data:
        return User(user_data['id'], user_data['username'], user_data['role'])
    return None

# 角色检查装饰器
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied.')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return wrapped_view
    return decorator

# 登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user_data = cursor.fetchone()
        conn.close()
        if user_data and bcrypt.checkpw(password.encode('utf-8'), user_data['password'].encode('utf-8')):
            user = User(user_data['id'], user_data['username'], user_data['role'])
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid credentials.')
    return render_template('login.html')

# 注销路由
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 用户资料路由
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# 输入验证函数
def validate_required_fields(data, required_fields):
    missing = [field for field in required_fields if not data.get(field)]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"
    return True, None

def validate_numeric_field(value, field_name, allow_negative=False):
    try:
        num = float(value)
        if not allow_negative and num < 0:
            return False, f"{field_name} cannot be negative"
        return True, None
    except (ValueError, TypeError):
        return False, f"{field_name} must be a valid number"

# 首页
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 计算最低库存物品（前5个，基于 current_stock / 阈值 最小的）
    cursor.execute('''
        SELECT i.sku, i.standard_name, i.current_stock, i.threshold,
               (i.current_stock / i.threshold) as ratio
        FROM inventory i
        WHERE i.low_stock = 1
        ORDER BY ratio ASC
        LIMIT 5
    ''')
    low_inventory_items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('index.html', low_inventory_items=low_inventory_items)

@app.route('/register', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = bcrypt.hashpw(request.form['password'].encode('utf-8'), bcrypt.gensalt())
        role = request.form['role']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                       (username, password.decode('utf-8'), role))
        conn.commit()
        conn.close()
        flash('User registered.')
    return render_template('register.html')

# 产品相关路由
@app.route('/products', methods=['GET'])
@login_required
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products', methods=['POST'])
@login_required
@role_required('superadmin')
def add_product():
    data = request.form
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['category', 'product_name', 'description'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO products (category, product_name, description) VALUES (?, ?, ?)',
                       (data['category'], data['product_name'], data['description']))
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Insert failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/products/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_product(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # 调试
    try:
        cursor.execute('UPDATE products SET category = ?, product_name = ?, description = ? WHERE id = ?',
                      (data.get('category'), data.get('product_name'), data.get('description'), id))
        conn.commit()
        print(f"Updated product id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify({'message': 'Product updated'}), 200
    except sqlite3.Error as e:
        print(f"Update error: {e}")
        conn.rollback()
        return jsonify({'error': f'Update failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/products/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_product(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Attempting to delete product id {id}")  # 调试
    try:
        cursor.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        print(f"Deleted product id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Product not found'}), 404
        return jsonify({'message': 'Product deleted'}), 200
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        conn.rollback()
        return jsonify({'error': f'Delete failed: {e}'}), 400
    finally:
        conn.close()

# 库存相关路由
@app.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('inventory.html', inventory=inventory)

@app.route('/inventory/<int:id>', methods=['GET'])
@login_required
def get_inventory_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        return jsonify({'error': 'Inventory item not found'}), 404
    return jsonify(dict(item))

@app.route('/inventory', methods=['POST'])
@login_required
@role_required('superadmin')
def add_inventory():
    data = request.form
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['sku', 'standard_name', 'brand_name', 'current_stock', 'unit', 'unit_cost', 'is_active'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate numeric fields
    is_valid, error_msg = validate_numeric_field(data['current_stock'], 'current_stock')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    is_valid, error_msg = validate_numeric_field(data['unit_cost'], 'unit_cost')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO inventory (sku, standard_name, brand_name, current_stock, unit, unit_cost, is_active) VALUES (?, ?, ?, ?, ?, ?, ?)',
                       (data['sku'], data['standard_name'], data['brand_name'], int(float(data['current_stock'])), data['unit'], float(data['unit_cost']), int(data['is_active'])))
        conn.commit()
        return jsonify({'message': 'Inventory added successfully'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Insert failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/inventory/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_inventory(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # 调试
    try:
        cursor.execute('UPDATE inventory SET sku = ?, standard_name = ?, brand_name = ?, current_stock = ?, unit = ?, unit_cost = ?, is_active = ? WHERE id = ?',
                       (data.get('sku'), data.get('standard_name'), data.get('brand_name'), data.get('current_stock'), data.get('unit'), 
                        float(data.get('unit_cost', 0)), int(data.get('is_active', 0)), id))
        conn.commit()
        print(f"Updated inventory id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Inventory not found'}), 404
        return jsonify({'message': 'Inventory updated'}), 200
    except ValueError as ve:
        print(f"Value error: {ve}")  # 转换错误
        return jsonify({'error': f'Invalid data: {ve}'}), 400
    except sqlite3.Error as e:
        print(f"Update error: {e}")
        conn.rollback()
        return jsonify({'error': f'Update failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/inventory/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_inventory(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Attempting to delete inventory id {id}")  # 调试
    try:
        cursor.execute('DELETE FROM inventory WHERE id = ?', (id,))
        conn.commit()
        print(f"Deleted inventory id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Inventory item not found'}), 404
        return jsonify({'message': 'Inventory deleted'}), 200
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        conn.rollback()
        return jsonify({'error': f'Delete failed: {e}'}), 400
    finally:
        conn.close()

# 配方相关路由
@app.route('/recipes', methods=['GET'])
@login_required
def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes')
    recipes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('recipes.html', recipes=recipes)

@app.route('/recipes/<int:id>', methods=['GET'])
def get_recipes_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        return jsonify({'error': 'Recipe not found'}), 404
    return jsonify(dict(item))

@app.route('/recipes', methods=['POST'])
@login_required
@role_required('superadmin')
def add_recipe():
    data = request.form
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['product_name', 'ingredient_sku', 'usage', 'unit'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate numeric field
    is_valid, error_msg = validate_numeric_field(data['usage'], 'usage')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO recipes (product_name, ingredient_sku, usage, unit) VALUES (?, ?, ?, ?)',
                       (data['product_name'], data['ingredient_sku'], float(data['usage']), data['unit']))
        conn.commit()
        return jsonify({'message': 'Recipe added successfully'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Insert failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/recipes/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_recipe(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # 调试
    try:
        cursor.execute('UPDATE recipes SET product_name = ?, ingredient_sku = ?, usage = ?, unit = ? WHERE id = ?',
                       (data.get('product_name'), data.get('ingredient_sku'), 
                        float(data.get('usage', 0)), data.get('unit'), id))
        conn.commit()
        print(f"Updated recipe id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify({'message': 'Recipe updated'}), 200
    except ValueError as ve:
        print(f"Value error: {ve}")  # 转换错误
        return jsonify({'error': f'Invalid data: {ve}'}), 400
    except sqlite3.Error as e:
        print(f"Update error: {e}")
        conn.rollback()
        return jsonify({'error': f'Update failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/recipes/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_recipe(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Attempting to delete recipe id {id}")  # 调试
    try:
        cursor.execute('DELETE FROM recipes WHERE id = ?', (id,))
        conn.commit()
        print(f"Deleted recipe id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify({'message': 'Recipe deleted'}), 200
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        conn.rollback()
        return jsonify({'error': f'Delete failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/suppliers', methods=['GET'])
@login_required
def get_suppliers():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM suppliers')
    suppliers = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('suppliers.html', suppliers=suppliers)

@app.route('/suppliers/<int:id>', methods=['GET'])
def get_suppliers_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM suppliers WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        return jsonify({'error': 'Supplier not found'}), 404
    return jsonify(dict(item))

@app.route('/suppliers', methods=['POST'])
@login_required
@role_required('superadmin')
def add_supplier():
    data = request.form
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['company_name', 'contact_person', 'phone'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO suppliers (company_name, contact_person, phone) VALUES (?, ?, ?)',
                       (data['company_name'], data['contact_person'], data['phone']))
        conn.commit()
        return jsonify({'message': 'Supplier added successfully'}), 201
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Insert failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/suppliers/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_supplier(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # 调试
    try:
        cursor.execute('UPDATE suppliers SET company_name = ?, contact_person = ?, phone = ?, WHERE id = ?',
                       (data.get('company_name'), data.get('contact_person'), data.get('phone'), id))
        conn.commit()
        print(f"Updated recipe id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Supplier not found'}), 404
        return jsonify({'message': 'Supplier updated'}), 200
    except ValueError as ve:
        print(f"Value error: {ve}")  # 转换错误
        return jsonify({'error': f'Invalid data: {ve}'}), 400
    except sqlite3.Error as e:
        print(f"Update error: {e}")
        conn.rollback()
        return jsonify({'error': f'Update failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/suppliers/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_supplier(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Attempting to delete supplier id {id}")  # 调试
    try:
        cursor.execute('DELETE FROM suppliers WHERE id = ?', (id,))
        conn.commit()
        print(f"Deleted supplier id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Supplier not found'}), 404
        return jsonify({'message': 'Supplier deleted'}), 200
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        conn.rollback()
        return jsonify({'error': f'Delete failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/products/options', methods=['GET'])
@login_required
def get_product_options():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, product_name FROM products')
    options = [{'id': row['id'], 'name': row['product_name']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(options)

# 交易路由 (手动销售)
@app.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transactions ORDER BY sale_date DESC')
    transactions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('transactions.html', transactions=transactions)

@app.route('/transactions', methods=['POST'])
@login_required
def add_transaction():
    data = request.form
    try:
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
        selected_sku = data.get('selected_sku', '')  # 用户选择的具体 SKU
    except (ValueError, TypeError) as e:
        return jsonify({'error': f'Invalid input: {e}'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 验证产品是否存在
        cursor.execute('SELECT product_name FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 400

        # 获取产品可能的 ingredient_category
        cursor.execute('''
            SELECT ingredient_category 
            FROM recipes 
            WHERE product_name = (SELECT product_name FROM products WHERE id = ?) 
            LIMIT 1
        ''', (product_id,))
        category = cursor.fetchone()
        category = category[0] if category else None

        # 如果有 category，验证选定的 SKU
        if category and not selected_sku:
            return jsonify({'error': 'Please select a specific ingredient for this product'}), 400

        # 获取成本和库存
        cursor.execute('''
            SELECT i.standard_name, i.current_stock, i.unit_cost 
            FROM inventory i 
            WHERE i.sku = ? AND (? IS NULL OR i.category = ?)
        ''', (selected_sku if category else (cursor.execute('SELECT ingredient_sku FROM recipes WHERE product_name = ?', (product['product_name'],)).fetchone()[0] or ''), category, category))
        inventory_item = cursor.fetchone()
        if not inventory_item:
            return jsonify({'error': f'Inventory item not found for {selected_sku or "default SKU"}'}), 400
        name, current_stock, unit_cost = inventory_item

        # 计算扣减量
        cursor.execute('SELECT usage FROM recipes WHERE product_name = ?', (product['product_name'],))
        usage_per_unit = cursor.fetchone()[0] or 1.0  # 默认 1.0，如果 usage 缺失
        deduct = usage_per_unit * quantity

        # 检查库存
        if current_stock < deduct:
            return jsonify({'error': f'Insufficient stock for {name} - Needed: {deduct}, Available: {current_stock}'}), 400

        # 计算总成本 = unit_cost * usage_per_unit * quantity
        total_cost = unit_cost * usage_per_unit * quantity

        # 插入交易记录
        cursor.execute('INSERT INTO transactions (product_id, quantity, total_cost) VALUES (?, ?, ?)',
                       (product_id, quantity, total_cost))
        tx_id = cursor.lastrowid

        # 扣减库存
        cursor.execute('UPDATE inventory SET current_stock = current_stock - ? WHERE sku = ?', (deduct, selected_sku if category else (cursor.execute('SELECT ingredient_sku FROM recipes WHERE product_name = ?', (product['product_name'],)).fetchone()[0] or '')))

        conn.commit()
        return redirect(url_for('get_transactions'))
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Transaction error: {e}")
        return jsonify({'error': f'Transaction failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/inventory/options', methods=['GET'])
@login_required
def get_inventory_options():
    product_id = request.args.get('product_id')
    if not product_id:
        return jsonify({'category': None, 'items': []})
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT i.category, i.sku, i.standard_name 
        FROM inventory i 
        JOIN recipes r ON i.category = r.ingredient_category 
        WHERE r.product_name = (SELECT product_name FROM products WHERE id = ?) AND i.category IS NOT NULL
    ''', (product_id,))
    items = [dict(row) for row in cursor.fetchall()]
    category = items[0]['category'] if items else None
    conn.close()
    return jsonify({'category': category, 'items': items})

@app.route('/transactions/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_transaction(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Attempting to delete transaction id {id}")  # 调试
    try:
        cursor.execute('DELETE FROM transactions WHERE id = ?', (id,))
        conn.commit()
        print(f"Deleted transaction id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Transaction not found'}), 404
        return jsonify({'message': 'Transaction deleted'}), 200
    except sqlite3.Error as e:
        print(f"Delete error: {e}")
        conn.close()
        return jsonify({'error': f'Delete failed: {e}'}), 400

# 检查 low-stock 路由
@app.route('/check_low_stock', methods=['GET'])
def check_low_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 获取所有材料
    cursor.execute('SELECT sku, current_stock, threshold FROM inventory')
    for row in cursor.fetchall():
        sku = row[0]
        current_stock = row[1] or 0
        threshold = row[2] or 0  # 如果 threshold 未设，默认 0（可调整为继承逻辑）

        # 安全网：如果 threshold=0，根据 category 设置默认（可选，保留以防）
        if threshold == 0:
            cursor.execute('SELECT category FROM inventory WHERE sku = ?', (sku,))
            category = (cursor.fetchone()[0] or '').lower()
            if category == 'syrup':
                threshold = 600  # 你的自定义阈值
            elif category == 'chocolate':
                threshold = 600  # 同上
            # 更新 threshold 以存储
            cursor.execute('UPDATE inventory SET threshold = ? WHERE sku = ?', (threshold, sku))

        # 更新 low_stock
        low_stock = 1 if current_stock < threshold else 0
        cursor.execute('UPDATE inventory SET low_stock = ? WHERE sku = ?', (low_stock, sku))

        # 如果 low-stock，发送通知
        if low_stock:
            #send_low_stock_notification(sku, current_stock, threshold)
            print(f"Low stock alert for {sku}: Current Stock = {current_stock}, Threshold = {threshold}")

    conn.commit()
    conn.close()
    return jsonify({'message': 'Low stock check completed'})

scheduler = BackgroundScheduler()
scheduler.add_job(check_low_stock, 'interval', hours=1) 
scheduler.start()

if __name__ == '__main__':
    app.run(debug=True)