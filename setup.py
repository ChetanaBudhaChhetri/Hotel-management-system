#!/usr/bin/env python3
"""
Setup script for Hotel Management System Database
Run this script to create the database and tables.
Uses SQLite - no MySQL required!
"""

import sqlite3
from sqlite3 import Error
from config import Config

def setup_database():
    try:
        connection = sqlite3.connect(Config.DB_PATH)
        cursor = connection.cursor()

        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_no TEXT NOT NULL UNIQUE,
                type TEXT NOT NULL CHECK (type IN ('AC', 'Non-AC')),
                price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available' CHECK (status IN ('Available', 'Booked'))
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                id_proof TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                customer_id INTEGER NOT NULL,
                check_in_date TEXT NOT NULL,
                check_out_date TEXT,
                days INTEGER NOT NULL,
                total_amount REAL NOT NULL,
                booking_status TEXT NOT NULL DEFAULT 'Checked-In' CHECK (booking_status IN ('Checked-In', 'Checked-Out')),
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
            )
        ''')

        # Insert sample data (using INSERT OR IGNORE to avoid duplicates)
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('101', 'AC', 3500.00, 'Available'))
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('102', 'AC', 4000.00, 'Booked'))
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('103', 'Non-AC', 2200.00, 'Available'))
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('201', 'AC', 5500.00, 'Available'))
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('202', 'Non-AC', 2500.00, 'Booked'))
        cursor.execute('INSERT OR IGNORE INTO rooms (room_no, type, price, status) VALUES (?, ?, ?, ?)',
                      ('301', 'AC', 6500.00, 'Available'))

        cursor.execute('INSERT OR IGNORE INTO customers (name, phone, id_proof) VALUES (?, ?, ?)',
                      ('Aarav Sharma', '9876543210', 'Aadhaar Card'))
        cursor.execute('INSERT OR IGNORE INTO customers (name, phone, id_proof) VALUES (?, ?, ?)',
                      ('Priya Nair', '9123456780', 'Passport'))
        cursor.execute('INSERT OR IGNORE INTO customers (name, phone, id_proof) VALUES (?, ?, ?)',
                      ('Rohan Das', '9988776655', 'Driving License'))

        cursor.execute('INSERT OR IGNORE INTO bookings (room_id, customer_id, check_in_date, check_out_date, days, total_amount, booking_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (2, 1, '2026-04-08', None, 3, 12000.00, 'Checked-In'))
        cursor.execute('INSERT OR IGNORE INTO bookings (room_id, customer_id, check_in_date, check_out_date, days, total_amount, booking_status) VALUES (?, ?, ?, ?, ?, ?, ?)',
                      (5, 2, '2026-04-10', '2026-04-12', 2, 5000.00, 'Checked-Out'))

        connection.commit()
        print('✅ Database setup completed successfully!')
        print('Sample data has been inserted.')
        print(f'Database file: {Config.DB_PATH}')

    except Error as e:
        print(f'❌ Error setting up database: {e}')
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    setup_database()