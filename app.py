# app.py
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_jwt_extended import (
    JWTManager, create_access_token, jwt_required,
    get_jwt_identity, get_jwt, set_access_cookies, unset_jwt_cookies
)
import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from config import DB_CONFIG, SECRET_KEY, JWT_SECRET_KEY
from datetime import timedelta

app = Flask(__name__)
app.secret_key = SECRET_KEY

# JWT config
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["JWT_TOKEN_LOCATION"] = ["cookies", "headers"]
app.config["JWT_ACCESS_COOKIE_PATH"] = "/"
app.config["JWT_COOKIE_SECURE"] = False  # True on HTTPS
app.config["JWT_COOKIE_CSRF_PROTECT"] = False  # Set True in production
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=6)

jwt = JWTManager(app)


def get_db():
    conn = pymysql.connect(
        host=DB_CONFIG["host"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        database=DB_CONFIG["database"],
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )
    return conn


# ---------- Helpers ----------
def safe_int(v):
    """Convert value to int or return None safely."""
    try:
        if v is None:
            return None
        if isinstance(v, int):
            return v
        s = str(v).strip()
        if s == "" or s.lower() == "null":
            return None
        # handle floats like "12.0"
        return int(float(s))
    except Exception:
        return None


# ---------- Web UI Routes ----------
@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        if not (username and email and password):
            flash("All fields required", "danger")
            return redirect(url_for("register"))

        pw_hash = generate_password_hash(password)
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username,email,password_hash) VALUES (%s,%s,%s)",
                (username, email, pw_hash)
            )
            conn.commit()
            flash("Registered! Please login.", "success")
            return redirect(url_for("login"))
        except pymysql.err.IntegrityError:
            conn.rollback()
            flash("Email already exists", "danger")
            return redirect(url_for("register"))
        finally:
            cur.close()
            conn.close()

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        if not (email and password):
            flash("Email and password required", "danger")
            return redirect(url_for("login"))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, username, password_hash, role FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("login"))

        # IMPORTANT: identity must be a string (JWT 'sub' claim)
        access_token = create_access_token(
            identity=str(user["id"]),
            additional_claims={"role": user["role"], "username": user["username"]}
        )
        resp = redirect(url_for("students_ui"))
        set_access_cookies(resp, access_token)
        flash("Logged in", "success")
        return resp

    return render_template("login.html")


@app.route("/logout")
def logout():
    resp = redirect(url_for("login"))
    unset_jwt_cookies(resp)
    flash("Logged out", "info")
    return resp


# ---------- UI pages ----------
@app.route("/dashboard")
@jwt_required()
def dashboard():
    claims = get_jwt()
    return render_template("dashboard.html", username=claims.get("username"), role=claims.get("role"))


@app.route("/students-ui")
@jwt_required()
def students_ui():
    claims = get_jwt()
    return render_template("students.html", role=claims.get("role"), username=claims.get("username"))



@app.route("/add-student-ui")
@jwt_required()
def add_student_ui():
    return render_template("add_student.html")


@app.route("/edit-student-ui/<int:sid>")
@jwt_required()
def edit_student_ui(sid):
    return render_template("edit_student.html", sid=sid)



# ---------- API endpoints ----------
@app.route("/api/profile", methods=["GET"])
@jwt_required()
def api_profile():
    # convert identity back to int when using for DB or comparisons
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    return jsonify({"id": user_id, "username": claims.get("username"), "role": claims.get("role")}), 200


@app.route("/api/students", methods=["GET"])
@jwt_required()
def api_get_students():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    conn = get_db()
    cur = conn.cursor()
    try:
        if role == "admin":
            cur.execute("SELECT * FROM students ORDER BY id DESC")
            rows = cur.fetchall()
        elif role == "user":
            cur.execute("SELECT * FROM students ORDER BY id DESC")
            rows = cur.fetchall()
        else:
            cur.execute("SELECT * FROM students WHERE created_by=%s ORDER BY id DESC", (user_id,))
            rows = cur.fetchall()
        return jsonify(rows), 200
    finally:
        cur.close()
        conn.close()


@app.route("/api/students/<int:sid>", methods=["GET"])
@jwt_required()
def api_get_student(sid):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM students WHERE id=%s", (sid,))
        row = cur.fetchone()
        if not row:
            return jsonify({"msg": "not found"}), 404
        if role != "admin" and row.get("created_by") != user_id:
            return jsonify({"msg": "forbidden"}), 403
        return jsonify(row), 200
    finally:
        cur.close()
        conn.close()


