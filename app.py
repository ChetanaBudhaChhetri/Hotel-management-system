import os
from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from datetime import datetime
from db import get_connection, fetch_all, fetch_one, execute_query
from config import Config
from setup import setup_database

app = Flask(__name__)
app.config.from_object(Config)

# Automatically initialize the database on startup if it's missing or empty
if not os.path.exists(Config.DB_PATH) or os.path.getsize(Config.DB_PATH) == 0:
    setup_database()


def login_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return view_func(*args, **kwargs)
    return wrapper


@app.route('/')
def index():
    # For testing, always redirect to login
    # if session.get('admin_logged_in'):
    #     return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return redirect(url_for('login'))

        if username == app.config['ADMIN_USERNAME'] and password == app.config['ADMIN_PASSWORD']:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Welcome back, admin!', 'success')
            return redirect(url_for('dashboard'))

        flash('Invalid login credentials.', 'danger')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_rooms': fetch_one('SELECT COUNT(*) AS count FROM rooms')['count'],
        'available_rooms': fetch_one("SELECT COUNT(*) AS count FROM rooms WHERE status = 'Available'")['count'],
        'booked_rooms': fetch_one("SELECT COUNT(*) AS count FROM rooms WHERE status = 'Booked'")['count'],
        'total_customers': fetch_one('SELECT COUNT(*) AS count FROM customers')['count'],
    }

    recent_bookings = fetch_all(
        """
        SELECT b.id, r.room_no, r.type, c.name, c.phone, b.check_in_date, b.days, b.total_amount, b.booking_status
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN customers c ON b.customer_id = c.id
        ORDER BY b.id DESC
        LIMIT 5
        """
    )
    return render_template('dashboard.html', stats=stats, recent_bookings=recent_bookings)


@app.route('/rooms', methods=['GET', 'POST'])
@login_required
def rooms():
    if request.method == 'POST':
        room_no = request.form.get('room_no', '').strip()
        room_type = request.form.get('type', '').strip()
        price = request.form.get('price', '').strip()

        if not room_no or not room_type or not price:
            flash('All room fields are required.', 'danger')
            return redirect(url_for('rooms'))

        if room_type not in ['AC', 'Non-AC']:
            flash('Room type must be AC or Non-AC.', 'danger')
            return redirect(url_for('rooms'))

        # Check if room number already exists
        existing_room = fetch_one('SELECT id FROM rooms WHERE room_no = ?', (room_no,))
        if existing_room:
            flash(f'Room number {room_no} already exists.', 'warning')
            return redirect(url_for('rooms'))

        try:
            price_value = float(price)
        except ValueError:
            flash('Price must be a valid number.', 'danger')
            return redirect(url_for('rooms'))

        try:
            execute_query(
                'INSERT INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                (room_no, room_type, price_value, 'Available')
            )
            flash('Room added successfully.', 'success')
        except Exception as exc:
            flash(f'Could not add room. {exc}', 'danger')

        return redirect(url_for('rooms'))

    status_filter = request.args.get('status', '')
    query = 'SELECT * FROM rooms'
    params = ()
    if status_filter in ['Available', 'Booked']:
        query += ' WHERE status = ?'
        params = (status_filter,)
    query += ' ORDER BY room_no ASC'
    room_list = fetch_all(query, params)
    return render_template('rooms.html', rooms=room_list, status_filter=status_filter)


@app.route('/customers', methods=['GET', 'POST'])
@login_required
def customers():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        id_proof = request.form.get('id_proof', '').strip()

        if not name or not phone or not id_proof:
            flash('All customer fields are required.', 'danger')
            return redirect(url_for('customers'))

        execute_query(
            'INSERT INTO customers (name, phone, id_proof) VALUES (?, ?, ?)',
            (name, phone, id_proof)
        )
        flash('Customer added successfully.', 'success')
        return redirect(url_for('customers'))

    search = request.args.get('search', '').strip()
    if search:
        customer_list = fetch_all(
            'SELECT * FROM customers WHERE name LIKE ? ORDER BY id DESC',
            (f'%{search}%',)
        )
    else:
        customer_list = fetch_all('SELECT * FROM customers ORDER BY id DESC')

    return render_template('customers.html', customers=customer_list, search=search)


