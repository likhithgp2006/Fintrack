# Fintrack – Smart Expense Tracker 💰

A full-stack, responsive web application for personal expense tracking, budgeting, and financial analytics built with **HTML5, CSS3, Vanilla JavaScript, Python Flask**, and persistent **CSV file storage**.

[![GitHub Repo](https://img.shields.io/badge/GitHub-likhithgp2006%2FFintrack-blue?logo=github)](https://github.com/likhithgp2006/Fintrack)

---

## 🌐 Live Deployment
- **Live Demo Link:** `[Paste your deployment link here]` *(Send your link and it will be updated here!)*
- **GitHub Repository:** [https://github.com/likhithgp2006/Fintrack](https://github.com/likhithgp2006/Fintrack)

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

## 🔐 Security & Privacy Architecture

- **Client-Side Transmission Encryption**: Passwords are encrypted in the browser via SHA-256 before HTTP dispatch, preventing plain-text exposure in Browser DevTools / Network Inspect.
- **Server-Side Password Hashing**: Server salts and hashes the client payload with Werkzeug's `scrypt` / `pbkdf2:sha256` before saving to storage. Plain-text passwords are never logged, stored, or transmitted.
- **Session Authentication**: Server-side Flask session cookies prevent unauthorized access across user datasets.
- **Data Protection**: User database files and private environment variables (`.env`) are strictly excluded via `.gitignore`.

---

## 🚀 Deployment Guide

This app can be deployed on **Render**, **Railway**, **PythonAnywhere**, or any Python hosting provider.

### Live Deployment URL
> 🔗 **Production Link:** `[Add your deployment link here]`
> *(Once deployed, update this line with your live website address)*

### Step 1: Connect to Render (Recommended — Free)
1. Go to [render.com](https://render.com) → **New Web Service**
2. Connect your GitHub repo (`likhithgp2006/Fintrack`)
3. Set the following build settings:
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
4. Add environment variables (see below)
5. Click **Deploy Web Service**

---

## ⚙️ Post-Deployment: Configure SMS OTP (For Forgot Password)

> **Important:** After deploying, configure an SMS gateway for the Forgot Password feature to deliver real SMS OTPs to user mobile phones.
>
> Without configuration, the app runs in **Demo Mode** (the OTP is shown on screen for testing).

### Option A: Fast2SMS (Recommended for India 🇮🇳 — Free tier available)

1. Sign up at **[fast2sms.com](https://www.fast2sms.com)**
2. Go to **Dev API** section → Copy your API Key
3. Add this environment variable in your deployment dashboard:

```env
FAST2SMS_API_KEY=your_fast2sms_api_key_here
```

### Option B: Twilio (International 🌍)

1. Sign up at **[twilio.com](https://www.twilio.com)**
2. Copy your **Account SID**, **Auth Token**, and **Twilio Phone Number**
3. Add these environment variables:

```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=+1xxxxxxxxxx
```

---

### Environment Variables Summary

Add these in your hosting platform's **Environment Variables** panel:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | ✅ Yes | Random string for securing Flask user sessions |
| `FAST2SMS_API_KEY` | ⚡ For SMS OTP | API key from Fast2SMS (India 10-digit mobile) |
| `TWILIO_ACCOUNT_SID` | ⚡ For SMS OTP | Twilio Account SID (International) |
| `TWILIO_AUTH_TOKEN` | ⚡ For SMS OTP | Twilio Auth Token |
| `TWILIO_PHONE_NUMBER` | ⚡ For SMS OTP | Twilio sender phone number |

---

### How SMS OTP Works

```
User clicks "Forgot Password"
        ↓
Enters registered 10-digit mobile number
        ↓
Server generates secure 6-digit OTP (valid 15 minutes)
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

## 📄 License
Open source and available under the [MIT License](LICENSE).

