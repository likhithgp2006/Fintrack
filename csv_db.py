import os
import csv
import threading
from datetime import datetime
from werkzeug.security import generate_password_hash

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')
EXPENSES_CSV = os.path.join(DATA_DIR, 'expenses.csv')
CATEGORIES_CSV = os.path.join(DATA_DIR, 'categories.csv')
BUDGETS_CSV = os.path.join(DATA_DIR, 'budgets.csv')
GOALS_CSV = os.path.join(DATA_DIR, 'goals.csv')
SUBSCRIPTIONS_CSV = os.path.join(DATA_DIR, 'subscriptions.csv')
FRIENDS_CSV = os.path.join(DATA_DIR, 'friends.csv')
SHARED_EXPENSES_CSV = os.path.join(DATA_DIR, 'shared_expenses.csv')
SPLIT_ROOMS_CSV = os.path.join(DATA_DIR, 'split_rooms.csv')
SPLIT_ROOM_MEMBERS_CSV = os.path.join(DATA_DIR, 'split_room_members.csv')

_file_lock = threading.Lock()

def init_db():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    with _file_lock:
        # Users CSV
        if not os.path.exists(USERS_CSV):
            with open(USERS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'email', 'phone', 'password_hash', 'created_at'])

        # Categories CSV (universal system default categories)
        if not os.path.exists(CATEGORIES_CSV):
            with open(CATEGORIES_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'name', 'type', 'icon', 'color'])
                default_categories = [
                    ['1', 'Food', 'Expense', 'fa-utensils', '#ef4444'],
                    ['2', 'Transport', 'Expense', 'fa-bus', '#f59e0b'],
                    ['3', 'Housing', 'Expense', 'fa-house', '#10b981'],
                    ['4', 'Education', 'Expense', 'fa-graduation-cap', '#6366f1'],
                    ['5', 'Shopping', 'Expense', 'fa-bag-shopping', '#ec4899'],
                    ['6', 'Health', 'Expense', 'fa-heart-pulse', '#8b5cf6'],
                    ['7', 'Entertainment', 'Expense', 'fa-film', '#3b82f6'],
                    ['8', 'Bills', 'Expense', 'fa-file-invoice-dollar', '#06b6d4'],
                    ['9', 'Travel', 'Expense', 'fa-plane', '#14b8a6'],
                    ['10', 'Recharge', 'Expense', 'fa-mobile-screen-button', '#84cc16'],
                    ['11', 'Salary', 'Income', 'fa-wallet', '#10b981'],
                    ['12', 'Freelance', 'Income', 'fa-laptop-code', '#6366f1'],
                    ['13', 'Investment', 'Income', 'fa-chart-line', '#3b82f6'],
                    ['14', 'Other', 'Expense', 'fa-asterisk', '#64748b']
                ]
                writer.writerows(default_categories)

        # Expenses CSV
        if not os.path.exists(EXPENSES_CSV):
            with open(EXPENSES_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at'])

        # Budgets CSV
        if not os.path.exists(BUDGETS_CSV):
            with open(BUDGETS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'category', 'amount', 'month', 'year'])

        # Savings Goals CSV
        if not os.path.exists(GOALS_CSV):
            with open(GOALS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'title', 'target_amount', 'current_amount', 'target_date', 'category', 'notes', 'created_at'])

        # Recurring Subscriptions CSV
        if not os.path.exists(SUBSCRIPTIONS_CSV):
            with open(SUBSCRIPTIONS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'payment_method', 'status', 'created_at'])

        # Friends CSV
        if not os.path.exists(FRIENDS_CSV):
            with open(FRIENDS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'user_id', 'friend_user_id', 'status', 'created_at'])
                # status: pending | accepted | rejected

        # Shared Expenses CSV
        if not os.path.exists(SHARED_EXPENSES_CSV):
            with open(SHARED_EXPENSES_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'])
                # status: pending | settled

        # Split Rooms CSV
        if not os.path.exists(SPLIT_ROOMS_CSV):
            with open(SPLIT_ROOMS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'])

        # Split Room Members CSV
        if not os.path.exists(SPLIT_ROOM_MEMBERS_CSV):
            with open(SPLIT_ROOM_MEMBERS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'])

# Helper functions for CSV CRUD

def read_csv(filepath):
    with _file_lock:
        if not os.path.exists(filepath):
            return []
        with open(filepath, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return list(reader)

def write_csv(filepath, fieldnames, rows):
    with _file_lock:
        with open(filepath, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

def append_csv(filepath, fieldnames, row_dict):
    with _file_lock:
        with open(filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writerow(row_dict)

def get_next_id(filepath):
    rows = read_csv(filepath)
    if not rows:
        return 1
    ids = [int(r['id']) for r in rows if r.get('id') and r['id'].isdigit()]
    return max(ids) + 1 if ids else 1

def update_user_password(identifier, new_password_hash):
    """Thread-safe update of user password hash in users.csv by phone or email"""
    fieldnames = ['id', 'name', 'email', 'phone', 'password_hash', 'created_at']
    clean_id = str(identifier).strip().lower()
    # Extract digits for phone check
    id_digits = ''.join(c for c in clean_id if c.isdigit())
    if len(id_digits) == 12 and id_digits.startswith('91'):
        id_digits = id_digits[2:]
    elif len(id_digits) == 11 and id_digits.startswith('0'):
        id_digits = id_digits[1:]

    with _file_lock:
        if not os.path.exists(USERS_CSV):
            return False
        rows = []
        updated = False
        with open(USERS_CSV, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                r_email = row.get('email', '').strip().lower()
                r_phone = row.get('phone', '').strip()
                r_digits = ''.join(c for c in r_phone if c.isdigit())
                if len(r_digits) == 12 and r_digits.startswith('91'):
                    r_digits = r_digits[2:]
                elif len(r_digits) == 11 and r_digits.startswith('0'):
                    r_digits = r_digits[1:]

                # Match by email OR by normalized phone
                if r_email == clean_id or (id_digits and len(id_digits) >= 10 and r_digits == id_digits):
                    row['password_hash'] = new_password_hash
                    updated = True
                rows.append(row)
        if updated:
            with open(USERS_CSV, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(rows)
            return True
        return False

