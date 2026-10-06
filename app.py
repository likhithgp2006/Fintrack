import os
import io
import csv
import secrets
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps
from datetime import datetime, timedelta, date
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from werkzeug.security import generate_password_hash, check_password_hash
from flask_cors import CORS
import requests

def normalize_phone(phone_str):
    """Normalizes phone string to clean 10-digit number without country code or symbols"""
    if not phone_str:
        return ''
    digits = ''.join(c for c in str(phone_str) if c.isdigit())
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]
    return digits

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

def _load_local_env():
    """Fallback loader for .env if python-dotenv is not present."""
    env_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        k, v = line.split('=', 1)
                        k = k.strip()
                        v = v.strip().strip("'\"")
                        if k and k not in os.environ:
                            os.environ[k] = v
        except Exception:
            pass

_load_local_env()

import csv_db

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'smart_expense_tracker_bca_secret_key_2026')
CORS(app)

# Initialize database CSVs on startup
csv_db.init_db()

# --- Auth Decorator ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'message': 'Authentication required. Please log in.'}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


# --- HTML Page Routes ---

@app.route('/')
def index_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('index.html')

@app.route('/login')
def login_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('login.html')

@app.route('/register')
def register_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('register.html')

@app.route('/forgot-password')
def forgot_password_page():
    if 'user_id' in session:
        return redirect(url_for('dashboard_page'))
    return render_template('forgot-password.html')

@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html', user_name=session.get('user_name', 'User'))

@app.route('/add-expense')
@login_required
def add_expense_page():
    return render_template('add-expense.html')

@app.route('/transactions')
@login_required
def transactions_page():
    return render_template('transactions.html')

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

@app.route('/budgets')
@login_required
def budgets_page():
    return render_template('budgets.html')

@app.route('/profile')
@login_required
def profile_page():
    return render_template('profile.html')

@app.route('/goals')
@login_required
def goals_page():
    return render_template('goals.html')

@app.route('/subscriptions')
@login_required
def subscriptions_page():
    return render_template('subscriptions.html')

@app.route('/split-bill')
@login_required
def split_bill_page():
    return render_template('split-bill.html')


# --- AUTH APIs ---

@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = normalize_phone(data.get('phone', ''))
    password = data.get('password', '')
    confirm_password = data.get('confirm_password', '')

    if not name or not email or not phone or not password:
        return jsonify({'success': False, 'message': 'All fields including 10-digit mobile number are required.'}), 400

    if len(phone) < 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number.'}), 400

    if password != confirm_password:
        return jsonify({'success': False, 'message': 'Passwords do not match.'}), 400

    if len(password) < 6:
        return jsonify({'success': False, 'message': 'Password must be at least 6 characters long.'}), 400

    users = csv_db.read_csv(csv_db.USERS_CSV)
    for u in users:
        if u.get('email', '').strip().lower() == email:
            return jsonify({'success': False, 'message': 'Email address is already registered.'}), 400
        u_ph = normalize_phone(u.get('phone', ''))
        if u_ph and u_ph == phone:
            return jsonify({'success': False, 'message': 'Mobile number is already registered with another account.'}), 400

    user_id = str(csv_db.get_next_id(csv_db.USERS_CSV))
    pw_hash = generate_password_hash(password)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_user = {
        'id': user_id,
        'name': name,
        'email': email,
        'phone': phone,
        'password_hash': pw_hash,
        'created_at': now_str
    }
    fieldnames = ['id', 'name', 'email', 'phone', 'password_hash', 'created_at']
    csv_db.append_csv(csv_db.USERS_CSV, fieldnames, new_user)

    session['user_id'] = user_id
    session['user_name'] = name
    session['user_email'] = email
    session['user_phone'] = phone

    return jsonify({
        'success': True,
        'message': 'Registration successful! Welcome aboard.',
        'user': {'id': user_id, 'name': name, 'email': email, 'phone': phone}
    })

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'message': 'Email and password are required.'}), 400

    users = csv_db.read_csv(csv_db.USERS_CSV)
    target_user = None
    for u in users:
        if u['email'].lower() == email:
            target_user = u
            break

    if not target_user or not check_password_hash(target_user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Invalid email or password.'}), 401

    session['user_id'] = target_user['id']
    session['user_name'] = target_user['name']
    session['user_email'] = target_user['email']
    session['user_phone'] = target_user.get('phone', '')

    return jsonify({
        'success': True,
        'message': 'Login successful!',
        'user': {'id': target_user['id'], 'name': target_user['name'], 'email': target_user['email'], 'phone': target_user.get('phone', '')}
    })

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully.'})

@app.route('/api/me', methods=['GET'])
def api_me():
    if 'user_id' in session:
        return jsonify({
            'success': True,
            'user': {
                'id': session['user_id'],
                'name': session.get('user_name', ''),
                'email': session.get('user_email', ''),
                'phone': session.get('user_phone', '')
            }
        })
    return jsonify({'success': False, 'message': 'Not logged in.'}), 401


# --- FORGOT PASSWORD & SMS OTP APIs ---

def send_password_reset_sms(phone, user_name, otp_code):
    """
    Sends a real password reset OTP SMS.
    1. Checks Fast2SMS API key (FAST2SMS_API_KEY) - ideal for Indian mobile numbers.
    2. Checks Twilio credentials (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER).
    3. If neither service is configured, runs in Demo Mode: returns (True, message, is_demo=True)
       so the web interface can display the OTP without failing or blocking the user.
    Returns (success, message, is_demo).
    """
    fast2sms_key = os.environ.get('FAST2SMS_API_KEY', '').strip()
    twilio_sid = os.environ.get('TWILIO_ACCOUNT_SID', '').strip()
    twilio_token = os.environ.get('TWILIO_AUTH_TOKEN', '').strip()
    twilio_phone = os.environ.get('TWILIO_PHONE_NUMBER', '').strip()

    clean_p = normalize_phone(phone)

    # 1. Fast2SMS Gateway (Quick OTP route)
    if fast2sms_key and not fast2sms_key.lower().startswith('your_'):
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "variables_values": otp_code,
                "route": "otp",
                "numbers": clean_p
            }
            headers = {
                "authorization": fast2sms_key,
                "Content-Type": "application/json"
            }
            res = requests.post(url, json=payload, headers=headers, timeout=10)
            res_json = res.json()
            if res_json.get("return") is True:
                print(f"[SMS-AUTH] Successfully dispatched Fast2SMS OTP to {clean_p}")
                return True, "SMS OTP sent successfully to your mobile number.", False
            else:
                msg = res_json.get("message", ["Fast2SMS dispatch failed"])[0] if isinstance(res_json.get("message"), list) else str(res_json.get("message"))
                print(f"[SMS-AUTH ERROR] Fast2SMS error: {msg}")
                return False, f"SMS Gateway Error: {msg}", False
        except Exception as e:
            print(f"[SMS-AUTH EXCEPTION] Fast2SMS connection failed: {e}")
            return False, f"SMS service connection error: {str(e)}", False

    # 2. Twilio Gateway
    if twilio_sid and twilio_token and twilio_phone and not twilio_sid.lower().startswith('your_'):
        try:
            target_num = f"+91{clean_p}" if len(clean_p) == 10 else f"+{clean_p}"
            msg_body = f"Your Smart Expense Tracker verification code is: {otp_code}. Valid for 15 minutes."
            twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{twilio_sid}/Messages.json"
            res = requests.post(
                twilio_url,
                auth=(twilio_sid, twilio_token),
                data={
                    "To": target_num,
                    "From": twilio_phone,
                    "Body": msg_body
                },
                timeout=10
            )
            if res.status_code in (200, 201):
                print(f"[SMS-AUTH] Successfully dispatched Twilio SMS to {target_num}")
                return True, "SMS OTP sent successfully to your mobile number.", False
            else:
                try:
                    res_data = res.json()
                    msg = res_data.get('message', res.text)
                except Exception:
                    msg = res.text
                print(f"[SMS-AUTH ERROR] Twilio error: {msg}")
                return False, f"Twilio SMS Error: {msg}", False
        except Exception as e:
            print(f"[SMS-AUTH EXCEPTION] Twilio connection failed: {e}")
            return False, f"SMS service connection error: {str(e)}", False

    # 3. Demo Mode (Fallback when SMS provider API key is not configured)
    print(f"[SMS-AUTH DEMO MODE] Mobile: {clean_p} | Generated OTP: {otp_code}")
    demo_msg = f"SMS Gateway not configured in .env. Use Demo OTP: {otp_code}"
    return True, demo_msg, True


def send_password_reset_email(to_email, user_name, otp_code):
    """Fallback email dispatcher if email reset is requested."""
    mail_server = os.environ.get('MAIL_SERVER', 'smtp.gmail.com').strip()
    mail_port = int(os.environ.get('MAIL_PORT', 587))
    mail_username = os.environ.get('MAIL_USERNAME', '').strip()
    mail_password = os.environ.get('MAIL_PASSWORD', '').strip().replace(' ', '')
    mail_use_tls = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('true', '1', 't')
    mail_use_ssl = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('true', '1', 't') or mail_port == 465
    mail_default_sender = os.environ.get('MAIL_DEFAULT_SENDER', '').strip() or mail_username or 'noreply@smartfinance.app'

    if not mail_username or not mail_password or mail_username.startswith('your_'):
        return False, "SMTP credentials are not configured in deployment environment."

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"{otp_code} is your Smart Expense Tracker verification code"
        msg['From'] = f"Smart Expense Tracker <{mail_default_sender}>"
        msg['To'] = to_email

        body = f"Hello {user_name},\n\nYour 6-digit verification code is: {otp_code}\nValid for 15 minutes."
        msg.attach(MIMEText(body, 'plain'))

        if mail_use_ssl:
            server = smtplib.SMTP_SSL(mail_server, mail_port, timeout=15)
        else:
            server = smtplib.SMTP(mail_server, mail_port, timeout=15)
            if mail_use_tls:
                server.starttls()
        server.login(mail_username, mail_password)
        server.sendmail(mail_default_sender, [to_email], msg.as_string())
        server.quit()
        return True, "Email sent successfully."
    except Exception as e:
        return False, str(e)


_reset_tokens = {}
_reset_tokens_lock = threading.Lock()

def _normalize_key(identifier):
    clean = str(identifier).strip().lower()
    digits = normalize_phone(clean)
    return digits if digits and len(digits) >= 10 else clean

def create_reset_token(identifier):
    """Generates a secure 6-digit verification code with 15-minute validity"""
    code = f"{secrets.randbelow(900000) + 100000}"
    expires_at = datetime.now() + timedelta(minutes=15)
    key = _normalize_key(identifier)
    with _reset_tokens_lock:
        _reset_tokens[key] = {
            'code': code,
            'expires_at': expires_at,
            'attempts': 0
        }
    return code

def verify_reset_token(identifier, code):
    """Validates the reset token and returns (is_valid, message)"""
    key = _normalize_key(identifier)
    with _reset_tokens_lock:
        data = _reset_tokens.get(key)
        if not data:
            return False, "No active password reset request found for this mobile number."
        if datetime.now() > data['expires_at']:
            del _reset_tokens[key]
            return False, "Verification code has expired. Please request a new one."
        if data['attempts'] >= 5:
            del _reset_tokens[key]
            return False, "Too many invalid attempts. Please request a new code."
        if str(data['code']).strip() != str(code).strip():
            data['attempts'] += 1
            return False, "Invalid verification code. Please check and try again."
        return True, "Code verified."

