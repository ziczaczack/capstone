from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, make_response
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import sqlite3
import csv
import io
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import threading
import os
from werkzeug.utils import secure_filename
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
import bcrypt
from collections import defaultdict
from datetime import datetime, timedelta

app = Flask(__name__, template_folder='templates', static_folder='static')
app.secret_key = 'your_secret_key'  # Replace with a random secret key

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Database file path: can be overridden with the environment variable `DATABASE`.
# Default to `cafe_inventory.db` which exists in the workspace and contains the `users` table.
DATABASE = os.environ.get('DATABASE', 'cafe_inventory.db')

# Email Configuration (Replace with actual credentials or use environment variables)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = '' # CHANGE_ME
EMAIL_PASSWORD = '' # CHANGE_ME
EMAIL_FROM = EMAIL_USER
EMAIL_TO = '' # CHANGE_ME

def send_low_stock_email(product_name, current_stock, threshold):
    """Sends an email notification for low stock running in a separate thread."""
    def _send_email_thread(product_name, current_stock, threshold):
        subject = f"Low Stock Alert: {product_name}"
        body = f"""
        <html>
          <body>
            <h2>Low Stock Alert</h2>
            <p>The stock for <b>{product_name}</b> has dropped below the threshold.</p>
            <ul>
                <li><b>Current Stock:</b> {current_stock}</li>
                <li><b>Threshold:</b> {threshold}</li>
            </ul>
            <p>Please restock soon.</p>
          </body>
        </html>
        """
        msg = MIMEMultipart()
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        try:
            if 'your_email' in EMAIL_USER: # Prevent actual sending default dummy creds
                print(f"Mock Email Sent: {subject}")
                return

            server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            print(f"Email sent successfully for {product_name}")
        except Exception as e:
            print(f"Failed to send email: {e}")

    # Run in thread to not block the request
    threading.Thread(target=_send_email_thread, args=(product_name, current_stock, threshold)).start()

def check_and_alert_low_stock(cursor, sku=None, item_id=None):
    """Checks stock vs threshold for an item and sends email if low. 
    Updates low_stock flag in DB."""
    if sku:
        cursor.execute('SELECT id, sku, standard_name, current_stock, threshold, low_stock FROM inventory WHERE sku = ?', (sku,))
    elif item_id:
        cursor.execute('SELECT id, sku, standard_name, current_stock, threshold, low_stock FROM inventory WHERE id = ?', (item_id,))
    else:
        return

    item = cursor.fetchone()
    if item:
        current_stock = item['current_stock']
        threshold = item['threshold'] if item['threshold'] is not None else 10
        item_id = item['id']
        
        if current_stock < threshold:
            cursor.execute('UPDATE inventory SET low_stock = 1 WHERE id = ?', (item_id,))
            send_low_stock_email(item['standard_name'], current_stock, threshold)
        else:
            cursor.execute('UPDATE inventory SET low_stock = 0 WHERE id = ?', (item_id,))

@app.route('/check_alerts')
@login_required
def check_all_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get all active inventory
    cursor.execute('SELECT id FROM inventory WHERE is_active = 1')
    items = cursor.fetchall()
    
    count = 0
    for item in items:
        check_and_alert_low_stock(cursor, item_id=item['id'])
        count += 1
        
    conn.commit()
    conn.close()
    flash(f"Checked {count} items for low stock. Emails sent where necessary.")
    return redirect(url_for('index'))




# Database connection function
def get_db_connection():
    # Use the configured DATABASE path
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# User class
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role

# Load user
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

# Role check decorator
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

# Login route
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

# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# User profile route
@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

# Input validation function
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