@app.route("/api/students", methods=["POST"])
@jwt_required()
def api_create_student():
    # jwt identity stored as string => convert to int
    user_id = int(get_jwt_identity())

    # accept both JSON and form submissions
    data = request.get_json(silent=True)
    if not data:
        data = request.form or {}

    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()
    email = (data.get("email") or "").strip().lower()
    rollno = (data.get("rollno") or "").strip()
    phone = (data.get("phone") or "").strip()
    unit_test1 = safe_int(data.get("unit_test1_marks"))
    unit_test2 = safe_int(data.get("unit_test2_marks"))

    if not (name and email and rollno and subject):
        return jsonify({"msg": "name, email, rollno, subject required"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO students
            (name,subject,email,rollno,phone,unit_test1_marks,unit_test2_marks,created_by)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (name, subject, email, rollno, phone, unit_test1, unit_test2, user_id)
        )
        conn.commit()
        return jsonify({"msg": "created"}), 201
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        return jsonify({"msg": "duplicate or DB error", "error": str(e)}), 400
    finally:
        cur.close()
        conn.close()


@app.route("/api/students/<int:sid>", methods=["PUT"])
@jwt_required()
def api_update_student(sid):
    claims = get_jwt()
    role = claims.get("role")
    if role != "admin":
        return jsonify({"msg": "forbidden, admin only"}), 403

    data = request.get_json(silent=True)
    if not data:
        data = request.form or {}

    name = (data.get("name") or "").strip()
    subject = (data.get("subject") or "").strip()
    email = (data.get("email") or "").strip().lower()
    rollno = (data.get("rollno") or "").strip()
    phone = (data.get("phone") or "").strip()
    unit_test1 = safe_int(data.get("unit_test1_marks"))
    unit_test2 = safe_int(data.get("unit_test2_marks"))

    if not (name and email and rollno and subject):
        return jsonify({"msg": "name, email, rollno, subject required"}), 400

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM students WHERE id=%s", (sid,))
        if not cur.fetchone():
            return jsonify({"msg": "not found"}), 404

        cur.execute(
            """UPDATE students SET name=%s, subject=%s, email=%s, rollno=%s, phone=%s,
            unit_test1_marks=%s, unit_test2_marks=%s WHERE id=%s""",
            (name, subject, email, rollno, phone, unit_test1, unit_test2, sid)
        )
        conn.commit()
        return jsonify({"msg": "updated"}), 200
    except pymysql.err.IntegrityError as e:
        conn.rollback()
        return jsonify({"msg": "duplicate or DB error", "error": str(e)}), 400
    finally:
        cur.close()
        conn.close()


@app.route("/api/students/<int:sid>", methods=["DELETE"])
@jwt_required()
def api_delete_student(sid):
    claims = get_jwt()
    role = claims.get("role")
    if role != "admin":
        return jsonify({"msg": "forbidden, admin only"}), 403

    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM students WHERE id=%s", (sid,))
        conn.commit()
        return jsonify({"msg": "deleted"}), 200
    finally:
        cur.close()
        conn.close()


# ---------- JSON helper endpoints (for programmatic clients) ----------
@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username")
    email = data.get("email")
    role = data.get("role")
    password = data.get("password")
    if not (username and email and role and password):
        return jsonify({"msg": "username,email,role,password required"}), 400

    pw_hash = generate_password_hash(password)
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (username,email,password_hash,role) VALUES (%s,%s,%s,%s)", (username, email, pw_hash, role))
        conn.commit()
        return jsonify({"msg": "registered"}), 201
    except pymysql.err.IntegrityError:
        conn.rollback()
        return jsonify({"msg": "email exists"}), 400
    finally:
        cur.close()
        conn.close()


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not (email and password):
        return jsonify({"msg": "email,password required"}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, email, password_hash, role FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"msg": "bad credentials"}), 401

    access_token = create_access_token(identity=str(user["id"]), additional_claims={"role": user["role"], "username": user["username"]})
    resp = jsonify({"msg": "logged", "access_token": access_token})
    set_access_cookies(resp, access_token)
    return resp, 200

@app.route("/api/stats", methods=["GET"])
@jwt_required()
def api_stats():
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")

    conn = get_db()
    cur = conn.cursor()
    try:
        # total students
        if role == "admin":
            cur.execute("SELECT COUNT(*) AS c FROM students")
        elif role == "user":
            cur.execute("SELECT COUNT(*) AS c FROM students")
        else:
            cur.execute("SELECT COUNT(*) AS c FROM students WHERE created_by=%s", (user_id,))
        total_students = cur.fetchone()["c"]

        # total admins
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='admin'")
        total_admins = cur.fetchone()["c"]

        # total normal users
        cur.execute("SELECT COUNT(*) AS c FROM users WHERE role='user'")
        total_users = cur.fetchone()["c"]

        return jsonify({
            "total_students": total_students,
            "total_admins": total_admins,
            "total_users": total_users
        }), 200
    finally:
        cur.close()
        conn.close()


# ---------- Run ----------
if __name__ == "__main__":
    app.run(debug=True)