def clear_reset_token(identifier):
    """Clears used token from memory"""
    key = _normalize_key(identifier)
    with _reset_tokens_lock:
        _reset_tokens.pop(key, None)


@app.route('/api/forgot-password/request', methods=['POST'])
def api_forgot_password_request():
    data = request.get_json() or {}
    phone_raw = data.get('phone', '') or data.get('email', '')
    phone = normalize_phone(phone_raw)

    if not phone or len(phone) < 10:
        return jsonify({'success': False, 'message': 'Please enter a valid 10-digit mobile number.'}), 400

    users = csv_db.read_csv(csv_db.USERS_CSV)
    target_user = None
    for u in users:
        u_phone = normalize_phone(u.get('phone', ''))
        if u_phone == phone:
            target_user = u
            break

    if not target_user:
        return jsonify({'success': False, 'message': 'No registered account found with this mobile number.'}), 404

    code = create_reset_token(phone)
    user_name = target_user.get('name', 'User')

    # Send SMS OTP
    sms_sent, sms_msg, is_demo = send_password_reset_sms(phone, user_name, code)

    if not sms_sent:
        clear_reset_token(phone)
        return jsonify({
            'success': False,
            'sms_sent': False,
            'message': sms_msg
        }), 500

    masked_phone = f"+91 ******{phone[-4:]}" if len(phone) >= 4 else phone

    return jsonify({
        'success': True,
        'sms_sent': True,
        'is_demo': is_demo,
        'demo_code': code if is_demo else None,
        'phone': phone,
        'masked_phone': masked_phone,
        'message': f"A 6-digit verification code has been dispatched to {masked_phone} via SMS.",
        'expires_in_minutes': 15
    })


@app.route('/api/forgot-password/verify-code', methods=['POST'])
def api_forgot_password_verify_code():
    data = request.get_json() or {}
    phone_raw = data.get('phone', '') or data.get('email', '')
    phone = normalize_phone(phone_raw)
    code = data.get('code', '').strip()

    if not phone or not code:
        return jsonify({'success': False, 'message': 'Mobile number and verification code are required.'}), 400

    valid, msg = verify_reset_token(phone, code)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    return jsonify({'success': True, 'message': 'Verification code verified successfully.'})


@app.route('/api/forgot-password/reset', methods=['POST'])
def api_forgot_password_reset():
    data = request.get_json() or {}
    phone_raw = data.get('phone', '') or data.get('email', '')
    phone = normalize_phone(phone_raw)
    code = data.get('code', '').strip()
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not phone or not code or not new_password or not confirm_password:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New password and confirmation do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters long.'}), 400

    valid, msg = verify_reset_token(phone, code)
    if not valid:
        return jsonify({'success': False, 'message': msg}), 400

    new_hash = generate_password_hash(new_password)
    updated = csv_db.update_user_password(phone, new_hash)
    if not updated:
        return jsonify({'success': False, 'message': 'Failed to update password. User account not found.'}), 404

    clear_reset_token(phone)
    return jsonify({
        'success': True,
        'message': 'Password has been reset successfully! You can now log in with your new password.'
    })


@app.route('/api/profile/change-password', methods=['POST'])
@login_required
def api_change_password():
    data = request.get_json() or {}
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')

    if not current_password or not new_password or not confirm_password:
        return jsonify({'success': False, 'message': 'All password fields are required.'}), 400

    if new_password != confirm_password:
        return jsonify({'success': False, 'message': 'New password and confirmation do not match.'}), 400

    if len(new_password) < 6:
        return jsonify({'success': False, 'message': 'New password must be at least 6 characters long.'}), 400

    user_id = session['user_id']
    users = csv_db.read_csv(csv_db.USERS_CSV)
    target_user = next((u for u in users if u['id'] == user_id), None)

    if not target_user:
        return jsonify({'success': False, 'message': 'User account not found.'}), 404

    if not check_password_hash(target_user['password_hash'], current_password):
        return jsonify({'success': False, 'message': 'Current password is incorrect.'}), 400

    if current_password == new_password:
        return jsonify({'success': False, 'message': 'New password must be different from current password.'}), 400

    new_hash = generate_password_hash(new_password)
    csv_db.update_user_password(target_user['email'], new_hash)

    return jsonify({'success': True, 'message': 'Your password has been changed successfully!'})



# --- CATEGORIES APIs ---

@app.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    categories = csv_db.read_csv(csv_db.CATEGORIES_CSV)
    return jsonify({'success': True, 'categories': categories})

@app.route('/api/categories', methods=['POST'])
@login_required
def api_add_category():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    c_type = data.get('type', 'Expense')
    icon = data.get('icon', 'fa-folder')
    color = data.get('color', '#6366f1')

    if not name:
        return jsonify({'success': False, 'message': 'Category name is required.'}), 400

    categories = csv_db.read_csv(csv_db.CATEGORIES_CSV)
    for c in categories:
        if c['name'].lower() == name.lower():
            return jsonify({'success': False, 'message': 'Category already exists.'}), 400

    cat_id = str(csv_db.get_next_id(csv_db.CATEGORIES_CSV))
    new_cat = {'id': cat_id, 'name': name, 'type': c_type, 'icon': icon, 'color': color}
    csv_db.append_csv(csv_db.CATEGORIES_CSV, ['id', 'name', 'type', 'icon', 'color'], new_cat)

    return jsonify({'success': True, 'message': 'Category added successfully.', 'category': new_cat})


# --- EXPENSES / TRANSACTIONS CRUD APIs ---

@app.route('/api/expenses', methods=['GET'])
@login_required
def api_get_expenses():
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    
    # Filter by user_id
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id]

    # Query filters
    search = request.args.get('search', '').strip().lower()
    category = request.args.get('category', '').strip()
    t_type = request.args.get('type', '').strip()
    payment_method = request.args.get('payment_method', '').strip()
    start_date = request.args.get('start_date', '').strip()
    end_date = request.args.get('end_date', '').strip()
    min_amount = request.args.get('min_amount', type=float)
    max_amount = request.args.get('max_amount', type=float)
    sort_by = request.args.get('sort_by', 'date')
    sort_order = request.args.get('sort_order', 'desc')
    
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)

    filtered = []
    for item in user_expenses:
        # Search match
        if search:
            match = (search in item.get('description', '').lower() or
                     search in item.get('category', '').lower() or
                     search in item.get('payment_method', '').lower() or
                     search in item.get('notes', '').lower())
            if not match:
                continue

        if category and item.get('category') != category:
            continue
        if t_type and item.get('type') != t_type:
            continue
        if payment_method and item.get('payment_method') != payment_method:
            continue
        if start_date and item.get('date') < start_date:
            continue
        if end_date and item.get('date') > end_date:
            continue
        
        amt = float(item.get('amount', 0))
        if min_amount is not None and amt < min_amount:
            continue
        if max_amount is not None and amt > max_amount:
            continue

        filtered.append(item)

    # Sorting
    reverse = (sort_order.lower() == 'desc')
    if sort_by == 'amount':
        filtered.sort(key=lambda x: float(x.get('amount', 0)), reverse=reverse)
    elif sort_by == 'description':
        filtered.sort(key=lambda x: x.get('description', '').lower(), reverse=reverse)
    elif sort_by == 'category':
        filtered.sort(key=lambda x: x.get('category', '').lower(), reverse=reverse)
    else:  # default date
        filtered.sort(key=lambda x: (x.get('date', ''), x.get('id', '')), reverse=reverse)

    total_count = len(filtered)
    total_filtered_income = sum(float(x['amount']) for x in filtered if x.get('type') == 'Income')
    total_filtered_expense = sum(float(x['amount']) for x in filtered if x.get('type') == 'Expense')

    # Pagination
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated = filtered[start_idx:end_idx]

    return jsonify({
        'success': True,
        'expenses': paginated,
        'pagination': {
            'total': total_count,
            'page': page,
            'limit': limit,
            'pages': (total_count + limit - 1) // limit if limit > 0 else 1
        },
        'summary': {
            'filtered_income': total_filtered_income,
            'filtered_expense': total_filtered_expense
        }
    })

@app.route('/api/expenses/<int:expense_id>', methods=['GET'])
@login_required
def api_get_single_expense(expense_id):
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    for e in all_expenses:
        if e.get('id') == str(expense_id) and e.get('user_id') == user_id:
            return jsonify({'success': True, 'expense': e})
    return jsonify({'success': False, 'message': 'Transaction not found or unauthorized.'}), 404

@app.route('/api/expenses', methods=['POST'])
@login_required
def api_add_expense():
    user_id = session['user_id']
    data = request.get_json() or {}

    date = data.get('date', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    amount_raw = data.get('amount', 0)
    payment_method = data.get('payment_method', '').strip()
    t_type = data.get('type', 'Expense').strip()
    notes = data.get('notes', '').strip()

    if not date or not description or not category or not payment_method or not t_type:
        return jsonify({'success': False, 'message': 'Please fill all required fields.'}), 400

    try:
        amount = float(amount_raw)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount provided.'}), 400

    expense_id = str(csv_db.get_next_id(csv_db.EXPENSES_CSV))
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_item = {
        'id': expense_id,
        'user_id': user_id,
        'date': date,
        'description': description,
        'category': category,
        'amount': f"{amount:.2f}",
        'payment_method': payment_method,
        'type': t_type,
        'notes': notes,
        'created_at': now_str
    }

    fieldnames = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
    csv_db.append_csv(csv_db.EXPENSES_CSV, fieldnames, new_item)

    return jsonify({
        'success': True,
        'message': 'Transaction added successfully!',
        'expense': new_item
    })

@app.route('/api/expenses/<int:expense_id>', methods=['PUT'])
@login_required
def api_update_expense(expense_id):
    user_id = session['user_id']
    data = request.get_json() or {}

    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    target_idx = -1
    for i, e in enumerate(all_expenses):
        if e.get('id') == str(expense_id) and e.get('user_id') == user_id:
            target_idx = i
            break

    if target_idx == -1:
        return jsonify({'success': False, 'message': 'Transaction not found or unauthorized.'}), 404

    date = data.get('date', all_expenses[target_idx]['date']).strip()
    description = data.get('description', all_expenses[target_idx]['description']).strip()
    category = data.get('category', all_expenses[target_idx]['category']).strip()
    payment_method = data.get('payment_method', all_expenses[target_idx]['payment_method']).strip()
    t_type = data.get('type', all_expenses[target_idx]['type']).strip()
    notes = data.get('notes', all_expenses[target_idx]['notes']).strip()

    try:
        amount = float(data.get('amount', all_expenses[target_idx]['amount']))
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount.'}), 400

    all_expenses[target_idx]['date'] = date
    all_expenses[target_idx]['description'] = description
    all_expenses[target_idx]['category'] = category
    all_expenses[target_idx]['amount'] = f"{amount:.2f}"
    all_expenses[target_idx]['payment_method'] = payment_method
    all_expenses[target_idx]['type'] = t_type
    all_expenses[target_idx]['notes'] = notes

    fieldnames = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
    csv_db.write_csv(csv_db.EXPENSES_CSV, fieldnames, all_expenses)

    return jsonify({
        'success': True,
        'message': 'Transaction updated successfully!',
        'expense': all_expenses[target_idx]
    })

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
@login_required
def api_delete_expense(expense_id):
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)

    new_expenses = [e for e in all_expenses if not (e.get('id') == str(expense_id) and e.get('user_id') == user_id)]

    if len(new_expenses) == len(all_expenses):
        return jsonify({'success': False, 'message': 'Transaction not found or unauthorized.'}), 404

    fieldnames = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
    csv_db.write_csv(csv_db.EXPENSES_CSV, fieldnames, new_expenses)

    return jsonify({'success': True, 'message': 'Transaction deleted successfully.'})


