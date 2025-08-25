from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
from decimal import Decimal
import os

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-change-this")

db_config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "bangtan07"),
    "database": os.getenv("DB_NAME", "bankdb"),
    "raise_on_warnings": True
}

def get_db():
    return mysql.connector.connect(**db_config)

def get_user_by_email(email):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

def get_user_by_id(uid):
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE id = %s", (uid,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    return user

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        if get_user_by_email(email):
            flash("Email already registered", "danger")
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO users (name, email, password_hash, balance) VALUES (%s,%s,%s,%s)",
                    (name, email, password_hash, Decimal('1000.00')))  # give new users small starting balance
        conn.commit()
        cur.close()
        conn.close()
        flash("Account created! Please login.", "success")
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        password = request.form['password']
        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            flash("Welcome back, " + user['name'], "success")
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials", "danger")
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    # recent transactions (involving this user)
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.*, su.name as sender_name, ru.name as receiver_name
        FROM transactions t
        LEFT JOIN users su ON t.sender_id = su.id
        LEFT JOIN users ru ON t.receiver_id = ru.id
        WHERE t.sender_id = %s OR t.receiver_id = %s
        ORDER BY t.txn_time DESC
        LIMIT 8
    """, (user['id'], user['id']))
    txns = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('dashboard.html', user=user, transactions=txns)

@app.route('/transfer', methods=['GET','POST'])
def transfer():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        receiver_email = request.form['receiver_email'].strip().lower()
        amount = Decimal(request.form['amount'])
        note = request.form.get('note', '')

        sender = get_user_by_id(session['user_id'])
        receiver = get_user_by_email(receiver_email)
        if not receiver:
            flash("Receiver not found", "danger")
            return redirect(url_for('transfer'))
        if amount <= 0:
            flash("Amount must be positive", "danger")
            return redirect(url_for('transfer'))
        if Decimal(sender['balance']) < amount:
            flash("Insufficient balance", "danger")
            return redirect(url_for('transfer'))

        conn = get_db()
        cur = conn.cursor()
        # deduct from sender
        cur.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, sender['id']))
        # credit to receiver
        cur.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, receiver['id']))
        # record transaction
        cur.execute("INSERT INTO transactions (sender_id, receiver_id, amount, note) VALUES (%s,%s,%s,%s)",
                    (sender['id'], receiver['id'], amount, note))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Transferred ₹{amount} to {receiver['name']}", "success")
        return redirect(url_for('dashboard'))

    return render_template('transfer.html')

@app.route('/history')
def history():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = get_user_by_id(session['user_id'])
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    cur.execute("""
        SELECT t.*, su.name as sender_name, ru.name as receiver_name
        FROM transactions t
        LEFT JOIN users su ON t.sender_id = su.id
        LEFT JOIN users ru ON t.receiver_id = ru.id
        WHERE t.sender_id = %s OR t.receiver_id = %s
        ORDER BY t.txn_time DESC
    """, (user['id'], user['id']))
    txns = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('history.html', transactions=txns, user=user)

if __name__ == '__main__':
    app.run(debug=True)