# Home page
@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Calculate lowest inventory items (top 5, based on lowest current_stock / threshold ratio)
    cursor.execute('''
        SELECT i.sku, i.standard_name, i.current_stock, i.threshold,
               (i.current_stock / i.threshold) as ratio
        FROM inventory i
        WHERE i.low_stock = 1
        ORDER BY ratio ASC
        LIMIT 5
    ''')
    low_inventory_items = [dict(row) for row in cursor.fetchall()]

    # Inventory summary by category
    cursor.execute('SELECT category, SUM(current_stock) AS total_stock FROM inventory GROUP BY category')
    inv_by_category = [dict(row) for row in cursor.fetchall()]

    # Sales trend for last 30 days
    cursor.execute("""
        SELECT date(sale_date) AS day, SUM(quantity) AS sold
        FROM transactions
        WHERE sale_date >= date('now', '-30 days')
        GROUP BY day
        ORDER BY day
    """)
    sales_trend = [dict(row) for row in cursor.fetchall()]

    # Inventory value by category
    cursor.execute('SELECT category, SUM(current_stock * unit_cost) AS value FROM inventory GROUP BY category')
    value_by_category = [dict(row) for row in cursor.fetchall()]

    # Top selling products (up to 10)
    cursor.execute('''
        SELECT p.product_name, SUM(t.quantity) AS sold
        FROM transactions t
        JOIN products p ON t.product_id = p.id
        GROUP BY p.product_name
        ORDER BY sold DESC
        LIMIT 10
    ''')
    top_sellers = [dict(row) for row in cursor.fetchall()]

    conn.close()
    return render_template('index.html', 
                           low_inventory_items=low_inventory_items,
                           inv_by_category=inv_by_category,
                           sales_trend=sales_trend,
                           value_by_category=value_by_category,
                           top_sellers=top_sellers)

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

# User management routes (superadmin only)
@app.route('/users', methods=['GET'])
@login_required
@role_required('superadmin')
def get_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role FROM users')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('users.html', users=users)

@app.route('/users/<int:id>', methods=['GET'])
@login_required
@role_required('superadmin')
def get_user_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, role FROM users WHERE id = ?', (id,))
    user = cursor.fetchone()
    conn.close()
    if user is None:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(user))

@app.route('/users/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_user(id):
    data = request.form
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id FROM users WHERE id = ?', (id,))
    if cursor.fetchone() is None:
        conn.close()
        return jsonify({'error': 'User not found'}), 404
    
    try:
        # Update username and role
        username = data.get('username')
        role = data.get('role')
        password = data.get('password')
        
        if password:
            # If password is provided, update it as well
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('UPDATE users SET username = ?, role = ?, password = ? WHERE id = ?',
                          (username, role, hashed_password.decode('utf-8'), id))
        else:
            # Only update username and role
            cursor.execute('UPDATE users SET username = ?, role = ? WHERE id = ?',
                          (username, role, id))
        
        conn.commit()
        return jsonify({'message': 'User updated successfully'}), 200
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'error': 'Username already exists'}), 400
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Update failed: {e}'}), 400
    finally:
        conn.close()

@app.route('/users/<int:id>', methods=['DELETE'])
@login_required
@role_required('superadmin')
def delete_user(id):
    # Prevent deleting yourself
    if current_user.id == id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    
    try:
        cursor.execute('DELETE FROM users WHERE id = ?', (id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'}), 200
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'error': f'Delete failed: {e}'}), 400
    finally:
        conn.close()

# Product-related routes
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

@app.route('/products/<int:id>', methods=['GET'])
@login_required
def get_product_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = cursor.fetchone()
    conn.close()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))