# --- DASHBOARD & ANALYTICS APIs ---

@app.route('/api/dashboard', methods=['GET'])
@login_required
def api_get_dashboard():
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id]

    total_income = 0.0
    total_expenses = 0.0
    highest_expense = 0.0
    current_month_spending = 0.0

    now = datetime.now()
    current_ym = now.strftime('%Y-%m')

    category_map = {}
    monthly_map = {}

    for e in user_expenses:
        amt = float(e.get('amount', 0))
        t_type = e.get('type', 'Expense')
        cat = e.get('category', 'Other')
        date_str = e.get('date', '')

        if t_type == 'Income':
            total_income += amt
        else:
            total_expenses += amt
            if amt > highest_expense:
                highest_expense = amt

            if date_str.startswith(current_ym):
                current_month_spending += amt

            # Category aggregation for expenses
            category_map[cat] = category_map.get(cat, 0.0) + amt

        # Monthly aggregation (both income and expense)
        if len(date_str) >= 7:
            ym = date_str[:7]
            if ym not in monthly_map:
                monthly_map[ym] = {'income': 0.0, 'expense': 0.0}
            if t_type == 'Income':
                monthly_map[ym]['income'] += amt
            else:
                monthly_map[ym]['expense'] += amt

    balance = total_income - total_expenses
    total_transactions = len(user_expenses)

    # Sort recent transactions (last 10)
    sorted_recent = sorted(user_expenses, key=lambda x: (x.get('date', ''), x.get('id', '')), reverse=True)[:10]

    # Category chart data
    category_chart = {
        'labels': list(category_map.keys()),
        'datasets': list(category_map.values())
    }

    # Monthly chart data (sorted by YYYY-MM)
    sorted_months = sorted(monthly_map.keys())
    monthly_chart = {
        'labels': sorted_months,
        'income': [monthly_map[m]['income'] for m in sorted_months],
        'expense': [monthly_map[m]['expense'] for m in sorted_months]
    }

    return jsonify({
        'success': True,
        'summary': {
            'total_income': total_income,
            'total_expenses': total_expenses,
            'balance': balance,
            'total_transactions': total_transactions,
            'highest_expense': highest_expense,
            'current_month_spending': current_month_spending
        },
        'recent_transactions': sorted_recent,
        'charts': {
            'category': category_chart,
            'monthly': monthly_chart
        }
    })


# --- REPORTS APIs ---

@app.route('/api/reports/monthly', methods=['GET'])
@login_required
def api_reports_monthly():
    user_id = session['user_id']
    month = request.args.get('month', datetime.now().strftime('%m'))
    year = request.args.get('year', datetime.now().strftime('%Y'))

    target_prefix = f"{year}-{month.zfill(2)}"

    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id and e.get('date', '').startswith(target_prefix)]

    total_income = sum(float(e['amount']) for e in user_expenses if e.get('type') == 'Income')
    total_expenses = sum(float(e['amount']) for e in user_expenses if e.get('type') == 'Expense')
    balance = total_income - total_expenses

    category_summary = {}
    for e in user_expenses:
        if e.get('type') == 'Expense':
            cat = e.get('category', 'Other')
            category_summary[cat] = category_summary.get(cat, 0.0) + float(e['amount'])

    return jsonify({
        'success': True,
        'period': target_prefix,
        'summary': {
            'income': total_income,
            'expenses': total_expenses,
            'balance': balance,
            'transaction_count': len(user_expenses)
        },
        'category_summary': category_summary,
        'transactions': user_expenses
    })

@app.route('/api/reports/category', methods=['GET'])
@login_required
def api_reports_category():
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id and e.get('type') == 'Expense']

    category_summary = {}
    for e in user_expenses:
        cat = e.get('category', 'Other')
        category_summary[cat] = category_summary.get(cat, 0.0) + float(e['amount'])

    total = sum(category_summary.values())
    result = []
    for cat, amt in category_summary.items():
        pct = (amt / total * 100) if total > 0 else 0
        result.append({'category': cat, 'amount': amt, 'percentage': round(pct, 2)})

    result.sort(key=lambda x: x['amount'], reverse=True)

    return jsonify({'success': True, 'categories': result, 'total_expense': total})


# --- BUDGETS APIs ---

@app.route('/api/budgets', methods=['GET'])
@login_required
def api_get_budgets():
    user_id = session['user_id']
    now = datetime.now()
    month = request.args.get('month', now.strftime('%m')).zfill(2)
    year = request.args.get('year', now.strftime('%Y'))

    all_budgets = csv_db.read_csv(csv_db.BUDGETS_CSV)
    user_budgets = [b for b in all_budgets if b.get('user_id') == user_id and b.get('month') == month and b.get('year') == year]

    # Calculate spent per category in this month/year
    target_prefix = f"{year}-{month}"
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    month_expenses = [e for e in all_expenses if e.get('user_id') == user_id and e.get('type') == 'Expense' and e.get('date', '').startswith(target_prefix)]

    spent_map = {}
    for e in month_expenses:
        cat = e.get('category')
        spent_map[cat] = spent_map.get(cat, 0.0) + float(e.get('amount', 0))

    result = []
    warnings = []
    for b in user_budgets:
        cat = b.get('category')
        budget_amt = float(b.get('amount', 0))
        spent = spent_map.get(cat, 0.0)
        remaining = budget_amt - spent
        pct = (spent / budget_amt * 100) if budget_amt > 0 else 0

        status = 'ok'
        if pct >= 100:
            status = 'danger'
            warnings.append(f"Exceeded your {cat} budget! Spent ₹{spent:,.2f} of ₹{budget_amt:,.2f}")
        elif pct >= 80:
            status = 'warning'
            warnings.append(f"Warning: Used {pct:.1f}% of your {cat} budget.")

        result.append({
            'id': b.get('id'),
            'category': cat,
            'budget_amount': budget_amt,
            'spent_amount': spent,
            'remaining_amount': remaining,
            'percentage_used': round(pct, 1),
            'status': status,
            'month': month,
            'year': year
        })

    return jsonify({
        'success': True,
        'budgets': result,
        'warnings': warnings,
        'month': month,
        'year': year
    })

@app.route('/api/budgets', methods=['POST'])
@login_required
def api_add_budget():
    user_id = session['user_id']
    data = request.get_json() or {}
    category = data.get('category', '').strip()
    amount_raw = data.get('amount', 0)
    now = datetime.now()
    month = str(data.get('month', now.strftime('%m'))).zfill(2)
    year = str(data.get('year', now.strftime('%Y')))

    if not category:
        return jsonify({'success': False, 'message': 'Category is required.'}), 400

    try:
        amount = float(amount_raw)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Budget amount must be greater than zero.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid budget amount.'}), 400

    all_budgets = csv_db.read_csv(csv_db.BUDGETS_CSV)
    
    # Check if budget already exists for this category/month/year for user
    existing_idx = -1
    for i, b in enumerate(all_budgets):
        if b.get('user_id') == user_id and b.get('category') == category and b.get('month') == month and b.get('year') == year:
            existing_idx = i
            break

    fieldnames = ['id', 'user_id', 'category', 'amount', 'month', 'year']
    if existing_idx != -1:
        all_budgets[existing_idx]['amount'] = f"{amount:.2f}"
        csv_db.write_csv(csv_db.BUDGETS_CSV, fieldnames, all_budgets)
        msg = f"Budget for {category} updated to ₹{amount:,.2f}."
    else:
        budget_id = str(csv_db.get_next_id(csv_db.BUDGETS_CSV))
        new_budget = {
            'id': budget_id,
            'user_id': user_id,
            'category': category,
            'amount': f"{amount:.2f}",
            'month': month,
            'year': year
        }
        csv_db.append_csv(csv_db.BUDGETS_CSV, fieldnames, new_budget)
        msg = f"Budget set for {category}: ₹{amount:,.2f}."

    return jsonify({'success': True, 'message': msg})

@app.route('/api/budgets/<int:budget_id>', methods=['DELETE'])
@login_required
def api_delete_budget(budget_id):
    user_id = session['user_id']
    all_budgets = csv_db.read_csv(csv_db.BUDGETS_CSV)

    new_budgets = [b for b in all_budgets if not (b.get('id') == str(budget_id) and b.get('user_id') == user_id)]

    if len(new_budgets) == len(all_budgets):
        return jsonify({'success': False, 'message': 'Budget not found.'}), 404

    fieldnames = ['id', 'user_id', 'category', 'amount', 'month', 'year']
    csv_db.write_csv(csv_db.BUDGETS_CSV, fieldnames, new_budgets)

    return jsonify({'success': True, 'message': 'Budget deleted successfully.'})


# --- CSV EXPORT API ---

@app.route('/api/export/csv', methods=['GET'])
@login_required
def api_export_csv():
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Date', 'Description', 'Category', 'Amount (INR)', 'Payment Method', 'Type', 'Notes', 'Created At'])

    for e in user_expenses:
        writer.writerow([
            e.get('id'),
            e.get('date'),
            e.get('description'),
            e.get('category'),
            e.get('amount'),
            e.get('payment_method'),
            e.get('type'),
            e.get('notes'),
            e.get('created_at')
        ])

    output.seek(0)
    filename = f"expenses_export_{session.get('user_name', 'user')}_{datetime.now().strftime('%Y%m%d')}.csv"
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": f"attachment; filename={filename}"}
    )


# --- SAVINGS GOALS APIs ---

@app.route('/api/goals', methods=['GET'])
@login_required
def api_get_goals():
    user_id = session['user_id']
    all_goals = csv_db.read_csv(csv_db.GOALS_CSV)
    user_goals = [g for g in all_goals if g.get('user_id') == user_id]

    today = datetime.now().date()
    formatted = []
    total_target = 0.0
    total_saved = 0.0
    completed_count = 0

    for g in user_goals:
        try:
            target = float(g.get('target_amount', 0))
            current = float(g.get('current_amount', 0))
        except (ValueError, TypeError):
            target = 0.0
            current = 0.0

        total_target += target
        total_saved += current

        pct = (current / target * 100) if target > 0 else 0
        pct_display = min(100.0, round(pct, 1))

        # Days remaining
        target_date_str = g.get('target_date', '')
        days_remaining = None
        status = 'In Progress'
        if target_date_str:
            try:
                t_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
                days_remaining = (t_date - today).days
                if days_remaining < 0 and pct < 100:
                    status = 'Overdue'
            except ValueError:
                pass

        if pct >= 100:
            status = 'Completed'
            completed_count += 1

        # Milestone badge
        if pct >= 100:
            milestone = {'name': 'Completed', 'badge': '🏆 Target Reached', 'class': 'badge-success'}
        elif pct >= 75:
            milestone = {'name': 'Gold', 'badge': '🥇 75% Milestone', 'class': 'badge-income'}
        elif pct >= 50:
            milestone = {'name': 'Silver', 'badge': '🥈 Halfway There', 'class': 'badge-info'}
        elif pct >= 25:
            milestone = {'name': 'Bronze', 'badge': '🥉 25% Started', 'class': 'badge-warning'}
        else:
            milestone = {'name': 'Started', 'badge': '🌱 Just Started', 'class': 'badge-secondary'}

        formatted.append({
            'id': g.get('id'),
            'title': g.get('title'),
            'target_amount': target,
            'current_amount': current,
            'remaining_amount': max(0.0, target - current),
            'percentage': round(pct, 1),
            'percentage_display': pct_display,
            'target_date': target_date_str,
            'days_remaining': days_remaining,
            'category': g.get('category', 'Savings'),
            'notes': g.get('notes', ''),
            'status': status,
            'milestone': milestone,
            'created_at': g.get('created_at', '')
        })

    overall_pct = (total_saved / total_target * 100) if total_target > 0 else 0

    return jsonify({
        'success': True,
        'goals': formatted,
        'summary': {
            'total_target': total_target,
            'total_saved': total_saved,
            'overall_percentage': round(overall_pct, 1),
            'total_goals': len(user_goals),
            'completed_count': completed_count,
            'in_progress_count': len(user_goals) - completed_count
        }
    })

