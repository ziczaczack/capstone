from flask import Flask, request, jsonify
import sqlite3

app = Flask(__name__)

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('cafe_inventory - Copy.db')
    conn.row_factory = sqlite3.Row  # 返回字典格式
    return conn

# 产品相关路由
@app.route('/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products')
    products = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(products)

@app.route('/products/<int:id>', methods=['GET'])
def get_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE id = ?', (id,))
    product = cursor.fetchone()
    conn.close()
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    return jsonify(dict(product))

@app.route('/products', methods=['POST'])
def add_product():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO products (category, product_name, description) VALUES (?, ?, ?)',
                   (data['category'], data['product_name'], data['description']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product added', 'id': cursor.lastrowid}), 201

@app.route('/products/<int:id>', methods=['PUT'])
def update_product(id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE products SET category = ?, product_name = ?, description = ? WHERE id = ?',
                   (data['category'], data['product_name'], data['description'], id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product updated'})

@app.route('/products/<int:id>', methods=['DELETE'])
def delete_product(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted'})

# 库存相关路由
@app.route('/inventory', methods=['GET'])
def get_inventory():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory')
    inventory = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(inventory)

@app.route('/inventory/<int:id>', methods=['GET'])
def get_inventory_item(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM inventory WHERE id = ?', (id,))
    item = cursor.fetchone()
    conn.close()
    if item is None:
        return jsonify({'error': 'Inventory item not found'}), 404
    return jsonify(dict(item))

@app.route('/inventory', methods=['POST'])
def add_inventory():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO inventory (sku, standard_name, brand_name, unit, unit_cost, is_active, supplier_id) VALUES (?, ?, ?, ?, ?, ?, ?)',
                   (data['sku'], data['standard_name'], data['brand_name'], data['unit'], data['unit_cost'], data['is_active'], data.get('supplier_id')))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Inventory added', 'id': cursor.lastrowid}), 201

@app.route('/inventory/<int:id>', methods=['PUT'])
def update_inventory(id):
    conn = get_db_connection()
    if conn is None:
        return jsonify({'error': 'Database connection failed'}), 500
    cursor = conn.cursor()
    data = request.form
    print(f"Received data for update id {id}: {data}")  # 调试
    try:
        cursor.execute('UPDATE inventory SET sku = ?, standard_name = ?, brand_name = ?, unit = ?, unit_cost = ?, is_active = ? WHERE id = ?',
                       (data.get('sku'), data.get('standard_name'), data.get('brand_name'), data.get('unit'), 
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
        conn.close(

@app.route('/inventory/<int:id>', methods=['DELETE'])
def delete_inventory(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM inventory WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Inventory deleted'})

# 配方相关路由
@app.route('/recipes', methods=['GET'])
def get_recipes():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes')
    recipes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return jsonify(recipes)

@app.route('/recipes/<int:id>', methods=['GET'])
def get_recipe(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM recipes WHERE id = ?', (id,))
    recipe = cursor.fetchone()
    conn.close()
    if recipe is None:
        return jsonify({'error': 'Recipe not found'}), 404
    return jsonify(dict(recipe))

@app.route('/recipes', methods=['POST'])
def add_recipe():
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO recipes (product_name, ingredient_sku, usage, unit) VALUES (?, ?, ?, ?)',
                   (data['product_name'], data['ingredient_sku'], data['usage'], data['unit']))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Recipe added', 'id': cursor.lastrowid}), 201

@app.route('/recipes/<int:id>', methods=['PUT'])
def update_recipe(id):
    data = request.get_json()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE recipes SET product_name = ?, ingredient_sku = ?, usage = ?, unit = ? WHERE id = ?',
                   (data['product_name'], data['ingredient_sku'], data['usage'], data['unit'], id))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Recipe updated'})

@app.route('/recipes/<int:id>', methods=['DELETE'])
def delete_recipe(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM recipes WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Recipe deleted'})

if __name__ == '__main__':
    app.run(debug=True)