@app.route('/products/<int:id>', methods=['PUT'])
@login_required
@role_required('superadmin')
def update_product(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # Debug
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
    print(f"Attempting to delete product id {id}")  # Debug
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

# Inventory-related routes
@app.route('/inventory', methods=['GET'])
@login_required
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get filter parameters
    search_sku = request.args.get('search_sku', '').strip()
    search_name = request.args.get('search_name', '').strip()
    filter_category = request.args.get('filter_category', '').strip()
    filter_status = request.args.get('filter_status', '').strip()
    filter_stock_status = request.args.get('filter_stock_status', '').strip()
    min_stock = request.args.get('min_stock', '').strip()
    max_stock = request.args.get('max_stock', '').strip()
    
    # Build query with filters
    query = 'SELECT * FROM inventory WHERE 1=1'
    params = []
    
    if search_sku:
        query += ' AND sku LIKE ?'
        params.append(f'%{search_sku}%')
    
    if search_name:
        query += ' AND (standard_name LIKE ? OR brand_name LIKE ?)'
        params.extend([f'%{search_name}%', f'%{search_name}%'])
    
    if filter_category:
        query += ' AND category = ?'
        params.append(filter_category)
    
    if filter_status in ['0', '1']:
        query += ' AND is_active = ?'
        params.append(int(filter_status))
    
    if filter_stock_status == 'low':
        query += ' AND low_stock = 1'
    elif filter_stock_status == 'normal':
        query += ' AND low_stock = 0'
    
    if min_stock:
        try:
            query += ' AND current_stock >= ?'
            params.append(int(min_stock))
        except ValueError:
            pass
    
    if max_stock:
        try:
            query += ' AND current_stock <= ?'
            params.append(int(max_stock))
        except ValueError:
            pass
    
    query += ' ORDER BY id'
    cursor.execute(query, params)
    inventory = [dict(row) for row in cursor.fetchall()]
    
    # Get categories for dropdown
    cursor.execute('SELECT DISTINCT category FROM inventory WHERE category IS NOT NULL ORDER BY category')
    categories = [row['category'] for row in cursor.fetchall()]
    
    conn.close()
    return render_template('inventory.html', inventory=inventory, categories=categories, 
                         filters={
                             'search_sku': search_sku,
                             'search_name': search_name,
                             'filter_category': filter_category,
                             'filter_status': filter_status,
                             'filter_stock_status': filter_stock_status,
                             'min_stock': min_stock,
                             'max_stock': max_stock
                         })

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
        cursor.execute('INSERT INTO inventory (sku, standard_name, brand_name, current_stock, unit, unit_cost, is_active, threshold, low_stock) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                       (data['sku'], data['standard_name'], data['brand_name'], int(float(data['current_stock'])), data['unit'], float(data['unit_cost']), int(data['is_active']), int(data.get('threshold', 10)), 0))
        
        # Check for low stock immediately on add (unlikely but possible if added with 0 stock)
        current_stk = int(float(data['current_stock']))
        thresh = int(data.get('threshold', 10))
        if current_stk < thresh:
             cursor.execute('UPDATE inventory SET low_stock = 1 WHERE sku = ?', (data['sku'],))
             send_low_stock_email(data['standard_name'], current_stk, thresh)
    

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
    data = request.form
    
    # Validate numeric fields
    is_valid, error_msg = validate_numeric_field(data.get('current_stock', 0), 'current_stock')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    is_valid, error_msg = validate_numeric_field(data.get('unit_cost', 0), 'unit_cost')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE inventory SET sku = ?, standard_name = ?, brand_name = ?, current_stock = ?, unit = ?, supplier_id = ?, unit_cost = ?, is_active = ?, threshold = ? WHERE id = ?',
                       (data.get('sku'), data.get('standard_name'), data.get('brand_name'), int(float(data.get('current_stock', 0))), data.get('unit'), 
                        int(data.get('supplier_id', 0)), float(data.get('unit_cost', 0)), int(data.get('is_active', 0)), int(data.get('threshold', 10)), id))
        
        # Check low stock Logic via Helper
        check_and_alert_low_stock(cursor, item_id=id)

        conn.commit()
        print(f"Updated inventory id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Inventory not found'}), 404
        return jsonify({'message': 'Inventory updated'}), 200
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
    print(f"Attempting to delete inventory id {id}")  # Debug
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

# Recipe-related routes
@app.route('/recipes', methods=['GET'])
@login_required
def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get search parameter
    search_product = request.args.get('search_product', '').strip()
    
    if search_product:
        cursor.execute('SELECT * FROM recipes WHERE product_name LIKE ?', (f'%{search_product}%',))
    else:
        cursor.execute('SELECT * FROM recipes')

    recipes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('recipes.html', recipes=recipes)

@app.route('/recipes/<int:id>', methods=['GET'])
@login_required
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
    data = request.form
    
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['product_name', 'ingredient_sku', 'usage', 'unit'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    # Validate numeric field
    is_valid, error_msg = validate_numeric_field(data.get('usage', 0), 'usage')
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Received data for update id {id}: {data}")  # Debug
    try:
        cursor.execute('UPDATE recipes SET product_name = ?, ingredient_sku = ?, usage = ?, unit = ? WHERE id = ?',
                       (data.get('product_name'), data.get('ingredient_sku'), 
                        float(data.get('usage', 0)), data.get('unit'), id))
        conn.commit()
        print(f"Updated recipe id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Recipe not found'}), 404
        return jsonify({'message': 'Recipe updated'}), 200
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
    print(f"Attempting to delete recipe id {id}")  # Debug
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
@login_required
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
    data = request.form
    
    # Validate required fields
    is_valid, error_msg = validate_required_fields(data, ['company_name', 'contact_person', 'phone'])
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    print(f"Received data for update id {id}: {data}")  # Debug
    try:
        cursor.execute('UPDATE suppliers SET company_name = ?, contact_person = ?, phone = ? WHERE id = ?',
                       (data.get('company_name'), data.get('contact_person'), data.get('phone'), id))
        conn.commit()
        print(f"Updated supplier id {id} successfully")
        if cursor.rowcount == 0:
            return jsonify({'error': 'Supplier not found'}), 404
        return jsonify({'message': 'Supplier updated'}), 200
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
    print(f"Attempting to delete supplier id {id}")  # Debug
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

# Transaction routes (manual sales)
@app.route('/transactions', methods=['GET'])
@login_required
def get_transactions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get filter parameters
    search_product = request.args.get('search_product', '').strip()
    date_from = request.args.get('date_from', '').strip()
    date_to = request.args.get('date_to', '').strip()
    min_cost = request.args.get('min_cost', '').strip()
    max_cost = request.args.get('max_cost', '').strip()
    min_qty = request.args.get('min_qty', '').strip()
    max_qty = request.args.get('max_qty', '').strip()
    
    # Build query with filters
    query = '''
        SELECT t.id, t.product_id, p.product_name, t.quantity, t.total_cost, t.sale_date, t.status
        FROM transactions t
        LEFT JOIN products p ON t.product_id = p.id
        WHERE 1=1
    '''
    params = []
    
    if search_product:
        query += ' AND p.product_name LIKE ?'
        params.append(f'%{search_product}%')
    
    if date_from:
        query += ' AND t.sale_date >= ?'
        params.append(date_from)
    
    if date_to:
        query += ' AND t.sale_date <= ?'
        params.append(date_to)
    
    if min_cost:
        try:
            query += ' AND t.total_cost >= ?'
            params.append(float(min_cost))
        except ValueError:
            pass
    
    if max_cost:
        try:
            query += ' AND t.total_cost <= ?'
            params.append(float(max_cost))
        except ValueError:
            pass
    
    if min_qty:
        try:
            query += ' AND t.quantity >= ?'
            params.append(int(min_qty))
        except ValueError:
            pass
    
    if max_qty:
        try:
            query += ' AND t.quantity <= ?'
            params.append(int(max_qty))
        except ValueError:
            pass
    
    query += ' ORDER BY t.sale_date DESC'
    cursor.execute(query, params)
    transactions = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return render_template('transactions.html', transactions=transactions,
        filters={
                'search_product': search_product,
                'date_from': date_from,
                'date_to': date_to,
                'min_cost': min_cost,
                'max_cost': max_cost,
                'min_qty': min_qty,
                'max_qty': max_qty
            })

@app.route('/transactions', methods=['POST'])
@login_required
def add_transaction():
    conn = None
    try:
        data = request.form
        try:
            product_id = int(data['product_id'])
            quantity = int(data['quantity'])
            selected_sku = data.get('selected_sku', '')
        except (ValueError, TypeError) as e:
            return jsonify({'error': f'Invalid input: {e}'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Verify Product
        cursor.execute('SELECT product_name FROM products WHERE id = ?', (product_id,))
        product = cursor.fetchone()
        if not product:
            return jsonify({'error': 'Product not found'}), 400
        product_name = product['product_name']

        # 2. Get ALL Recipes for this product
        cursor.execute('SELECT ingredient_sku, usage, ingredient_category FROM recipes WHERE product_name = ?', (product_name,))
        recipes = cursor.fetchall()
        
        if not recipes:
             return jsonify({'error': f'No recipe found for product: {product_name}'}), 400

        # 3. Validation Phase: Check ALL ingredients
        deductions = [] # List of (sku, amount_to_deduct)
        total_cost = 0.0

        for r in recipes:
            target_sku = r['ingredient_sku']
            category = r['ingredient_category']
            usage = r['usage']

            # Dynamic Ingredient Logic (
            if category and not target_sku:
                if not selected_sku:
                     return jsonify({'error': f'Product requires a choice from category "{category}". Please select an ingredient.'}), 400
                target_sku = selected_sku
            
            # Check Inventory for this specific ingredient
            cursor.execute('SELECT standard_name, current_stock, unit_cost, category FROM inventory WHERE sku = ?', (target_sku,))
            inv_item = cursor.fetchone()
            
            if not inv_item:
                return jsonify({'error': f'Ingredient not found in inventory: {target_sku}'}), 400
            
            # Verify category match for dynamic selection
            if category and inv_item['category'] != category:
                return jsonify({'error': f'Selected item {target_sku} is not in category {category}'}), 400

            needed = usage * quantity
            if inv_item['current_stock'] < needed:
                return jsonify({'error': f'Insufficient stock for {inv_item["standard_name"]}. Needed: {needed}, Available: {inv_item["current_stock"]}'}), 400
            
            deductions.append((target_sku, needed))
            total_cost += (inv_item['unit_cost'] * needed)

        #Execution Phase: Deduct Stock and Record Transaction
        for sku, amount in deductions:
            cursor.execute('UPDATE inventory SET current_stock = current_stock - ? WHERE sku = ?', (amount, sku))
            
            # Check for low stock after deduction
            check_and_alert_low_stock(cursor, sku=sku)


        cursor.execute('INSERT INTO transactions (product_id, quantity, total_cost, status, sale_date) VALUES (?, ?, ?, ?, ?)',
                       (product_id, quantity, total_cost, 'completed', datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        conn.commit()
        return redirect(url_for('get_transactions'))

    except sqlite3.Error as e:
        if conn: conn.rollback()
        return jsonify({'error': f'Transaction failed: {e}'}), 400
    finally:
        if conn: conn.close()

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
    print(f"Attempting to delete transaction id {id}")  # Debug
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


@app.route('/transactions/<int:id>', methods=['GET'])
@login_required
def get_transaction_by_id(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT t.id, t.product_id, p.product_name, t.quantity, t.total_cost, t.sale_date, t.status
        FROM transactions t
        LEFT JOIN products p ON t.product_id = p.id
        WHERE t.id = ?
    ''', (id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        return jsonify({'error': 'Transaction not found'}), 404
    return jsonify(dict(item))

# Check low-stock route
@app.route('/check_low_stock', methods=['GET'])
def check_low_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all ingredients
    cursor.execute('SELECT sku, current_stock, threshold FROM inventory')
    for row in cursor.fetchall():
        sku = row[0]
        current_stock = row[1] or 0
        threshold = row[2] or 0  # If threshold not set, default to 0 (can be adjusted for inheritance logic)

        # Safety net: If threshold=0, set default based on category (optional, kept as backup)
        if threshold == 0:
            cursor.execute('SELECT category FROM inventory WHERE sku = ?', (sku,))
            category = (cursor.fetchone()[0] or '').lower()
            if category == 'syrup':
                threshold = 600  
            elif category == 'chocolate':
                threshold = 600  
            # Update threshold for storage
            cursor.execute('UPDATE inventory SET threshold = ? WHERE sku = ?', (threshold, sku))

        # Update low_stock
        low_stock = 1 if current_stock < threshold else 0
        cursor.execute('UPDATE inventory SET low_stock = ? WHERE sku = ?', (low_stock, sku))

        # If low-stock, send notification
        if low_stock:
            print(f"Low stock alert for {sku}: Current Stock = {current_stock}, Threshold = {threshold}")

    conn.commit()
    conn.close()
    return jsonify({'message': 'Low stock check completed'})

scheduler = BackgroundScheduler()
scheduler.add_job(check_low_stock, 'interval', hours=1) 
scheduler.start()


# Allowed tables for CSV import/export to avoid SQL injection
ALLOWED_TABLES = {'inventory', 'products', 'recipes', 'suppliers', 'transactions'}


def get_table_columns(table):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    cols = [row['name'] for row in cursor.fetchall()]
    conn.close()
    return cols


#Forecast: simple moving-average based inventory forecast
def forecast_inventory(window_days=30, top_n=50):
    conn = get_db_connection()
    cursor = conn.cursor()

    # aggregate product-level daily sales over the window
    since_date = (datetime.utcnow() - timedelta(days=window_days)).strftime('%Y-%m-%d')
    cursor.execute('''
        SELECT t.product_id, date(t.sale_date) AS day, SUM(t.quantity) AS qty
        FROM transactions t
        WHERE date(t.sale_date) >= ?
        GROUP BY t.product_id, day
    ''', (since_date,))

    rows = cursor.fetchall()

    # accumulate totals per product across the window
    prod_totals = defaultdict(float)
    for r in rows:
        pid = r['product_id']
        prod_totals[pid] += (r['qty'] or 0.0)

    # average per day per product (spread over full window to smooth)
    prod_avg_per_day = {pid: total / float(window_days) for pid, total in prod_totals.items()}

    # map product -> recipe ingredients and compute ingredient-level avg daily usage
    ingredient_usage = defaultdict(float)  # sku -> avg daily units consumed
    for pid, avg_per_day in prod_avg_per_day.items():
        cursor.execute('SELECT product_name FROM products WHERE id = ?', (pid,))
        p = cursor.fetchone()
        product_name = p['product_name'] if p else None
        if not product_name:
            continue
        cursor.execute('SELECT ingredient_sku, usage FROM recipes WHERE product_name = ?', (product_name,))
        recs = cursor.fetchall()
        if not recs:
            continue
        for rec in recs:
            sku = rec['ingredient_sku']
            try:
                usage_per_unit = float(rec['usage'] or 0)
            except Exception:
                usage_per_unit = 0.0
            ingredient_usage[sku] += avg_per_day * usage_per_unit

    # build results list using inventory current_stock when available
    results = []
    for sku, avg_daily in ingredient_usage.items():
        cursor.execute('SELECT * FROM inventory WHERE sku = ?', (sku,))
        inv = cursor.fetchone()
        name = inv['standard_name'] if inv and 'standard_name' in inv.keys() else sku
        current_stock = inv['current_stock'] if inv and 'current_stock' in inv.keys() else None
        days_until = None
        if current_stock is not None and avg_daily > 0:
            days_until = round(current_stock / avg_daily, 1)
        results.append({
            'sku': sku,
            'name': name,
            'avg_daily_usage': round(avg_daily, 4),
            'current_stock': current_stock,
            'days_until_stockout': days_until
        })

    conn.close()

    # sort by days_until_stockout asc (None placed at end)
    results.sort(key=lambda x: (x['days_until_stockout'] is None, x['days_until_stockout']))
    return {'window_days': window_days, 'items': results[:top_n]}


@app.route('/forecast', methods=['GET'])
@login_required
def forecast_route():
    try:
        w = int(request.args.get('window', 30))
    except Exception:
        w = 30
    data = forecast_inventory(window_days=w)
    return jsonify(data)

@app.route('/suppliers/<int:supplier_id>/inventory', methods=['GET'])
@login_required
def get_supplier_inventory(supplier_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, sku, standard_name, brand_name, current_stock, unit, unit_cost, is_active
        FROM inventory
        WHERE supplier_id = ?
        ORDER BY standard_name
    ''', (supplier_id,))
    items = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(items)

@app.route('/export', methods=['GET'])
@login_required
def export_csv():
    table = request.args.get('table', 'inventory')
    if table not in ALLOWED_TABLES:
        return jsonify({'error': 'Table not allowed for export'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'SELECT * FROM {table}')
        rows = cursor.fetchall()

        # column names
        if rows:
            columns = rows[0].keys()
        else:
            columns = [d[0] for d in cursor.description] if cursor.description else []

        si = io.StringIO()
        writer = csv.writer(si)
        writer.writerow(columns)
        for r in rows:
            writer.writerow([r[c] for c in columns])

        output = make_response(si.getvalue())
        output.headers['Content-Disposition'] = f'attachment; filename={table}.csv'
        output.headers['Content-Type'] = 'text/csv; charset=utf-8'
        return output
    except sqlite3.Error as e:
        return jsonify({'error': f'Export failed: {e}'}), 500
    finally:
        conn.close()

@app.route('/export/forecast', methods=['GET'])
@login_required
def export_forecast():
    # Get forecast data (default 30 days, top 1000 items)
    data = forecast_inventory(window_days=30, top_n=1000)
    items = data['items']
    
    si = io.StringIO()
    writer = csv.writer(si)
    # Write Header
    writer.writerow(['SKU', 'Name', 'Avg Daily Usage', 'Current Stock', 'Days Until Stockout'])
    
    # Write Data
    for item in items:
        writer.writerow([
            item['sku'],
            item['name'],
            item['avg_daily_usage'],
            item['current_stock'],
            item['days_until_stockout'] if item['days_until_stockout'] is not None else 'N/A'
        ])
        
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = 'attachment; filename=forecast_at_risk.csv'
    output.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return output
    
@app.route('/import', methods=['GET', 'POST'])
@login_required
@role_required('superadmin')
def import_csv():
    if request.method == 'GET':
        return render_template('import.html')

    # POST: handle file upload
    table = request.form.get('table')
    if not table or table not in ALLOWED_TABLES:
        return jsonify({'error': 'Table not allowed for import'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    try:
        data = file.read()
        # Support UTF-8 with BOM
        s = data.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(s))
    except Exception as e:
        return jsonify({'error': f'Failed to read CSV: {e}'}), 400

    cols = get_table_columns(table)
    if not cols:
        return jsonify({'error': f'Could not read columns for table {table}'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    inserted = 0
    failed = 0
    errors = []
    try:
        for i, row in enumerate(reader, start=1):
            # Filter to columns that exist in table and have values
            filtered = {k: v for k, v in row.items() if k in cols and v != '' and v is not None}
            if not filtered:
                continue
            columns_sql = ','.join(filtered.keys())
            placeholders = ','.join(['?'] * len(filtered))
            values = list(filtered.values())
            try:
                cursor.execute(f'INSERT OR REPLACE INTO {table} ({columns_sql}) VALUES ({placeholders})', values)
                inserted += 1
            except sqlite3.IntegrityError as ie:
                failed += 1
                errors.append({'row': i, 'error': str(ie)})
            except sqlite3.Error as e:
                failed += 1
                errors.append({'row': i, 'error': str(e)})

        conn.commit()
        return jsonify({'message': 'Import completed', 'inserted': inserted, 'failed': failed, 'errors': errors}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'error': f'Import failed: {e}'}), 500
    finally:
        conn.close()

@app.route('/import/template', methods=['GET'])
@login_required
@role_required('superadmin')
def download_template():
    table = request.args.get('table')
    if not table or table not in ALLOWED_TABLES:
        return jsonify({'error': 'Invalid table'}), 400
    
    cols = get_table_columns(table)
    
    si = io.StringIO()
    writer = csv.writer(si)
    writer.writerow(cols)  # Write only headers
    
    output = make_response(si.getvalue())
    output.headers['Content-Disposition'] = f'attachment; filename={table}_template.csv'
    output.headers['Content-Type'] = 'text/csv; charset=utf-8'
    return output

if __name__ == '__main__':
    app.run(debug=True)
