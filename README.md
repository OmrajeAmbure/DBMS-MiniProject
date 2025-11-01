Student Management System (Flask + MySQL) - Admin Dashboard Theme

Setup:
1. Create virtualenv and activate:
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # mac/linux
   source venv/bin/activate

2. Install requirements:
   pip install -r requirements.txt

3. Create database:
   mysql -u root -p < db_init.sql

4. (Optional) Register via UI and promote a user to admin:
   UPDATE users SET role='admin' WHERE email='your_email';

5. Run:
   python app.py

Admin Dashboard features:
- Collapsible sidebar with navigation
- Topbar with user info
- Responsive layout (Bootstrap)
- CRUD pages for students

📌 Student Management System (Flask + MySQL + JWT Authentication)

This project is a Student CRUD Web Application built using Flask and MySQL, with role-based authentication (Admin & User).

Admin can add, edit, delete, view all students.

Normal User can add and view only the students created by them.

Login is handled using JWT (cookie-based authentication).

🚀 Features
Feature	            Admin	            User
Register & Login	   ✅	              ✅
Dashboard	         ✅	              ✅
Add Student	         ✅	              ✅
View Student List	   ✅	              ✅
Edit Student	      ✅	              ❌
Delete Student	      ✅	              ❌

🛠️ Tech Stack
Component	Technology Used
Backend	Flask (Python)
Templates	HTML, CSS, Bootstrap
Database	MySQL
Authentication	Flask-JWT-Extended
Password Security	werkzeug.hashing
ORM	Raw SQL (pymysql)

📂 Project Structure
project/
│── app.py
│── config.py           # ⚠️ never push to GitHub
│── requirements.txt
│── .gitignore
│── templates/
│   ├── base.html
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── students.html
│   ├── add_student.html
│   └── edit_student.html
│── static/
    └── css /

🧑‍💻 Setup Instructions
1. Clone the Repository
git clone https://github.com/yourusername/student-management.git
cd student-management

2. Create Virtual Environment
python -m venv venv

3. Activate Environment
OS	Command
Windows	venv\Scripts\activate
Mac/Linux	source venv/bin/activate

4. Install Dependencies
pip install -r requirements.txt

5. Setup Database

Create MySQL Database and tables:

CREATE DATABASE student_ms;

USE student_ms;

CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50),
    email VARCHAR(100) UNIQUE,
    password_hash TEXT,
    role ENUM('admin','user') DEFAULT 'user'
);

CREATE TABLE students (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    subject VARCHAR(100),
    email VARCHAR(100),
    rollno VARCHAR(50),
    phone VARCHAR(15),
    unit_test1_marks INT,
    unit_test2_marks INT,
    created_by INT
);

6. Create and Configure config.py

Create a file named config.py:

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "student_ms"
}
SECRET_KEY = "CHANGE_ME"
JWT_SECRET_KEY = "CHANGE_ME_TOO"

▶️ Run the Project
python app.py


Then open your browser:

http://127.0.0.1:5000/

🧪 Default Login (Optional Seed)
Role	   Email	              Password
Admin	 admin@example.com       12345
User	 user@example.com        12345