import os
import json
import openai
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
from models import db, User, ProofreadSession

# تحميل المتغيرات البيئية
load_dotenv()

# إنشاء التطبيق
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")  # استخدم متغير بيئي
openai.api_key = os.getenv("OPENAI_API_KEY")  # تعيين مفتاح OpenAI

# إعداد قاعدة البيانات
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///database.db")
if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgres://"):
    app.config["SQLALCHEMY_DATABASE_URI"] = app.config["SQLALCHEMY_DATABASE_URI"].replace("postgres://", "postgresql://", 1)

# تهيئة قاعدة البيانات
db.init_app(app)

# تهيئة Flask-Login
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# المتغير العالمي لمطالبة الذكاء الاصطناعي
AI_PROMPT = (
    "Please proofread the following Arabic text. Correct any spelling, grammar, and style errors. "
    "For each correction, specify the position (e.g., paragraph or line number if possible), "
    "the type of error (spelling, grammar, or style), and provide a detailed explanation in Arabic. "
    "Return the output in JSON format with two keys: 'result' for the corrected text (in HTML format), "
    "and 'corrections' for an array of correction objects. Each correction object should include 'error', "
    "'type', 'explanation', and optionally 'location'."
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("المستخدم موجود بالفعل!")
            return redirect(url_for("register"))
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash("تم التسجيل بنجاح! الرجاء تسجيل الدخول.")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        user = User.query.filter_by(email=email).first()
        if user and user.password == password:
            login_user(user)
            flash("تم تسجيل الدخول بنجاح!")
            return redirect(url_for("index"))
        else:
            flash("بيانات تسجيل الدخول غير صحيحة!")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("تم تسجيل الخروج.")
    return redirect(url_for("index"))

@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")
        flash("تم إرسال رسالتك. شكرًا لتواصلك معنا!")
        return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/check", methods=["POST"])
def check_text():
    text = request.json.get("text", "")
    prompt = f"{AI_PROMPT}\n\nText:\n{text}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            temperature=0.2,
            messages=[
                {"role": "system", "content": "You are an expert Arabic proofreader. Provide corrections and detailed explanations in Arabic."},
                {"role": "user", "content": prompt}
            ]
        )
        raw_output = response.choices[0].message.content.strip()
        parsed_output = json.loads(raw_output)
        return jsonify({"result": parsed_output.get("result", ""), "corrections": parsed_output.get("corrections", [])})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history")
@login_required
def history():
    sessions_entries = ProofreadSession.query.filter_by(user_id=current_user.id).order_by(ProofreadSession.timestamp.desc()).all()
    return render_template("history.html", sessions=sessions_entries)

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
