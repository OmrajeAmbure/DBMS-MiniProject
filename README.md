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