@app.route('/api/goals', methods=['POST'])
@login_required
def api_add_goal():
    user_id = session['user_id']
    data = request.get_json() or {}

    title = data.get('title', '').strip()
    target_raw = data.get('target_amount', 0)
    current_raw = data.get('current_amount', 0)
    target_date = data.get('target_date', '').strip()
    category = data.get('category', 'Savings').strip()
    notes = data.get('notes', '').strip()

    if not title or not target_date:
        return jsonify({'success': False, 'message': 'Title and Target Date are required.'}), 400

    try:
        target_amount = float(target_raw)
        current_amount = float(current_raw)
        if target_amount <= 0:
            return jsonify({'success': False, 'message': 'Target amount must be greater than zero.'}), 400
        if current_amount < 0:
            current_amount = 0.0
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid target or current amount.'}), 400

    goal_id = str(csv_db.get_next_id(csv_db.GOALS_CSV))
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_goal = {
        'id': goal_id,
        'user_id': user_id,
        'title': title,
        'target_amount': f"{target_amount:.2f}",
        'current_amount': f"{current_amount:.2f}",
        'target_date': target_date,
        'category': category,
        'notes': notes,
        'created_at': now_str
    }

    fieldnames = ['id', 'user_id', 'title', 'target_amount', 'current_amount', 'target_date', 'category', 'notes', 'created_at']
    csv_db.append_csv(csv_db.GOALS_CSV, fieldnames, new_goal)

    return jsonify({'success': True, 'message': f"Goal '{title}' created successfully!", 'goal': new_goal})

@app.route('/api/goals/<int:goal_id>', methods=['PUT'])
@login_required
def api_update_goal(goal_id):
    user_id = session['user_id']
    data = request.get_json() or {}

    all_goals = csv_db.read_csv(csv_db.GOALS_CSV)
    idx = -1
    for i, g in enumerate(all_goals):
        if g.get('id') == str(goal_id) and g.get('user_id') == user_id:
            idx = i
            break

    if idx == -1:
        return jsonify({'success': False, 'message': 'Goal not found or unauthorized.'}), 404

    title = data.get('title', all_goals[idx]['title']).strip()
    target_date = data.get('target_date', all_goals[idx]['target_date']).strip()
    category = data.get('category', all_goals[idx].get('category', 'Savings')).strip()
    notes = data.get('notes', all_goals[idx].get('notes', '')).strip()

    try:
        target_amount = float(data.get('target_amount', all_goals[idx]['target_amount']))
        current_amount = float(data.get('current_amount', all_goals[idx]['current_amount']))
        if target_amount <= 0 or current_amount < 0:
            return jsonify({'success': False, 'message': 'Amounts must be valid positive numbers.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount value.'}), 400

    all_goals[idx]['title'] = title
    all_goals[idx]['target_amount'] = f"{target_amount:.2f}"
    all_goals[idx]['current_amount'] = f"{current_amount:.2f}"
    all_goals[idx]['target_date'] = target_date
    all_goals[idx]['category'] = category
    all_goals[idx]['notes'] = notes

    fieldnames = ['id', 'user_id', 'title', 'target_amount', 'current_amount', 'target_date', 'category', 'notes', 'created_at']
    csv_db.write_csv(csv_db.GOALS_CSV, fieldnames, all_goals)

    return jsonify({'success': True, 'message': 'Goal updated successfully!', 'goal': all_goals[idx]})

@app.route('/api/goals/<int:goal_id>/contribute', methods=['POST'])
@login_required
def api_contribute_goal(goal_id):
    user_id = session['user_id']
    data = request.get_json() or {}
    amount_raw = data.get('amount', 0)
    record_expense = data.get('record_expense', False)
    payment_method = data.get('payment_method', 'UPI')

    try:
        contrib = float(amount_raw)
        if contrib <= 0:
            return jsonify({'success': False, 'message': 'Contribution must be greater than zero.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid deposit amount.'}), 400

    all_goals = csv_db.read_csv(csv_db.GOALS_CSV)
    idx = -1
    for i, g in enumerate(all_goals):
        if g.get('id') == str(goal_id) and g.get('user_id') == user_id:
            idx = i
            break

    if idx == -1:
        return jsonify({'success': False, 'message': 'Goal not found or unauthorized.'}), 404

    current = float(all_goals[idx].get('current_amount', 0))
    target = float(all_goals[idx].get('target_amount', 0))
    new_current = current + contrib
    all_goals[idx]['current_amount'] = f"{new_current:.2f}"

    fieldnames = ['id', 'user_id', 'title', 'target_amount', 'current_amount', 'target_date', 'category', 'notes', 'created_at']
    csv_db.write_csv(csv_db.GOALS_CSV, fieldnames, all_goals)

    # Optional: Log as transaction
    if record_expense:
        exp_id = str(csv_db.get_next_id(csv_db.EXPENSES_CSV))
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        new_exp = {
            'id': exp_id,
            'user_id': user_id,
            'date': datetime.now().strftime('%Y-%m-%d'),
            'description': f"Deposit to Goal: {all_goals[idx]['title']}",
            'category': 'Investment',
            'amount': f"{contrib:.2f}",
            'payment_method': payment_method,
            'type': 'Expense',
            'notes': f"Direct savings transfer into {all_goals[idx]['title']}",
            'created_at': now_str
        }
        exp_fields = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
        csv_db.append_csv(csv_db.EXPENSES_CSV, exp_fields, new_exp)

    new_pct = (new_current / target * 100) if target > 0 else 0
    return jsonify({
        'success': True,
        'message': f"Added ₹{contrib:,.2f} to '{all_goals[idx]['title']}'! New progress: {new_pct:.1f}%",
        'current_amount': new_current,
        'percentage': round(new_pct, 1)
    })

@app.route('/api/goals/<int:goal_id>', methods=['DELETE'])
@login_required
def api_delete_goal(goal_id):
    user_id = session['user_id']
    all_goals = csv_db.read_csv(csv_db.GOALS_CSV)
    new_goals = [g for g in all_goals if not (g.get('id') == str(goal_id) and g.get('user_id') == user_id)]

    if len(new_goals) == len(all_goals):
        return jsonify({'success': False, 'message': 'Goal not found or unauthorized.'}), 404

    fieldnames = ['id', 'user_id', 'title', 'target_amount', 'current_amount', 'target_date', 'category', 'notes', 'created_at']
    csv_db.write_csv(csv_db.GOALS_CSV, fieldnames, new_goals)

    return jsonify({'success': True, 'message': 'Savings goal removed.'})


# --- RECURRING SUBSCRIPTIONS APIs ---

@app.route('/api/subscriptions', methods=['GET'])
@login_required
def api_get_subscriptions():
    user_id = session['user_id']
    all_subs = csv_db.read_csv(csv_db.SUBSCRIPTIONS_CSV)
    user_subs = [s for s in all_subs if s.get('user_id') == user_id]

    today = datetime.now().date()
    formatted = []
    total_monthly = 0.0
    total_yearly = 0.0
    active_count = 0
    renewing_soon_count = 0

    for s in user_subs:
        try:
            amt = float(s.get('amount', 0))
        except (ValueError, TypeError):
            amt = 0.0

        cycle = s.get('billing_cycle', 'Monthly')
        status = s.get('status', 'Active')

        # Normalize to monthly and yearly cost
        if cycle == 'Weekly':
            monthly_equiv = amt * (52.0 / 12.0)
            yearly_equiv = amt * 52.0
        elif cycle == 'Yearly':
            monthly_equiv = amt / 12.0
            yearly_equiv = amt
        elif cycle == 'Quarterly':
            monthly_equiv = amt / 3.0
            yearly_equiv = amt * 4.0
        else: # Monthly
            monthly_equiv = amt
            yearly_equiv = amt * 12.0

        if status == 'Active':
            total_monthly += monthly_equiv
            total_yearly += yearly_equiv
            active_count += 1

        # Days until next billing
        days_until = None
        next_date_str = s.get('next_billing_date', '')
        if next_date_str:
            try:
                b_date = datetime.strptime(next_date_str, '%Y-%m-%d').date()
                days_until = (b_date - today).days
                if status == 'Active' and 0 <= days_until <= 7:
                    renewing_soon_count += 1
            except ValueError:
                pass

        formatted.append({
            'id': s.get('id'),
            'name': s.get('name'),
            'amount': amt,
            'monthly_equivalent': round(monthly_equiv, 2),
            'yearly_equivalent': round(yearly_equiv, 2),
            'billing_cycle': cycle,
            'next_billing_date': next_date_str,
            'days_until_renewal': days_until,
            'category': s.get('category', 'Entertainment'),
            'payment_method': s.get('payment_method', 'UPI'),
            'status': status,
            'created_at': s.get('created_at', '')
        })

    # Sort: active first, then soonest renewal
    formatted.sort(key=lambda x: (0 if x['status'] == 'Active' else 1, x['days_until_renewal'] if x['days_until_renewal'] is not None else 9999))

    return jsonify({
        'success': True,
        'subscriptions': formatted,
        'summary': {
            'total_monthly': round(total_monthly, 2),
            'total_yearly': round(total_yearly, 2),
            'active_count': active_count,
            'total_subscriptions': len(user_subs),
            'renewing_soon_count': renewing_soon_count
        }
    })

