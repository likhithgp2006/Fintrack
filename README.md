# Fintrack – Smart Expense Tracker 💰

A full-stack, responsive web application for personal expense tracking, budgeting, and financial analytics built with **HTML5, CSS3, Vanilla JavaScript, Python Flask**, and persistent **CSV file storage**.

---

## 🌟 Key Features

1. **User Authentication & Session Security**:
   - Secure Registration & Login using Werkzeug password hashing.
   - Mobile number (10-digit) required at registration for SMS OTP support.
   - Flask session-based authentication protecting all dashboard routes and APIs.
   - **Forgot Password via SMS OTP** — 6-digit code sent to registered mobile number.

2. **Dashboard & Visual Analytics**:
   - Stat Cards: **Total Income, Total Expenses, Net Balance, Total Transactions, Highest Expense, Current Month Spending**.
   - **Chart.js Visualizations**:
     - Category Distribution (Doughnut Chart)
     - Monthly Income vs Expense Comparison (Bar Chart)
   - Recent 5–10 transactions list.

3. **Transaction CRUD Management**:
   - **Create**: Add daily expenses/income with Date, Description, Amount (INR ₹), Category, Payment Method (UPI, Cash, Debit Card, Credit Card, Bank Transfer, Net Banking), Type, and Notes.
   - **Read**: View paginated table of transactions with search bar and filter drawer.
   - **Update**: Modal popup for editing transaction details.
   - **Delete**: Confirmation dialog before deletion.

4. **Search, Filter & Sort Capabilities**:
   - Instant search across description, category, payment method, and notes.
   - Advanced filters: Category, Transaction Type, Payment Method, Date Range, Min/Max Amount.
   - Column header sorting (Date, Description, Category, Amount).

5. **Category Budgeting & Warning Alerts**:
   - Set monthly spending caps for individual categories.
   - Visual progress bars with color-coded status badges (**On Track**, **Near Limit (80%+)**, **Exceeded (100%+)**).
   - Dynamic Toast Notifications for budget warnings upon user login.

6. **Reports & Exporting**:
   - Monthly and Category-wise analytical reports.
   - One-click **CSV Data Export** (`GET /api/export/csv`).
   - Printable report generator (supports PDF print output).

7. **Modern UI & Theme System**:
   - Dark Mode & Light Mode toggle saved in `localStorage`.
   - Reusable Toast Notification system.
   - Fully responsive sidebar with mobile hamburger menu drawer.

8. **🎯 Savings Goals & Milestones Tracker**:
   - Set financial targets with target dates, categories, and custom notes.
   - Visual progress bar with milestone status badges (🌱 Started, 🥉 Bronze 25%, 🥈 Silver 50%, 🥇 Gold 75%, 🏆 Complete).
   - Quick deposit modal (+₹500, +₹1,000, +₹5,000, +₹10,000) with optional automatic ledger expense entry.

9. **🔄 Recurring Subscriptions & Renewal Reminders**:
   - Track monthly and annual recurring services (Netflix, Spotify, Gym, Wi-Fi, etc.).
   - Normalized monthly equivalent cost and 12-month commitment projection.
   - Renewal countdown badges (e.g., "Renews in 3 days", "Due today!").
   - One-click "⚡ Log Expense" button to record recurring payment into the tracker and advance renewal date.
   - Toggle subscriptions between Active and Paused.

10. **💡 Financial Health Score (0–100) & AI Spending Advisor**:
    - Automated financial wellness score computed from Savings Rate (35%), 50/30/20 Rule adherence (30%), Budget discipline (20%), and Net Balance stability (15%).
    - Interactive 50/30/20 stacked visual breakdown (Needs vs Wants vs Savings).
    - Dynamic personalized smart spending insights and actionable recommendations.

11. **🧾 Split Bill, Live Rooms & Shared Expenses**:
    - Calculate shared group expenses with customizable Tip % (0%, 5%, 10%, 15%, Custom) and Tax %.
    - Equal splits vs Itemized/Custom participant weights.
    - **Live Split Rooms** — Create a room and share a unique `ROOM-XXXX` code with friends. Anyone on the app can join with the code and see their share instantly.
    - **Friends / Contacts System** — Search registered users by name, mobile, or email. Send/accept friend requests. Split bills directly with friends.
    - **Shared Expense Notifications** — Bell alert when a friend splits a bill with you.
    - Round up to nearest ₹5 / ₹10 / whole number to eliminate awkward change.
    - One-click "📋 Copy WhatsApp Summary" ready to send to friends.
    - "💳 Record My Share as Expense" button to instantly log individual share into personal ledger.

