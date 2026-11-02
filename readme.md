# Employee Attendance Management System

A high-performance, asynchronous **FastAPI** application built with **SQLModel**, **SQLAlchemy**, and **MySQL**, designed to manage employees, track daily attendance, manage check-ins/check-outs, and generate attendance reports.

## 🚀 Tech Stack

* **Framework:** FastAPI
* **Database & ORM:** MySQL (Local) with SQLModel & SQLAlchemy (Async)
* **Async Driver:** `aiomysql`
* **Validation:** Pydantic v2

---

## 🛠️ Getting Started & Installation Instructions

### 1. Prerequisites

Ensure you have **Python 3.10+** and **MySQL** installed on your system. If you are on macOS, you can install MySQL via Homebrew:

```bash
brew install mysql

```

### 2. Start MySQL and Create Database

Start your local MySQL service:

```bash
brew services start mysql

```

Log in to MySQL (default root user with an empty password):

```bash
mysql -u root

```

Inside the MySQL prompt, create your database:

```sql
CREATE DATABASE employee_management;
EXIT;

```

### 3. Project Setup

Clone or navigate to your project directory, then run the following commands in your terminal to set up the virtual environment and install dependencies:

```bash
# Navigate to project directory
cd /path/to/your/project

# Create a virtual environment
python3 -m venv .venv

# Activate the virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install required dependencies
pip install -r requirements.txt

```

---

## ⚙️ Configuration

Make sure your database connection string in your database configuration file (e.g., `database/db.py`) points to your local database:

```python
MYSQL_CONNECTION_STRING = "mysql+aiomysql://root:@localhost:3306/employee_management"

```

---

## 🚀 Running the Server

Start the FastAPI application using Uvicorn with live reload enabled:

```bash
uvicorn main:app --reload

```

*(Or alternatively using Python module syntax: `python -m uvicorn main:app --reload`)*

The server will run locally at **`[http://127.0.0.1:8000](http://127.0.0.1:8000)`**.

---

## 📖 API Documentation & Testing

Once the server is running, you can explore and test all available endpoints interactively via the built-in Swagger UI or ReDoc:

* **Swagger UI:** [http://127.0.0.1:8000/docs](https://www.google.com/search?q=http://127.0.0.1:8000/docs)
* **ReDoc:** [http://127.0.0.1:8000/redoc](https://www.google.com/search?q=http://127.0.0.1:8000/redoc)