@app.route('/api/subscriptions', methods=['POST'])
@login_required
def api_add_subscription():
    user_id = session['user_id']
    data = request.get_json() or {}

    name = data.get('name', '').strip()
    amount_raw = data.get('amount', 0)
    cycle = data.get('billing_cycle', 'Monthly').strip()
    next_date = data.get('next_billing_date', '').strip()
    category = data.get('category', 'Entertainment').strip()
    payment_method = data.get('payment_method', 'Credit Card').strip()
    status = data.get('status', 'Active').strip()

    if not name or not next_date:
        return jsonify({'success': False, 'message': 'Subscription name and Next Billing Date are required.'}), 400

    try:
        amount = float(amount_raw)
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
    except (ValueError, TypeError):
        return jsonify({'success': False, 'message': 'Invalid amount.'}), 400

    sub_id = str(csv_db.get_next_id(csv_db.SUBSCRIPTIONS_CSV))
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_sub = {
        'id': sub_id,
        'user_id': user_id,
        'name': name,
        'amount': f"{amount:.2f}",
        'billing_cycle': cycle,
        'next_billing_date': next_date,
        'category': category,
        'payment_method': payment_method,
        'status': status,
        'created_at': now_str
    }

    fieldnames = ['id', 'user_id', 'name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'payment_method', 'status', 'created_at']
    csv_db.append_csv(csv_db.SUBSCRIPTIONS_CSV, fieldnames, new_sub)

    return jsonify({'success': True, 'message': f"Subscription '{name}' added successfully!", 'subscription': new_sub})

@app.route('/api/subscriptions/<int:sub_id>', methods=['PUT'])
@login_required
def api_update_subscription(sub_id):
    user_id = session['user_id']
    data = request.get_json() or {}

    all_subs = csv_db.read_csv(csv_db.SUBSCRIPTIONS_CSV)
    idx = -1
    for i, s in enumerate(all_subs):
        if s.get('id') == str(sub_id) and s.get('user_id') == user_id:
            idx = i
            break

    if idx == -1:
        return jsonify({'success': False, 'message': 'Subscription not found or unauthorized.'}), 404

    # Allow partial toggle of status or full edit
    if 'status' in data and len(data) == 1:
        all_subs[idx]['status'] = data['status']
    else:
        all_subs[idx]['name'] = data.get('name', all_subs[idx]['name']).strip()
        all_subs[idx]['billing_cycle'] = data.get('billing_cycle', all_subs[idx]['billing_cycle']).strip()
        all_subs[idx]['next_billing_date'] = data.get('next_billing_date', all_subs[idx]['next_billing_date']).strip()
        all_subs[idx]['category'] = data.get('category', all_subs[idx]['category']).strip()
        all_subs[idx]['payment_method'] = data.get('payment_method', all_subs[idx]['payment_method']).strip()
        all_subs[idx]['status'] = data.get('status', all_subs[idx]['status']).strip()

        if 'amount' in data:
            try:
                amt = float(data['amount'])
                if amt <= 0:
                    return jsonify({'success': False, 'message': 'Amount must be greater than zero.'}), 400
                all_subs[idx]['amount'] = f"{amt:.2f}"
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid amount.'}), 400

    fieldnames = ['id', 'user_id', 'name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'payment_method', 'status', 'created_at']
    csv_db.write_csv(csv_db.SUBSCRIPTIONS_CSV, fieldnames, all_subs)

    return jsonify({'success': True, 'message': 'Subscription updated successfully!', 'subscription': all_subs[idx]})

@app.route('/api/subscriptions/<int:sub_id>/log-expense', methods=['POST'])
@login_required
def api_log_subscription_expense(sub_id):
    user_id = session['user_id']
    all_subs = csv_db.read_csv(csv_db.SUBSCRIPTIONS_CSV)
    idx = -1
    for i, s in enumerate(all_subs):
        if s.get('id') == str(sub_id) and s.get('user_id') == user_id:
            idx = i
            break

    if idx == -1:
        return jsonify({'success': False, 'message': 'Subscription not found.'}), 404

    sub = all_subs[idx]
    amt = float(sub.get('amount', 0))

    # Log into expenses
    exp_id = str(csv_db.get_next_id(csv_db.EXPENSES_CSV))
    today_str = datetime.now().strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    new_item = {
        'id': exp_id,
        'user_id': user_id,
        'date': today_str,
        'description': f"Subscription: {sub.get('name')}",
        'category': sub.get('category', 'Entertainment'),
        'amount': f"{amt:.2f}",
        'payment_method': sub.get('payment_method', 'Credit Card'),
        'type': 'Expense',
        'notes': f"Auto-recorded recurring subscription payment ({sub.get('billing_cycle', 'Monthly')})",
        'created_at': now_str
    }
    exp_fields = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
    csv_db.append_csv(csv_db.EXPENSES_CSV, exp_fields, new_item)

    # Advance next billing date
    try:
        curr_bdate = datetime.strptime(sub.get('next_billing_date', today_str), '%Y-%m-%d')
        cycle = sub.get('billing_cycle', 'Monthly')
        if cycle == 'Yearly':
            next_bdate = curr_bdate.replace(year=curr_bdate.year + 1)
        elif cycle == 'Weekly':
            next_bdate = curr_bdate + timedelta(days=7)
        elif cycle == 'Quarterly':
            next_bdate = curr_bdate + timedelta(days=90)
        else: # Monthly
            # Rough month advance
            new_month = curr_bdate.month + 1
            new_year = curr_bdate.year
            if new_month > 12:
                new_month = 1
                new_year += 1
            day = min(curr_bdate.day, 28)
            next_bdate = curr_bdate.replace(year=new_year, month=new_month, day=day)

        all_subs[idx]['next_billing_date'] = next_bdate.strftime('%Y-%m-%d')
        sub_fields = ['id', 'user_id', 'name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'payment_method', 'status', 'created_at']
        csv_db.write_csv(csv_db.SUBSCRIPTIONS_CSV, sub_fields, all_subs)
    except Exception as e:
        print("Date advance notice:", e)

    return jsonify({
        'success': True,
        'message': f"Logged payment of ₹{amt:,.2f} for '{sub.get('name')}' as an Expense!",
        'next_billing_date': all_subs[idx]['next_billing_date']
    })

@app.route('/api/subscriptions/<int:sub_id>', methods=['DELETE'])
@login_required
def api_delete_subscription(sub_id):
    user_id = session['user_id']
    all_subs = csv_db.read_csv(csv_db.SUBSCRIPTIONS_CSV)
    new_subs = [s for s in all_subs if not (s.get('id') == str(sub_id) and s.get('user_id') == user_id)]

    if len(new_subs) == len(all_subs):
        return jsonify({'success': False, 'message': 'Subscription not found or unauthorized.'}), 404

    fieldnames = ['id', 'user_id', 'name', 'amount', 'billing_cycle', 'next_billing_date', 'category', 'payment_method', 'status', 'created_at']
    csv_db.write_csv(csv_db.SUBSCRIPTIONS_CSV, fieldnames, new_subs)

    return jsonify({'success': True, 'message': 'Subscription removed.'})


# --- FINANCIAL HEALTH SCORE & SMART INSIGHTS API ---

@app.route('/api/analytics/financial-health', methods=['GET'])
@login_required
def api_financial_health():
    user_id = session['user_id']
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    user_expenses = [e for e in all_expenses if e.get('user_id') == user_id]

    total_income = sum(float(e['amount']) for e in user_expenses if e.get('type') == 'Income')
    total_expenses = sum(float(e['amount']) for e in user_expenses if e.get('type') == 'Expense')
    net_savings = total_income - total_expenses

    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

    # 50/30/20 Rule Classification
    needs_categories = {'housing', 'rent', 'food', 'bills', 'transport', 'health', 'recharge', 'education', 'utilities', 'grocery'}
    wants_categories = {'entertainment', 'shopping', 'travel', 'dining out', 'cinema', 'leisure', 'other'}

    needs_total = 0.0
    wants_total = 0.0
    category_totals = {}

    for e in user_expenses:
        if e.get('type') == 'Expense':
            amt = float(e.get('amount', 0))
            cat = e.get('category', 'Other')
            cat_lower = cat.lower()
            category_totals[cat] = category_totals.get(cat, 0.0) + amt

            if any(k in cat_lower for k in needs_categories):
                needs_total += amt
            elif any(k in cat_lower for k in wants_categories):
                wants_total += amt
            else:
                needs_total += amt * 0.7
                wants_total += amt * 0.3

    base_denom = total_income if total_income > 0 else (total_expenses if total_expenses > 0 else 1)
    needs_pct = round((needs_total / base_denom * 100), 1)
    wants_pct = round((wants_total / base_denom * 100), 1)
    savings_pct = round(max(0.0, (net_savings / base_denom * 100)), 1) if total_income > 0 else 0.0

    # Budget Adherence Component
    now = datetime.now()
    cur_m = now.strftime('%m')
    cur_y = now.strftime('%Y')
    all_budgets = csv_db.read_csv(csv_db.BUDGETS_CSV)
    user_budgets = [b for b in all_budgets if b.get('user_id') == user_id and b.get('month') == cur_m and b.get('year') == cur_y]

    budget_passed = 0
    exceeded_categories = []
    for b in user_budgets:
        cat = b.get('category')
        b_amt = float(b.get('amount', 0))
        c_spent = category_totals.get(cat, 0.0)
        if c_spent <= b_amt:
            budget_passed += 1
        else:
            exceeded_categories.append(cat)

    adherence_pct = (budget_passed / len(user_budgets) * 100) if user_budgets else 90.0

    # Composite Health Score Calculation (0 - 100)
    # 1. Savings Rate: up to 35 pts
    if savings_rate >= 25:
        score_savings = 35
    elif savings_rate >= 20:
        score_savings = 30
    elif savings_rate >= 10:
        score_savings = 20
    elif savings_rate > 0:
        score_savings = 10
    else:
        score_savings = 0

    # 2. 50/30/20 Balance: up to 30 pts (Needs <= 50% => 15 pts, Wants <= 30% => 15 pts)
    score_needs = 15 if needs_pct <= 50 else max(5, 15 - int((needs_pct - 50) * 0.5))
    score_wants = 15 if wants_pct <= 30 else max(5, 15 - int((wants_pct - 30) * 0.5))
    score_balance = score_needs + score_wants

    # 3. Budget Discipline: up to 20 pts
    score_discipline = round(adherence_pct * 0.20)

    # 4. Solvency / Net Balance: up to 15 pts
    score_solvency = 15 if net_savings > 0 else 0

    total_score = min(100, max(15, score_savings + score_balance + score_discipline + score_solvency))

    # Grade & Rating Label
    if total_score >= 85:
        grade = 'A+'
        rating = 'Excellent'
        color = '#10b981'
    elif total_score >= 75:
        grade = 'A'
        rating = 'Strong'
        color = '#3b82f6'
    elif total_score >= 60:
        grade = 'B'
        rating = 'Moderate'
        color = '#f59e0b'
    elif total_score >= 45:
        grade = 'C'
        rating = 'Needs Focus'
        color = '#f97316'
    else:
        grade = 'D'
        rating = 'Action Required'
        color = '#ef4444'

    # Smart Tailored Insights
    insights = []
    if savings_rate >= 20:
        insights.append({
            'type': 'success',
            'icon': 'fa-circle-check',
            'title': 'Outstanding Savings Discipline',
            'text': f"Your savings rate is {savings_rate:.1f}%, beating the benchmark 20% target. Keep this momentum to build long-term wealth!"
        })
    elif savings_rate > 0:
        insights.append({
            'type': 'info',
            'icon': 'fa-lightbulb',
            'title': 'Room for Savings Growth',
            'text': f"You are saving {savings_rate:.1f}% of income. Increasing monthly savings to 20% will add ₹{base_denom * 0.20 - net_savings:,.0f} to your safety net."
        })
    else:
        insights.append({
            'type': 'danger',
            'icon': 'fa-triangle-exclamation',
            'title': 'Negative Cashflow Alert',
            'text': "Your total spending is currently outpacing income. Review discretionary subscriptions and dining to restore positive cash flow."
        })

    # Top spending category insight
    sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
    if sorted_cats:
        top_cat, top_amt = sorted_cats[0]
        top_cat_pct = (top_amt / total_expenses * 100) if total_expenses > 0 else 0
        insights.append({
            'type': 'warning' if top_cat_pct > 30 else 'info',
            'icon': 'fa-chart-pie',
            'title': f"Top Spending Area: {top_cat}",
            'text': f"{top_cat} makes up {top_cat_pct:.1f}% (₹{top_amt:,.2f}) of your total expenses. Consider setting a strict monthly budget cap for it."
        })

    # Subscriptions audit insight
    all_subs = csv_db.read_csv(csv_db.SUBSCRIPTIONS_CSV)
    user_subs = [s for s in all_subs if s.get('user_id') == user_id and s.get('status') == 'Active']
    if user_subs:
        sub_monthly_total = sum(float(s.get('amount', 0)) for s in user_subs if s.get('billing_cycle') == 'Monthly')
        insights.append({
            'type': 'info',
            'icon': 'fa-arrows-rotate',
            'title': f"{len(user_subs)} Active Subscriptions",
            'text': f"You have {len(user_subs)} recurring services (~₹{sub_monthly_total:,.2f}/mo). Auditing unused memberships could save you hundreds."
        })

    return jsonify({
        'success': True,
        'health_score': total_score,
        'grade': grade,
        'rating': rating,
        'color': color,
        'breakdown': {
            'savings_rate': round(savings_rate, 1),
            'needs_pct': needs_pct,
            'wants_pct': wants_pct,
            'savings_pct': savings_pct,
            'budget_adherence_pct': round(adherence_pct, 1),
            'target_rules': {'needs': 50, 'wants': 30, 'savings': 20}
        },
        'component_scores': {
            'savings': score_savings,
            'rule_50_30_20': score_balance,
            'discipline': score_discipline,
            'solvency': score_solvency
        },
        'insights': insights
    })


# --- CSV DATA IMPORT & TEMPLATE APIs ---

@app.route('/api/import/csv', methods=['POST'])
@login_required
def api_import_csv():
    user_id = session['user_id']
    
    file_content = None
    if 'file' in request.files:
        uploaded_file = request.files['file']
        if uploaded_file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected.'}), 400
        try:
            file_content = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError:
            try:
                uploaded_file.seek(0)
                file_content = uploaded_file.read().decode('latin-1')
            except Exception:
                return jsonify({'success': False, 'message': 'Could not read CSV file encoding.'}), 400
    else:
        data = request.get_json() or {}
        file_content = data.get('csv_data', '')

    if not file_content or not file_content.strip():
        return jsonify({'success': False, 'message': 'Uploaded file is empty.'}), 400

    reader = csv.DictReader(io.StringIO(file_content))
    fieldnames = [f.strip().lower() for f in (reader.fieldnames or [])]

    # Helper to find column by variations
    def find_col(aliases):
        for a in aliases:
            for f in fieldnames:
                if a in f:
                    return f
        return None

    col_date = find_col(['date', 'txn_date', 'txndate', 'time'])
    col_desc = find_col(['desc', 'description', 'narration', 'particulars', 'title', 'name'])
    col_amount = find_col(['amount', 'amt', 'value', 'price'])
    col_category = find_col(['category', 'cat', 'tag'])
    col_method = find_col(['payment_method', 'method', 'mode', 'payment'])
    col_type = find_col(['type', 'txn_type', 'cr/dr', 'transaction_type'])
    col_notes = find_col(['notes', 'remark', 'remarks', 'comment'])

    if not col_amount:
        return jsonify({'success': False, 'message': "CSV must contain an 'Amount' column."}), 400

    imported_count = 0
    skipped_count = 0
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    today_str = datetime.now().strftime('%Y-%m-%d')

    new_rows = []
    all_expenses = csv_db.read_csv(csv_db.EXPENSES_CSV)
    next_id = csv_db.get_next_id(csv_db.EXPENSES_CSV)

    # Reset StringIO stream
    reader = csv.DictReader(io.StringIO(file_content))

    for row in reader:
        # Match case-insensitive keys
        row_normalized = {k.strip().lower(): v.strip() for k, v in row.items() if k}

        # Date
        txn_date = row_normalized.get(col_date, today_str) if col_date else today_str
        if not txn_date or len(txn_date) < 8:
            txn_date = today_str
        # Standardize YYYY-MM-DD if possible
        try:
            if '/' in txn_date:
                parts = txn_date.split('/')
                if len(parts[2]) == 4:
                    txn_date = f"{parts[2]}-{parts[1].zfill(2)}-{parts[0].zfill(2)}"
        except Exception:
            txn_date = today_str

        # Amount
        raw_amt_str = row_normalized.get(col_amount, '0').replace(',', '').replace('₹', '').replace('$', '').strip()
        try:
            amt = abs(float(raw_amt_str))
            if amt == 0:
                skipped_count += 1
                continue
        except (ValueError, TypeError):
            skipped_count += 1
            continue

        # Description
        desc = row_normalized.get(col_desc, 'Imported Transaction') if col_desc else 'Imported Transaction'
        if not desc:
            desc = 'Imported Transaction'

        # Category
        cat = row_normalized.get(col_category, 'Other') if col_category else 'Other'
        if not cat:
            cat = 'Other'

        # Payment Method
        method = row_normalized.get(col_method, 'UPI') if col_method else 'UPI'
        if not method:
            method = 'UPI'

        # Type (Expense or Income)
        t_type = 'Expense'
        if col_type and col_type in row_normalized:
            raw_t = row_normalized[col_type].strip().lower()
            if 'inc' in raw_t or 'cr' in raw_t or 'deposit' in raw_t:
                t_type = 'Income'
        notes = row_normalized.get(col_notes, 'Imported via CSV') if col_notes else 'Imported via CSV'

        new_rows.append({
            'id': str(next_id),
            'user_id': user_id,
            'date': txn_date,
            'description': desc,
            'category': cat,
            'amount': f"{amt:.2f}",
            'payment_method': method,
            'type': t_type,
            'notes': notes,
            'created_at': now_str
        })
        next_id += 1
        imported_count += 1

    if imported_count == 0:
        return jsonify({'success': False, 'message': 'No valid transactions found in the file to import.'}), 400

    fieldnames = ['id', 'user_id', 'date', 'description', 'category', 'amount', 'payment_method', 'type', 'notes', 'created_at']
    for r in new_rows:
        csv_db.append_csv(csv_db.EXPENSES_CSV, fieldnames, r)

    return jsonify({
        'success': True,
        'imported': imported_count,
        'skipped': skipped_count,
        'message': f"Successfully imported {imported_count} transactions! ({skipped_count} skipped/invalid)"
    })

@app.route('/api/export/template', methods=['GET'])
@login_required
def api_export_template():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Description', 'Category', 'Amount', 'Payment Method', 'Type', 'Notes'])
    writer.writerow(['2026-09-01', 'Monthly Salary', 'Salary', '50000', 'Bank Transfer', 'Income', 'Company payroll'])
    writer.writerow(['2026-09-02', 'House Rent', 'Housing', '12000', 'Net Banking', 'Expense', 'Monthly apartment rent'])
    writer.writerow(['2026-09-05', 'Grocery Supermarket', 'Food', '3250', 'UPI', 'Expense', 'Household supplies'])
    writer.writerow(['2026-09-10', 'Coffee with Client', 'Food', '450', 'Cash', 'Expense', 'Afternoon cafe meeting'])
    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=expense_tracker_import_template.csv"}
    )



# --- FRIENDS & CONTACTS ---

@app.route('/friends')
@login_required
def friends_page():
    return render_template('friends.html')


@app.route('/api/friends', methods=['GET'])
@login_required
def api_list_friends():
    """Return accepted friends with their user details."""
    uid = session['user_id']
    all_friends = csv_db.read_csv(csv_db.FRIENDS_CSV)
    users = csv_db.read_csv(csv_db.USERS_CSV)
    user_map = {u['id']: u for u in users}

    result = []
    for f in all_friends:
        if f.get('status') != 'accepted':
            continue
        if f.get('user_id') == uid:
            fid = f.get('friend_user_id')
        elif f.get('friend_user_id') == uid:
            fid = f.get('user_id')
        else:
            continue
        fu = user_map.get(fid)
        if fu:
            result.append({'id': fid, 'name': fu['name'], 'email': fu['email'], 'friendship_id': f['id']})
    return jsonify({'success': True, 'friends': result})


@app.route('/api/friends/requests', methods=['GET'])
@login_required
def api_list_friend_requests():
    """Return pending friend requests sent TO the current user."""
    uid = session['user_id']
    all_friends = csv_db.read_csv(csv_db.FRIENDS_CSV)
    users = csv_db.read_csv(csv_db.USERS_CSV)
    user_map = {u['id']: u for u in users}

    incoming = []
    for f in all_friends:
        if f.get('friend_user_id') == uid and f.get('status') == 'pending':
            sender = user_map.get(f.get('user_id'))
            if sender:
                incoming.append({'id': f['id'], 'name': sender['name'], 'email': sender['email']})
    return jsonify({'success': True, 'requests': incoming})


@app.route('/api/users/search', methods=['GET'])
@login_required
def api_search_users():
    """Search registered users by name, mobile number, or email."""
    q = request.args.get('q', '').strip().lower()
    if not q or len(q) < 2:
        return jsonify({'success': True, 'users': []})

    uid = session.get('user_id')
    clean_q_digits = normalize_phone(q)
    users = csv_db.read_csv(csv_db.USERS_CSV)
    results = []

    for u in users:
        if u['id'] == uid:
            continue
        u_phone = normalize_phone(u.get('phone', ''))
        u_email = u.get('email', '').lower()
        u_name = u.get('name', '').lower()

        # Match by name, email, or mobile number
        match = (q in u_name) or (q in u_email) or (clean_q_digits and clean_q_digits in u_phone)
        if match:
            results.append({
                'id': u['id'],
                'name': u['name'],
                'email': u['email'],
                'phone': u.get('phone', '')
            })

    return jsonify({'success': True, 'users': results[:10]})


@app.route('/api/friends/add', methods=['POST'])
@login_required
def api_add_friend():
    """Send a friend request by registered mobile number or email."""
    uid = session['user_id']
    data = request.get_json() or {}
    identifier = (data.get('identifier', '') or data.get('email', '') or data.get('phone', '')).strip().lower()

    if not identifier:
        return jsonify({'success': False, 'message': 'Mobile number or email is required.'}), 400

    clean_digits = normalize_phone(identifier)
    users = csv_db.read_csv(csv_db.USERS_CSV)
    target = None

    for u in users:
        if u.get('email', '').strip().lower() == identifier:
            target = u
            break
        if clean_digits and len(clean_digits) >= 10:
            u_phone = normalize_phone(u.get('phone', ''))
            if u_phone == clean_digits:
                target = u
                break

    if not target:
        return jsonify({'success': False, 'message': 'No registered user found with that mobile number or email.'}), 404
    if target['id'] == uid:
        return jsonify({'success': False, 'message': 'You cannot add yourself as a friend.'}), 400

    # Check if already friends or request pending
    all_friends = csv_db.read_csv(csv_db.FRIENDS_CSV)
    for f in all_friends:
        pair = {f.get('user_id'), f.get('friend_user_id')}
        if pair == {uid, target['id']}:
            if f.get('status') == 'accepted':
                return jsonify({'success': False, 'message': f"{target['name']} is already in your contacts."}), 400
            if f.get('status') == 'pending':
                return jsonify({'success': False, 'message': 'A friend request is already pending.'}), 400

    fid = str(csv_db.get_next_id(csv_db.FRIENDS_CSV))
    csv_db.append_csv(csv_db.FRIENDS_CSV,
        ['id', 'user_id', 'friend_user_id', 'status', 'created_at'],
        {'id': fid, 'user_id': uid, 'friend_user_id': target['id'], 'status': 'pending',
         'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
    return jsonify({'success': True, 'message': f"Friend request sent to {target['name']}!"})


@app.route('/api/friends/<string:friendship_id>/accept', methods=['POST'])
@login_required
def api_accept_friend(friendship_id):
    uid = session['user_id']
    rows = csv_db.read_csv(csv_db.FRIENDS_CSV)
    updated = False
    for r in rows:
        if r['id'] == friendship_id and r.get('friend_user_id') == uid and r.get('status') == 'pending':
            r['status'] = 'accepted'
            updated = True
            break
    if not updated:
        return jsonify({'success': False, 'message': 'Request not found.'}), 404
    csv_db.write_csv(csv_db.FRIENDS_CSV, ['id', 'user_id', 'friend_user_id', 'status', 'created_at'], rows)
    return jsonify({'success': True, 'message': 'Friend request accepted!'})


@app.route('/api/friends/<string:friendship_id>/reject', methods=['POST'])
@login_required
def api_reject_friend(friendship_id):
    uid = session['user_id']
    rows = csv_db.read_csv(csv_db.FRIENDS_CSV)
    new_rows = [r for r in rows if not (r['id'] == friendship_id and r.get('friend_user_id') == uid)]
    if len(new_rows) == len(rows):
        return jsonify({'success': False, 'message': 'Request not found.'}), 404
    csv_db.write_csv(csv_db.FRIENDS_CSV, ['id', 'user_id', 'friend_user_id', 'status', 'created_at'], new_rows)
    return jsonify({'success': True, 'message': 'Friend request declined.'})


@app.route('/api/friends/<string:friendship_id>', methods=['DELETE'])
@login_required
def api_remove_friend(friendship_id):
    uid = session['user_id']
    rows = csv_db.read_csv(csv_db.FRIENDS_CSV)
    new_rows = [r for r in rows if not (r['id'] == friendship_id and uid in {r.get('user_id'), r.get('friend_user_id')})]
    if len(new_rows) == len(rows):
        return jsonify({'success': False, 'message': 'Friend not found.'}), 404
    csv_db.write_csv(csv_db.FRIENDS_CSV, ['id', 'user_id', 'friend_user_id', 'status', 'created_at'], new_rows)
    return jsonify({'success': True, 'message': 'Friend removed.'})


# --- SHARED EXPENSES ---

@app.route('/api/shared-expenses', methods=['POST'])
@login_required
def api_add_shared_expense():
    """Log an expense shared with one or more friends."""
    uid = session['user_id']
    data = request.get_json() or {}
    payee_ids = data.get('payee_ids', [])   # list of friend user IDs
    amount_total = float(data.get('amount', 0))
    description = data.get('description', '').strip()
    split_type = data.get('split_type', 'equal')  # equal | custom

    if not payee_ids or not description or amount_total <= 0:
        return jsonify({'success': False, 'message': 'Amount, description and at least one friend are required.'}), 400

    share = round(amount_total / (len(payee_ids) + 1), 2)
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    added = 0
    for pid in payee_ids:
        eid = str(csv_db.get_next_id(csv_db.SHARED_EXPENSES_CSV))
        csv_db.append_csv(csv_db.SHARED_EXPENSES_CSV,
            ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'],
            {'id': eid, 'payer_user_id': uid, 'payee_user_id': pid,
             'amount': f"{share:.2f}", 'description': description,
             'split_type': split_type, 'status': 'pending', 'created_at': now_str})
        added += 1
    return jsonify({'success': True, 'message': f'Shared expense recorded for {added} friend(s). Each owes ₹{share:.2f}.'})


@app.route('/api/shared-expenses', methods=['GET'])
@login_required
def api_list_shared_expenses():
    """List all shared expenses involving the current user."""
    uid = session['user_id']
    all_se = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    users = csv_db.read_csv(csv_db.USERS_CSV)
    user_map = {u['id']: u for u in users}

    owed_to_me = []   # I paid, friend owes me
    i_owe = []        # Friend paid, I owe them

    for s in all_se:
        if s.get('payer_user_id') == uid:
            payee = user_map.get(s.get('payee_user_id'))
            owed_to_me.append({**s, 'friend_name': payee['name'] if payee else 'Unknown', 'friend_email': payee['email'] if payee else ''})
        elif s.get('payee_user_id') == uid:
            payer = user_map.get(s.get('payer_user_id'))
            i_owe.append({**s, 'friend_name': payer['name'] if payer else 'Unknown', 'friend_email': payer['email'] if payer else ''})

    return jsonify({'success': True, 'owed_to_me': owed_to_me, 'i_owe': i_owe})


@app.route('/api/shared-expenses/<string:se_id>/settle', methods=['POST'])
@login_required
def api_settle_shared_expense(se_id):
    uid = session['user_id']
    rows = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    updated = False
    for r in rows:
        if r['id'] == se_id and uid in {r.get('payer_user_id'), r.get('payee_user_id')}:
            r['status'] = 'settled'
            updated = True
            break
    if not updated:
        return jsonify({'success': False, 'message': 'Shared expense not found.'}), 404
    csv_db.write_csv(csv_db.SHARED_EXPENSES_CSV,
        ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'], rows)
    return jsonify({'success': True, 'message': 'Marked as settled!'})


# --- SPLIT ROOMS (LIVE ROOM CODES & SHARING) ---

@app.route('/api/split-rooms', methods=['POST'])
@login_required
def api_create_split_room():
    """Create a live shareable Split Room with a unique Room Code."""
    uid = session['user_id']
    creator_name = session.get('user_name', 'Host')
    data = request.get_json() or {}

    title = data.get('title', '').strip() or 'Group Split'
    total_amount = float(data.get('total_amount', 0))
    tip_pct = float(data.get('tip_pct', 0))
    tax_pct = float(data.get('tax_pct', 0))
    split_type = data.get('split_type', 'equal')
    members_data = data.get('members', [])  # list of { name, contact, share_amount, user_id }

    if total_amount <= 0 or not members_data:
        return jsonify({'success': False, 'message': 'Total amount and participants are required.'}), 400

    # Generate unique 6-character room code
    existing_rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    existing_codes = {r.get('room_code') for r in existing_rooms}
    
    room_code = None
    for _ in range(20):
        candidate = f"ROOM-{secrets.randbelow(9000) + 1000}"
        if candidate not in existing_codes:
            room_code = candidate
            break
    if not room_code:
        room_code = f"ROOM-{int(datetime.now().timestamp()) % 100000}"

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Save room header
    csv_db.append_csv(csv_db.SPLIT_ROOMS_CSV,
        ['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'],
        {
            'room_code': room_code,
            'creator_user_id': uid,
            'creator_name': creator_name,
            'title': title,
            'total_amount': f"{total_amount:.2f}",
            'tip_pct': str(tip_pct),
            'tax_pct': str(tax_pct),
            'split_type': split_type,
            'status': 'active',
            'created_at': now_str
        }
    )

    # Initial base expense item logged
    csv_db.append_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV,
        ['id', 'room_code', 'title', 'amount', 'added_by_name', 'created_at'],
        {
            'id': str(csv_db.get_next_id(csv_db.SPLIT_ROOM_EXPENSES_CSV)),
            'room_code': room_code,
            'title': title or 'Base Bill',
            'amount': f"{total_amount:.2f}",
            'added_by_name': creator_name,
            'created_at': now_str
        }
    )

    # All registered users map for auto-linking by contact
    users = csv_db.read_csv(csv_db.USERS_CSV)
    user_by_email = {u.get('email', '').strip().lower(): u for u in users}
    user_by_phone = {normalize_phone(u.get('phone', '')): u for u in users if u.get('phone')}

    # Save members and sync with shared_expenses if linked
    for idx, m in enumerate(members_data):
        m_id = str(csv_db.get_next_id(csv_db.SPLIT_ROOM_MEMBERS_CSV))
        m_name = m.get('name', '').strip()
        m_contact = m.get('contact', '').strip()
        m_share = float(m.get('share_amount', 0))
        m_user_id = str(m.get('user_id', '')).strip()

        # Is this the creator / host row?
        is_creator_share = (
            m_user_id == uid or 
            m.get('is_host') is True or
            (idx == 0 and not m_contact) or
            m_name.lower() in ('you (host)', 'you', 'me', 'host', creator_name.lower())
        )

        if is_creator_share:
            m_user_id = uid
            m_name = creator_name  # Always use actual host name!
            initial_status = 'settled'
        else:
            initial_status = 'pending'

        # Auto-match user_id if not given
        if not m_user_id and m_contact:
            contact_clean = m_contact.lower()
            contact_digits = normalize_phone(m_contact)
            matched_u = user_by_email.get(contact_clean) or user_by_phone.get(contact_digits)
            if matched_u:
                m_user_id = matched_u['id']
                if not m_name or m_name.startswith('Friend'):
                    m_name = matched_u['name']

        csv_db.append_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
            ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'],
            {
                'id': m_id,
                'room_code': room_code,
                'user_id': m_user_id,
                'member_name': m_name or 'Friend',
                'member_contact': m_contact,
                'share_amount': f"{m_share:.2f}",
                'status': initial_status,
                'updated_at': now_str
            }
        )

        # If this friend is a registered user and not the creator, also record in shared_expenses!
        if m_user_id and m_user_id != uid:
            se_id = str(csv_db.get_next_id(csv_db.SHARED_EXPENSES_CSV))
            csv_db.append_csv(csv_db.SHARED_EXPENSES_CSV,
                ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'],
                {
                    'id': se_id,
                    'payer_user_id': uid,
                    'payee_user_id': m_user_id,
                    'amount': f"{m_share:.2f}",
                    'description': f"[{room_code}] {title}",
                    'split_type': split_type,
                    'status': 'pending',
                    'created_at': now_str
                }
            )

    return jsonify({
        'success': True,
        'room_code': room_code,
        'message': f"Split room '{title}' created successfully!",
        'share_url': f"/split-bill?room={room_code}"
    })


@app.route('/api/split-rooms/<string:room_code>', methods=['GET'])
def api_get_split_room(room_code):
    """Retrieve full details of a Split Room by its Room Code."""
    code = room_code.strip().upper()
    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    room = next((r for r in rooms if r.get('room_code', '').upper() == code), None)

    if not room:
        return jsonify({'success': False, 'message': f'Split room "{code}" not found.'}), 404

    all_members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    members = [m for m in all_members if m.get('room_code', '').upper() == code]

    current_uid = session.get('user_id')
    current_phone = normalize_phone(session.get('user_phone', ''))

    creator_uid = room.get('creator_user_id')
    creator_name = room.get('creator_name', 'Host')

    # Identify host and current user
    for m in members:
        is_host = (
            m.get('user_id') == creator_uid or
            (m.get('member_name', '').strip().lower() in ('you (host)', 'you', 'me', 'host', creator_name.lower()) and not m.get('member_contact'))
        )
        if is_host:
            m['is_host'] = True
            m['member_name'] = creator_name  # Show Host's actual name to everyone!
            m['user_id'] = creator_uid
        else:
            m['is_host'] = False

        m_phone = normalize_phone(m.get('member_contact', ''))
        if current_uid and m.get('user_id') == current_uid:
            m['is_current_user'] = True
        elif is_host and current_uid and creator_uid == current_uid:
            m['is_current_user'] = True
        elif current_phone and m_phone and m_phone == current_phone:
            m['is_current_user'] = True
        else:
            m['is_current_user'] = False

    # Retrieve all itemized expenses logged in this room
    all_expenses = csv_db.read_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV)
    room_expenses = [e for e in all_expenses if e.get('room_code', '').upper() == code]

    return jsonify({
        'success': True,
        'room': room,
        'members': members,
        'expenses': room_expenses,
        'current_user_id': current_uid,
        'is_creator': bool(current_uid and creator_uid == current_uid)
    })


@app.route('/api/split-rooms/<string:room_code>/add-expense', methods=['POST'])
@login_required
def api_add_split_room_expense(room_code):
    """Add an extra amount / itemized expense to an existing live Split Room and recalculate shares."""
    code = room_code.strip().upper()
    data = request.get_json() or {}
    exp_title = data.get('title', '').strip() or 'Extra Expense'
    amount = float(data.get('amount', 0))

    if amount <= 0:
        return jsonify({'success': False, 'message': 'Please enter a valid expense amount greater than 0.'}), 400

    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    room = next((r for r in rooms if r.get('room_code', '').upper() == code), None)
    if not room:
        return jsonify({'success': False, 'message': 'Room not found.'}), 404

    members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    room_members = [m for m in members if m.get('room_code', '').upper() == code]
    if not room_members:
        return jsonify({'success': False, 'message': 'No members found in this room.'}), 400

    # 1. Update Room Total Amount
    current_total = float(room.get('total_amount', 0))
    new_total = current_total + amount
    room['total_amount'] = f"{new_total:.2f}"
    csv_db.write_csv(csv_db.SPLIT_ROOMS_CSV,
        ['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'],
        rooms
    )

    # 2. Recalculate member shares equally
    new_share_each = new_total / len(room_members)
    for m in room_members:
        m['share_amount'] = f"{new_share_each:.2f}"
        m['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    csv_db.write_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
        ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'],
        members
    )

    # 3. Log itemized expense in SPLIT_ROOM_EXPENSES_CSV
    added_by = session.get('user_name', 'Member')
    csv_db.append_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV,
        ['id', 'room_code', 'title', 'amount', 'added_by_name', 'created_at'],
        {
            'id': str(csv_db.get_next_id(csv_db.SPLIT_ROOM_EXPENSES_CSV)),
            'room_code': code,
            'title': exp_title,
            'amount': f"{amount:.2f}",
            'added_by_name': added_by,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    )

    # 4. Sync corresponding shared_expenses entries if any
    shared = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    for s in shared:
        if f"[{code}]" in s.get('description', ''):
            s['amount'] = f"{new_share_each:.2f}"
    csv_db.write_csv(csv_db.SHARED_EXPENSES_CSV,
        ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'],
        shared
    )

    return jsonify({
        'success': True,
        'message': f"Added ₹{amount:.2f} ({exp_title}) to room. New total: ₹{new_total:.2f} (₹{new_share_each:.2f} each)!",
        'new_total': f"{new_total:.2f}",
        'new_per_person': f"{new_share_each:.2f}"
    })


@app.route('/api/split-rooms/<string:room_code>/update', methods=['PUT', 'POST'])
@login_required
def api_update_split_room_details(room_code):
    """Directly update total bill amount or title for a live Split Room."""
    code = room_code.strip().upper()
    data = request.get_json() or {}
    new_total = float(data.get('total_amount', 0))
    new_title = data.get('title', '').strip()

    if new_total <= 0:
        return jsonify({'success': False, 'message': 'Please enter a valid bill amount greater than 0.'}), 400

    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    room = next((r for r in rooms if r.get('room_code', '').upper() == code), None)
    if not room:
        return jsonify({'success': False, 'message': 'Room not found.'}), 404

    members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    room_members = [m for m in members if m.get('room_code', '').upper() == code]
    if not room_members:
        return jsonify({'success': False, 'message': 'No members in room.'}), 400

    room['total_amount'] = f"{new_total:.2f}"
    if new_title:
        room['title'] = new_title

    csv_db.write_csv(csv_db.SPLIT_ROOMS_CSV,
        ['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'],
        rooms
    )

    # Recalculate member shares
    new_share_each = new_total / len(room_members)
    for m in room_members:
        m['share_amount'] = f"{new_share_each:.2f}"
        m['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    csv_db.write_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
        ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'],
        members
    )

    # Sync shared expenses
    shared = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    for s in shared:
        if f"[{code}]" in s.get('description', ''):
            s['amount'] = f"{new_share_each:.2f}"
            if new_title:
                s['description'] = f"[{code}] {new_title}"
    csv_db.write_csv(csv_db.SHARED_EXPENSES_CSV,
        ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'],
        shared
    )

    return jsonify({
        'success': True,
        'message': f"Updated bill total to ₹{new_total:.2f} (₹{new_share_each:.2f} each)!",
        'new_total': f"{new_total:.2f}",
        'new_per_person': f"{new_share_each:.2f}"
    })


@app.route('/api/split-rooms/<string:room_code>', methods=['DELETE'])
@login_required
def api_delete_split_room(room_code):
    """Delete / Clear a Split Room and its associated data."""
    code = room_code.strip().upper()
    uid = session['user_id']

    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    target_room = next((r for r in rooms if r.get('room_code', '').upper() == code), None)
    if not target_room:
        return jsonify({'success': False, 'message': 'Room not found.'}), 404

    # Allow creator or member to delete/clear
    if target_room.get('creator_user_id') != uid:
        return jsonify({'success': False, 'message': 'Only the host can delete or clear this split room.'}), 403

    # Remove room
    updated_rooms = [r for r in rooms if r.get('room_code', '').upper() != code]
    csv_db.write_csv(csv_db.SPLIT_ROOMS_CSV,
        ['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'],
        updated_rooms
    )

    # Remove room members
    members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    updated_members = [m for m in members if m.get('room_code', '').upper() != code]
    csv_db.write_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
        ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'],
        updated_members
    )

    # Remove room expenses
    expenses = csv_db.read_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV)
    updated_expenses = [e for e in expenses if e.get('room_code', '').upper() != code]
    csv_db.write_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV,
        ['id', 'room_code', 'title', 'amount', 'added_by_name', 'created_at'],
        updated_expenses
    )

    # Clean up linked pending shared expenses
    shared = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    updated_shared = [s for s in shared if f"[{code}]" not in s.get('description', '')]
    csv_db.write_csv(csv_db.SHARED_EXPENSES_CSV,
        ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'],
        updated_shared
    )

    return jsonify({'success': True, 'message': f'Split room "{code}" has been cleared and deleted.'})