12. **💱 Multi-Currency Switcher & Bulk CSV Import**:
    - Global currency switcher in top navigation bar and profile supporting ₹ INR, $ USD, € EUR, £ GBP, د.إ AED, C$ CAD, A$ AUD, and ¥ JPY.
    - Drag-and-drop CSV file importer with auto-header mapping and validation.
    - Ready-to-use CSV sample import template download.

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, CSS3 (Vanilla + CSS Variables), Vanilla JavaScript (ES6+) |
| **Data Visualization** | Chart.js (v4.4) |
| **Icons & Fonts** | Font Awesome 6, Google Fonts (Outfit, Plus Jakarta Sans) |
| **Backend Framework** | Python 3 (Flask, Werkzeug) |
| **Database** | File-based CSV persistence (`csv_db.py`) |
| **API Architecture** | RESTful JSON APIs |

---

## 📁 Project Folder Structure

```text
expenses-tracker/
├── app.py                  # Main Flask application routes & REST APIs
├── csv_db.py               # CSV Database operations & thread-safe helper
├── requirements.txt        # Python package dependencies
├── README.md               # Project documentation & viva guide
├── .gitignore              # Git ignore rules
│
├── data/                   # Persistent CSV Database Storage
│   ├── users.csv           # Registered user accounts & password hashes
│   ├── expenses.csv        # Transactions dataset
│   ├── categories.csv      # Expense and Income categories
│   └── budgets.csv         # Category spending budgets
│
├── templates/              # HTML Jinja2 Templates
│   ├── layout.html         # Master app shell & navigation layout
│   ├── index.html          # Public landing page
│   ├── login.html          # Login page with demo credentials
│   ├── register.html       # Account registration page
│   ├── dashboard.html      # Main user dashboard
│   ├── add-expense.html    # Add transaction form page
│   ├── transactions.html   # Transactions table view (CRUD, Search, Filter)
│   ├── reports.html        # Financial reports & analytics page
│   ├── budgets.html        # Category budget management page
│   └── profile.html        # User profile & export page
│
└── static/                 # Static Assets
    ├── css/
    │   ├── style.css       # Core design system & theme CSS variables
    │   ├── dashboard.css   # Dashboard layout & card styling
    │   ├── forms.css       # Form inputs, pills & modal overlay styling
    │   ├── tables.css      # Data table, badges & pagination styling
    │   ├── reports.css     # Reports layout & progress bars styling
    │   └── responsive.css  # Mobile hamburger & breakpoint media queries
    │
    └── js/
        ├── auth.js         # Theme toggle, mobile menu & toast notifications
        ├── charts.js       # Chart.js initialization & dynamic updates
        ├── dashboard.js    # Dashboard stats loading & recent table binding
        ├── expenses.js     # Add transaction form validation & submission
        ├── transactions.js # CRUD table, filter drawer, search & pagination
        ├── reports.js      # Reports analytics loading & print handler
        └── budgets.js      # Category budget cards & progress bar rendering
```

---

## 🚀 Installation & Setup Guide

### Step 1: Clone or Open Workspace
Navigate to the project root directory in VS Code or Terminal:
```bash
cd ee
```

### Step 2: Create Python Virtual Environment
```bash
# Windows
python -m venv venv

# Activate Virtual Environment
.\venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Run Flask Server
```bash
python app.py
```

### Step 5: Access Application in Browser
Open your browser and navigate to:
```text
http://127.0.0.1:5050
```

---

## 🔑 Quick Start

1. Register a new account at `/register` with your **name, email, 10-digit mobile number, and password**.
2. Log in and start tracking expenses immediately.
3. For Forgot Password — enter your registered mobile number and receive a 6-digit SMS OTP.

> **Note:** The CSV database files are auto-created on first run via `init_db()`. No manual setup needed.

---

## 🌐 REST API Documentation

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/register` | `POST` | Register a new user account |
| `POST /api/login` | `POST` | Authenticate user and initiate session |
| `POST /api/logout` | `POST` | Destroy session |
| `GET /api/me` | `GET` | Get logged-in user profile |
| `GET /api/dashboard` | `GET` | Get dashboard summary metrics, recent transactions & chart data |
| `GET /api/expenses` | `GET` | Fetch filtered, sorted, paginated transactions |
| `POST /api/expenses` | `POST` | Add a new income or expense transaction |
| `GET /api/expenses/<id>` | `GET` | Retrieve single transaction details |
| `PUT /api/expenses/<id>` | `PUT` | Update an existing transaction |
| `DELETE /api/expenses/<id>` | `DELETE` | Delete a transaction |
| `GET /api/categories` | `GET` | List expense and income categories |
| `POST /api/categories` | `POST` | Add custom category |
| `GET /api/budgets` | `GET` | Get category budgets, spent amounts & alert statuses |
| `POST /api/budgets` | `POST` | Set or update category spending budget |
| `DELETE /api/budgets/<id>` | `DELETE` | Delete budget limit |
| `GET /api/reports/monthly` | `GET` | Get monthly financial summary report |
| `GET /api/reports/category` | `GET` | Get category spending breakdown |
| `GET /api/export/csv` | `GET` | Download user's transactions as CSV file |

