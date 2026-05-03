from extensions import db  # Ensure db is initialized in extensions.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

# ==============================
# User Model
# ==============================
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='customer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# ==============================
# Cleaning Request Model
# ==============================
class Request(db.Model):
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(100), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    date = db.Column(db.String(20), nullable=True)
    time = db.Column(db.String(20), nullable=True)
    price = db.Column(db.Float, nullable=False, default=0.0)  # ✅ required for cart/checkout
    status = db.Column(db.String(20), default='pending')      # ✅ for tracking approval
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('User', backref='requests')

# ==============================
# Notification Model
# ==============================
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='unread')  # 'unread' or 'read'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')