@app.route('/api/split-rooms/clear-all', methods=['POST'])
@login_required
def api_clear_all_split_rooms():
    """Clear all split rooms created by the current user."""
    uid = session['user_id']
    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    user_rooms = [r for r in rooms if r.get('creator_user_id') == uid]
    user_codes = {r.get('room_code', '').upper() for r in user_rooms}

    if not user_codes:
        return jsonify({'success': True, 'message': 'No rooms to clear.'})

    remaining_rooms = [r for r in rooms if r.get('room_code', '').upper() not in user_codes]
    csv_db.write_csv(csv_db.SPLIT_ROOMS_CSV,
        ['room_code', 'creator_user_id', 'creator_name', 'title', 'total_amount', 'tip_pct', 'tax_pct', 'split_type', 'status', 'created_at'],
        remaining_rooms
    )

    members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    remaining_members = [m for m in members if m.get('room_code', '').upper() not in user_codes]
    csv_db.write_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
        ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'],
        remaining_members
    )

    expenses = csv_db.read_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV)
    remaining_expenses = [e for e in expenses if e.get('room_code', '').upper() not in user_codes]
    csv_db.write_csv(csv_db.SPLIT_ROOM_EXPENSES_CSV,
        ['id', 'room_code', 'title', 'amount', 'added_by_name', 'created_at'],
        remaining_expenses
    )

    return jsonify({'success': True, 'message': f'Cleared {len(user_codes)} split rooms successfully!'})