@app.route('/bookings', methods=['GET', 'POST'])
@login_required
def bookings():
    if request.method == 'POST':
        room_id = request.form.get('room_id', '').strip()
        customer_id = request.form.get('customer_id', '').strip()
        check_in_date = request.form.get('check_in_date', '').strip()
        days = request.form.get('days', '').strip()

        if not room_id or not customer_id or not check_in_date or not days:
            flash('All booking fields are required.', 'danger')
            return redirect(url_for('bookings'))

        try:
            days_value = int(days)
            if days_value <= 0:
                raise ValueError
        except ValueError:
            flash('Days must be a positive whole number.', 'danger')
            return redirect(url_for('bookings'))

        room = fetch_one('SELECT * FROM rooms WHERE id = ?', (room_id,))
        if not room:
            flash('Selected room does not exist.', 'danger')
            return redirect(url_for('bookings'))

        if room['status'] == 'Booked':
            flash('This room is already booked.', 'warning')
            return redirect(url_for('bookings'))

        total_amount = days_value * float(room['price'])
        execute_query(
            '''
            INSERT INTO bookings (room_id, customer_id, check_in_date, days, total_amount, booking_status)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            (room_id, customer_id, check_in_date, days_value, total_amount, 'Checked-In')
        )
        execute_query('UPDATE rooms SET status = ? WHERE id = ?', ('Booked', room_id))
        flash('Room booked and check-in confirmed successfully.', 'success')
        return redirect(url_for('bookings'))

    available_rooms = fetch_all("SELECT * FROM rooms WHERE status = 'Available' ORDER BY room_no ASC")
    customer_list = fetch_all('SELECT * FROM customers ORDER BY name ASC')
    booking_list = fetch_all(
        '''
        SELECT b.id, r.room_no, r.type, r.price, c.name, c.phone, b.check_in_date, b.days,
               b.total_amount, b.booking_status
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN customers c ON b.customer_id = c.id
        ORDER BY b.id DESC
        '''
    )
    today = datetime.today().strftime('%Y-%m-%d')
    return render_template(
        'bookings.html',
        rooms=available_rooms,
        customers=customer_list,
        bookings=booking_list,
        today=today,
    )


@app.route('/checkout/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def checkout(booking_id: int):
    booking = fetch_one(
        '''
        SELECT b.*, r.room_no, r.type, r.price, c.name, c.phone, c.id_proof
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ?
        ''',
        (booking_id,)
    )

    if not booking:
        flash('Booking not found.', 'danger')
        return redirect(url_for('bookings'))

    if request.method == 'POST':
        execute_query(
            'UPDATE bookings SET booking_status = ?, check_out_date = date("now") WHERE id = ?',
            ('Checked-Out', booking_id)
        )
        execute_query('UPDATE rooms SET status = ? WHERE id = ?', ('Available', booking['room_id']))
        flash('Check-out completed and room is now available.', 'success')
        return redirect(url_for('bill', booking_id=booking_id))

    return render_template('checkout.html', booking=booking)


@app.route('/bill/<int:booking_id>')
@login_required
def bill(booking_id: int):
    booking = fetch_one(
        '''
        SELECT b.*, r.room_no, r.type, r.price, c.name, c.phone, c.id_proof
        FROM bookings b
        JOIN rooms r ON b.room_id = r.id
        JOIN customers c ON b.customer_id = c.id
        WHERE b.id = ?
        ''',
        (booking_id,)
    )
    if not booking:
        flash('Bill not found.', 'danger')
        return redirect(url_for('bookings'))

    return render_template('bill.html', booking=booking)


@app.route('/health')
def health():
    return {'status': 'ok', 'app': 'hotel-management-system'}


if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(debug=True, host=host, port=port)
