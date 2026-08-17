# 🍕 Flask Online Restaurant

A feature-rich, full-stack online restaurant web application built with **Python (Flask)**. This project includes an interactive food catalog, a shopping cart system, user authentication, a table reservation feature, a dedicated secure admin panel, and **instant Telegram bot notifications** for incoming orders.

---

## ✨ Key Features

* **Interactive Menu & Catalog:** Browse dishes with search functionality and category filtering.
* **Shopping Cart & Checkout:** Add/remove items, update quantities, calculate totals seamlessly, and place orders.
* **Telegram Bot Integration:** Automatically sends instant order notifications with customer details directly to the administrator's Telegram chat.
* **Secure Admin Panel:** Manage inventory, add new dishes, edit existing items, and delete products dynamically.
* **Table Reservation System:** Allows customers to book tables online.
* **User Accounts & Roles:** User registration, login, session management, and role-based access control.
* **Data Persistence:** Automatically syncs and stores menu data in JSON format (`menu.json`).

---

## 🛠 Tech Stack

* **Backend:** Python, Flask, Flask-Login / Session Management
* **Frontend:** HTML5, CSS3 (Modern responsive layout, glassmorphic UI design)
* **Data Storage:** JSON (`menu.json`)
* **Notifications:** Telegram Bot API (`requests`)
* **Environment Security:** `python-dotenv`

---

## 📂 Project Structure

```text
online-restaurant/
│
├── static/                 # CSS styles, JavaScript files, and images
├── templates/              # HTML layout templates (index, menu, cart, admin, etc.)
├── .env.example            # Template file for environment variables
├── .gitignore              # Files and folders ignored by Git (venv/, .env)
├── menu.json               # Local JSON database for restaurant items
├── online_restaurant.py    # Main Flask application script
└── requirements.txt        # Project dependencies list