@app.route('/api/split-rooms/<string:room_code>/settle', methods=['POST'])
@login_required
def api_settle_split_room_member(room_code):
    """Mark a participant's share in a room as settled / paid."""
    code = room_code.strip().upper()
    uid = session['user_id']
    data = request.get_json() or {}
    member_id = str(data.get('member_id', '')).strip()

    rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    room = next((r for r in rooms if r.get('room_code', '').upper() == code), None)
    if not room:
        return jsonify({'success': False, 'message': 'Room not found.'}), 404

    is_creator = (room.get('creator_user_id') == uid)

    members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)
    target_member = None
    for m in members:
        if m.get('room_code', '').upper() == code and (m.get('id') == member_id or (not member_id and m.get('user_id') == uid)):
            # Only creator or the member themselves can settle
            if is_creator or m.get('user_id') == uid:
                m['status'] = 'settled'
                m['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                target_member = m
                break

    if not target_member:
        return jsonify({'success': False, 'message': 'Member not found or unauthorized to settle.'}), 400

    csv_db.write_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV,
        ['id', 'room_code', 'user_id', 'member_name', 'member_contact', 'share_amount', 'status', 'updated_at'], members)

    # Sync corresponding shared_expenses entry if exists
    shared = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    for s in shared:
        desc = s.get('description', '')
        if f"[{code}]" in desc and (s.get('payee_user_id') == target_member.get('user_id')):
            s['status'] = 'settled'
    csv_db.write_csv(csv_db.SHARED_EXPENSES_CSV,
        ['id', 'payer_user_id', 'payee_user_id', 'amount', 'description', 'split_type', 'status', 'created_at'], shared)

    return jsonify({'success': True, 'message': f"Marked {target_member['member_name']}'s share as settled!"})


