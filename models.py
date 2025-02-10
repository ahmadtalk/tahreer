from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    sessions = db.relationship('ProofreadSession', backref='user', lazy=True)

class ProofreadSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    input_text = db.Column(db.Text, nullable=False)
    result_text = db.Column(db.Text, nullable=False)
    corrections = db.Column(db.Text)  # يمكن استخدام JSON هنا لاحقًا
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
