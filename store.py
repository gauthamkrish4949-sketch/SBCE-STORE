import os
from flask import Flask, render_template, request, session, redirect, url_for
from werkzeug.utils import secure_filename

app = Flask(__name__)
# Secure key for sessions
app.secret_key = os.environ.get("SECRET_KEY", "sbce_secret_key_2026")

# Configure Uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Mock Data
inventory = [
    {'id': 1, 'name': 'Physics Lab Record', 'price': 50, 'stock': 100},
    {'id': 2, 'name': 'Scientific Calculator', 'price': 1200, 'stock': 10}
]
orders_received = []
AUTHORIZED_STUDENTS = ["SBCE2401", "SBCE2402", "GAUTHAM"]

@app.route('/')
def home():
    if 'user' not in session and 'is_admin' not in session:
        return redirect(url_for('login'))
    return render_template('index.html', inventory=inventory)

# --- Authentication ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u in AUTHORIZED_STUDENTS and p == "123":
            session['user'] = u
            return redirect(url_for('home'))
        return render_template('login.html', error="Invalid Credentials")
    return render_template('login.html')

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == "admin" and p == "sbce123":
            session['is_admin'] = True
            return redirect(url_for('admin_panel'))
        return render_template('admin_login_page.html', error="Invalid Admin Login")
    return render_template('admin_login_page.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# --- Store Logic ---

@app.route('/checkout', methods=['POST'])
def checkout():
    logged_in_user = session.get('user', 'None')
    s_name = request.form.get('student_name')
    pay_method = request.form.get('payment_method')
    
    cart = session.get('cart', {})
    items_summary = []
    order_total = 0 

    for pid, qty in cart.items():
        product = next((item for item in inventory if item['id'] == int(pid)), None)
        if product:
            order_total += (product['price'] * qty)
            product['stock'] -= qty
            items_summary.append(f"{product['name']} (x{qty})")

    new_order = {
        'id': len(orders_received) + 1,
        'username': logged_in_user,
        'name': s_name,
        'purchased_items': ", ".join(items_summary),
        'total': order_total,
        'method': pay_method,
        'status': '⏳ Pending Verification' if pay_method == 'UPI' else '💵 Cash on Counter',
        'screenshot': None 
    }
    
    orders_received.append(new_order)
    session.pop('cart', None)
    
    if pay_method == 'UPI':
        return redirect(url_for('payment', order_id=new_order['id']))
    return render_template('order_confirmed.html', name=s_name)

@app.route('/payment/<int:order_id>', methods=['GET', 'POST'])
def payment(order_id):
    if request.method == 'POST':
        file = request.files.get('screenshot')
        if file:
            filename = secure_filename(f"order_{order_id}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            for order in orders_received:
                if order['id'] == order_id:
                    order['screenshot'] = filename
                    order['status'] = '✅ Payment Uploaded'
            return render_template('order_confirmed.html')
            
    return render_template('payment_page.html', order_id=order_id)

# --- Admin Panel ---

@app.route('/admin')
def admin_panel():
    if not session.get('is_admin'):
        return redirect(url_for('admin_login'))
    return render_template('admin.html', orders=orders_received)

@app.route('/deliver_order/<int:order_id>', methods=['POST'])
def deliver_order(order_id):
    order = next((o for o in orders_received if o['id'] == order_id), None)
    if order:
        order['status'] = '🏁 Delivered'
    return redirect(url_for('admin_panel'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