---

## 📊 CSV Database Schemas

### 1. `users.csv`
```csv
id,name,email,phone,password_hash,created_at
1,Likhith,likhith@example.com,9876543210,scrypt:...,2026-09-01 10:00:00
```

### 2. `expenses.csv`
```csv
id,user_id,date,description,category,amount,payment_method,type,notes,created_at
1,1,2026-09-01,Monthly Salary,Salary,50000,Bank Transfer,Income,Company payout,2026-09-01 09:00:00
```

### 3. `categories.csv`
```csv
id,name,type,icon,color
1,Food,Expense,fa-utensils,#ef4444
2,Transport,Expense,fa-bus,#f59e0b
```

### 4. `budgets.csv`
```csv
id,user_id,category,amount,month,year
1,1,Food,5000,09,2026
```

### 5. `friends.csv`
```csv
id,user_id,friend_user_id,status,created_at
```

### 6. `split_rooms.csv`
```csv
room_code,creator_user_id,creator_name,title,total_amount,tip_pct,tax_pct,split_type,status,created_at
```

### 7. `split_room_members.csv`
```csv
id,room_code,user_id,member_name,member_contact,share_amount,status,updated_at
```

---

## 🎓 BCA Project Demonstration Flow

Follow this step-by-step sequence when demonstrating the application for viva evaluation:

1. **Landing Page**: Open `http://127.0.0.1:5050/`, demonstrate hero section and feature cards.
2. **Login**: Click Login, use demo credentials (`likhith@example.com` / `password123`).
3. **Dashboard Overview**: Show Total Income (₹57,500), Total Expenses, Net Balance, Highest Expense, Category Doughnut Chart, and Monthly Bar Chart.
4. **Add Transaction**: Click "+ Add Transaction", add a new Food expense for ₹750 via UPI with notes. Submit and observe automatic redirect & metric updates.
5. **Transactions Page**: Show search bar, category filter, date filter, sorting by Amount, Edit Modal popup, and Delete confirmation.
6. **Budgets Page**: Demonstrate category progress bars, status badges, and 80%/100% budget alerts.
7. **Reports & Analytics**: Select Month/Year, view category breakdown percentages, click Print/Save PDF.
8. **Dark Mode Toggle**: Click theme moon icon in top navbar to showcase seamless dark/light mode transition.
9. **CSV Export**: Click "Export CSV" to download the transaction data file.

---

## 🎤 Viva Voce Questions & Answers

### Q1: Why did you choose Python Flask for this project?
**Answer:** Flask is a micro web framework for Python. It is lightweight, flexible, and allows us to easily build RESTful API endpoints using JSON for seamless communication with standard JavaScript frontends without unnecessary boilerplate code.

### Q2: How is data persisted without a relational SQL database?
**Answer:** We implemented a custom file-based database layer in `csv_db.py` using Python's built-in `csv` module. Data is structured in standard CSV files (`users.csv`, `expenses.csv`, `categories.csv`, `budgets.csv`). Thread locking (`threading.Lock()`) is utilized to guarantee data integrity during concurrent read/write operations.

### Q3: How are passwords secured in `users.csv`?
**Answer:** Passwords are never stored in plain text. We utilize Werkzeug's `generate_password_hash()` which uses PBKDF2 with SHA-256 algorithm and salt. During login, `check_password_hash()` compares the input with the stored hash securely.

### Q4: Explain the calculation for Net Balance.
**Answer:** `Net Balance = Total Income - Total Expenses`. The backend iterates through the user's transactions in `expenses.csv`, sums all records with `type == 'Income'`, sums records with `type == 'Expense'`, and calculates the net difference.

