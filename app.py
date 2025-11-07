from flask import Flask, request, jsonify, render_template, redirect, url_for
import sqlite3

app = Flask(__name__, template_folder='templates', static_folder='static')

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('cafe_inventory - Copy.db')
    conn.row_factory = sqlite3.Row
    return conn

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 产品相关路由
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('products.html', products=products)

@app.route('/products', methods=['POST'])
def add_product():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (category, product_name, description) VALUES (?, ?, ?)',
                   (data['category'], data['product_name'], data['description']))
    conn.commit()
    conn.close()
    return redirect(url_for('get_products'))

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET category = ?, product_name = ?, description = ? WHERE id = ?',
                   (data['category'], data['product_name'], data['description'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('get_products'))

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('get_products'))

# 库存相关路由
@app.route('/inventory', methods=['GET'])
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('inventory.html', inventory=inventory)

@app.route('/inventory', methods=['POST'])
def add_inventory():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (sku, standard_name, brand_name, unit, unit_cost, is_active) VALUES (?, ?, ?, ?, ?, ?)',
                   (data['sku'], data['standard_name'], data['brand_name'], data['unit'], data['unit_cost'], data['is_active']))
    conn.commit()
    conn.close()
    return redirect(url_for('get_inventory'))

@app.route('/inventory/<int:id>', methods=['PUT'])
def update_inventory(id):
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE inventory SET sku = ?, standard_name = ?, brand_name = ?, unit = ?, unit_cost = ?, is_active = ? WHERE id = ?',
                   (data['sku'], data['standard_name'], data['brand_name'], data['unit'], data['unit_cost'], data['is_active'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('get_inventory'))

@app.route('/inventory/<int:id>', methods=['DELETE'])
def delete_inventory(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('get_inventory'))

# 配方相关路由
@app.route('/recipes', methods=['GET'])
def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes')
    recipes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return render_template('recipes.html', recipes=recipes)

@app.route('/recipes', methods=['POST'])
def add_recipe():
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recipes (product_name, ingredient_sku, usage, unit) VALUES (?, ?, ?, ?)',
                   (data['product_name'], data['ingredient_sku'], data['usage'], data['unit']))
    conn.commit()
    conn.close()
    return redirect(url_for('get_recipes'))

@app.route('/recipes/<int:id>', methods=['PUT'])
def update_recipe(id):
    data = request.form
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE recipes SET product_name = ?, ingredient_sku = ?, usage = ?, unit = ? WHERE id = ?',
                   (data['product_name'], data['ingredient_sku'], data['usage'], data['unit'], id))
    conn.commit()
    conn.close()
    return redirect(url_for('get_recipes'))

@app.route('/recipes/<int:id>', methods=['DELETE'])
def delete_recipe(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('get_recipes'))

if __name__ == '__main__':
    app.run(debug=True)