@app.route('/api/split-rooms/my-rooms', methods=['GET'])
@login_required
def api_get_my_split_rooms():
    """List all Split Rooms created by the current user or where they are a member."""
    uid = session['user_id']
    u_phone = normalize_phone(session.get('user_phone', ''))

    all_rooms = csv_db.read_csv(csv_db.SPLIT_ROOMS_CSV)
    all_members = csv_db.read_csv(csv_db.SPLIT_ROOM_MEMBERS_CSV)

    my_room_codes = set()
    # Rooms I created
    for r in all_rooms:
        if r.get('creator_user_id') == uid:
            my_room_codes.add(r.get('room_code', '').upper())

    # Rooms I am added to
    for m in all_members:
        m_phone = normalize_phone(m.get('member_contact', ''))
        if m.get('user_id') == uid or (u_phone and m_phone == u_phone):
            my_room_codes.add(m.get('room_code', '').upper())

    filtered_rooms = [r for r in all_rooms if r.get('room_code', '').upper() in my_room_codes]
    filtered_rooms.reverse() # latest first

    return jsonify({'success': True, 'rooms': filtered_rooms[:15]})


@app.route('/api/split-notifications', methods=['GET'])
@login_required
def api_get_split_notifications():
    """Return pending split bills and payment requests waiting for the current user."""
    uid = session['user_id']
    u_phone = normalize_phone(session.get('user_phone', ''))

    users = csv_db.read_csv(csv_db.USERS_CSV)
    user_map = {u['id']: u for u in users}

    all_se = csv_db.read_csv(csv_db.SHARED_EXPENSES_CSV)
    notifications = []

    for s in all_se:
        if s.get('payee_user_id') == uid and s.get('status') == 'pending':
            payer = user_map.get(s.get('payer_user_id'))
            desc = s.get('description', '')
            room_code = None
            if '[' in desc and ']' in desc:
                start = desc.find('[') + 1
                end = desc.find(']')
                candidate = desc[start:end].strip()
                if candidate.startswith('ROOM-'):
                    room_code = candidate

            notifications.append({
                'id': s['id'],
                'payer_name': payer['name'] if payer else 'A friend',
                'amount': s.get('amount', '0.00'),
                'description': desc,
                'room_code': room_code,
                'created_at': s.get('created_at', '')
            })

    return jsonify({'success': True, 'count': len(notifications), 'notifications': notifications})


if __name__ == '__main__':
    print("Starting Smart Expense Tracker Application on http://localhost:5050 and http://127.0.0.1:5050 ...")
    app.run(debug=True, host='0.0.0.0', port=5050)


