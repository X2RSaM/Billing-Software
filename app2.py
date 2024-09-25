from flask import Flask, request, jsonify
import sqlite3
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('billing_software.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (id INTEGER PRIMARY KEY, name TEXT, gender TEXT, contact TEXT, email TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER, brand TEXT,
                  supplier TEXT, old_stock INTEGER, category TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS bills
                 (id INTEGER PRIMARY KEY, customer_id INTEGER, total REAL,
                  FOREIGN KEY (customer_id) REFERENCES customers (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS bill_items
                 (id INTEGER PRIMARY KEY, bill_id INTEGER, product_id INTEGER, quantity INTEGER,
                  FOREIGN KEY (bill_id) REFERENCES bills (id),
                  FOREIGN KEY (product_id) REFERENCES products (id))''')
    conn.commit()
    conn.close()

init_db()

# Helper function to convert row to dictionary
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

# --------------------------- CUSTOMER ROUTES ---------------------------
@app.route('/customers', methods=['GET', 'POST'])
def customers():
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('SELECT * FROM customers')
        customers = c.fetchall()
        return jsonify(customers)

    elif request.method == 'POST':
        data = request.json
        c.execute('INSERT INTO customers (name, gender, contact, email) VALUES (?, ?, ?, ?)',
                  (data['name'], data['gender'], data['contact'], data['email']))
        conn.commit()
        return jsonify({'message': 'Customer added successfully'}), 201

@app.route('/customers/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def customer(id):
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('SELECT * FROM customers WHERE id = ?', (id,))
        customer = c.fetchone()
        return jsonify(customer)

    elif request.method == 'PUT':
        data = request.json
        c.execute('UPDATE customers SET name = ?, gender = ?, contact = ?, email = ? WHERE id = ?',
                  (data['name'], data['gender'], data['contact'], data['email'], id))
        conn.commit()
        return jsonify({'message': 'Customer updated successfully'})

    elif request.method == 'DELETE':
        c.execute('DELETE FROM customers WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'message': 'Customer deleted successfully'})

# --------------------------- PRODUCT ROUTES ---------------------------
@app.route('/products', methods=['GET', 'POST'])
def products():
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('SELECT * FROM products')
        products = c.fetchall()
        return jsonify(products)

    elif request.method == 'POST':
        data = request.json
        c.execute('INSERT INTO products (name, price, quantity, brand, supplier, old_stock, category) VALUES (?, ?, ?, ?, ?, ?, ?)',
                  (data['name'], data['price'], data['quantity'], data['brand'], data['supplier'], data['old_stock'], data['category']))
        conn.commit()
        return jsonify({'message': 'Product added successfully'}), 201

@app.route('/products/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def product(id):
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('SELECT * FROM products WHERE id = ?', (id,))
        product = c.fetchone()
        return jsonify(product)

    elif request.method == 'PUT':
        data = request.json
        c.execute('UPDATE products SET name = ?, price = ?, quantity = ?, brand = ?, supplier = ?, old_stock = ?, category = ? WHERE id = ?',
                  (data['name'], data['price'], data['quantity'], data['brand'], data['supplier'], data['old_stock'], data['category'], id))
        conn.commit()
        return jsonify({'message': 'Product updated successfully'})

    elif request.method == 'DELETE':
        c.execute('DELETE FROM products WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'message': 'Product deleted successfully'})

# --------------------------- BILL ROUTES ---------------------------
@app.route('/bills', methods=['GET', 'POST'])
def bills():
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('''SELECT bills.id, customers.name as customer_name, bills.total 
                     FROM bills JOIN customers ON bills.customer_id = customers.id''')
        bills = c.fetchall()
        return jsonify(bills)

    elif request.method == 'POST':
        data = request.json
        c.execute('INSERT INTO bills (customer_id, total) VALUES (?, ?)',
                  (data['customer_id'], data['total']))
        bill_id = c.lastrowid
        for item in data['items']:
            c.execute('INSERT INTO bill_items (bill_id, product_id, quantity) VALUES (?, ?, ?)',
                      (bill_id, item['product_id'], item['quantity']))
        conn.commit()
        return jsonify({'message': 'Bill added successfully', 'bill_id': bill_id}), 201

@app.route('/bills/<int:id>', methods=['GET', 'DELETE'])
def bill(id):
    conn = sqlite3.connect('billing_software.db')
    conn.row_factory = dict_factory
    c = conn.cursor()

    if request.method == 'GET':
        c.execute('''SELECT bills.id, customers.name as customer_name, bills.total 
                     FROM bills JOIN customers ON bills.customer_id = customers.id
                     WHERE bills.id = ?''', (id,))
        bill = c.fetchone()
        c.execute('''SELECT products.name, bill_items.quantity, products.price
                     FROM bill_items JOIN products ON bill_items.product_id = products.id
                     WHERE bill_items.bill_id = ?''', (id,))
        bill['items'] = c.fetchall()
        return jsonify(bill)

    elif request.method == 'DELETE':
        c.execute('DELETE FROM bill_items WHERE bill_id = ?', (id,))
        c.execute('DELETE FROM bills WHERE id = ?', (id,))
        conn.commit()
        return jsonify({'message': 'Bill deleted successfully'})

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