### Q5: How do budget warnings work?
**Answer:** When `/api/budgets` is queried, the server calculates the total expenses incurred for each category in the current month. It compares total category spending against the set budget limit. If spending exceeds 80%, a `warning` status is assigned; if spending exceeds 100%, a `danger` status is returned, triggering dynamic toast notifications on the frontend.

### Q6: How does the frontend communicate with the backend?
**Answer:** The frontend uses standard ES6 `fetch()` API calls to consume JSON REST endpoints (`GET`, `POST`, `PUT`, `DELETE`). The response JSON updates the DOM dynamically without requiring full browser page reloads.

### Q7: How is Dark Mode preference saved across sessions?
**Answer:** When the user clicks the theme toggle button, the selected theme (`dark` or `light`) is saved in the browser's `localStorage`. On page load, `auth.js` checks `localStorage.getItem('theme')` and sets the `data-theme` attribute on the `<html>` root element.

### Q8: What prevents User A from accessing User B's transactions?
**Answer:** Session-based authentication handles authorization. Each expense record stores a `user_id`. Every API endpoint extracts `user_id = session['user_id']` and filters records so users can only view, edit, or delete their own data.

### Q9: How is Chart.js integrated with dynamic Flask data?
**Answer:** Flask provides aggregated category totals and monthly spending through `/api/dashboard`. `dashboard.js` receives the JSON payload and passes labels and numerical arrays to Chart.js dataset objects, rendering responsive HTML5 canvas graphs.

### Q10: How can this project be scaled in the future?
**Answer:** Future enhancements include migrating `csv_db.py` to PostgreSQL/MySQL via SQLAlchemy, integrating Bank API auto-sync, OCR receipt scanning using OpenCV/Tesseract, and setting up automated monthly PDF email digests.

---

## 🔮 Future Enhancements
- Integration with SQL Database (PostgreSQL / SQLite).
- Receipt image upload & OCR scanning.
- Automated email alerts for budget overspending.
- Recurring transaction auto-scheduler.

---

## 🚀 Deployment Guide

This app can be deployed on **Render**, **Railway**, **PythonAnywhere**, or any platform that supports Python/Flask.

### Step 1: Push to GitHub
```bash
git add .
git commit -m "deploy"
git push origin main
```

### Step 2: Connect to Render (Recommended — Free)
1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo (`Fintrack`)
3. Set:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Add environment variables (see below)
5. Click **Deploy**

---

## ⚙️ Post-Deployment: Configure SMS OTP (Required for Forgot Password)

> **Important:** After deploying, you MUST configure an SMS provider for the Forgot Password feature to send real OTPs to users' mobile numbers.
>
> Without configuration, the app runs in **Demo Mode** — the OTP is displayed on screen instead of being sent via SMS (useful for local testing only).

### Option A: Fast2SMS (Recommended for India 🇮🇳 — Free tier available)

1. Sign up at **[fast2sms.com](https://www.fast2sms.com)**
2. Go to **Dev API** section → Copy your API Key
3. Add this environment variable in your deployment dashboard:

```env
FAST2SMS_API_KEY=your_fast2sms_api_key_here
```

✅ Works instantly with all Indian mobile numbers (10-digit).

---

### Option B: Twilio (International 🌍)

1. Sign up at **[twilio.com](https://www.twilio.com)** (free trial gives ~$15 credit)
2. Get your **Account SID**, **Auth Token**, and a **Twilio Phone Number**
3. Add these environment variables:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

---

### Environment Variables Summary

Add these in your hosting platform's **Environment Variables** panel (e.g. Render Dashboard → Environment):

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Random secret string for Flask sessions |
| `FAST2SMS_API_KEY` | ⚡ For SMS OTP | API key from fast2sms.com (India) |
| `TWILIO_ACCOUNT_SID` | ⚡ For SMS OTP | Twilio Account SID (International) |
| `TWILIO_AUTH_TOKEN` | ⚡ For SMS OTP | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | ⚡ For SMS OTP | Twilio sender phone number |

> See `.env.example` in the repo for the full template.

### How SMS OTP Works

```
User clicks "Forgot Password"
        ↓
Enters registered 10-digit mobile number
        ↓
Server generates 6-digit OTP (valid 15 minutes)
        ↓
  ┌─────────────────────────────────────┐
  │  SMS API configured?                │
  │  YES → OTP sent via SMS to mobile  │
  │  NO  → Demo Mode: OTP shown on     │
  │         screen (testing only)       │
  └─────────────────────────────────────┘
        ↓
User enters OTP → Sets new password
```

---

**Developed for BCA Final Year / Mini Project — Fintrack Smart Expense Tracker.**
