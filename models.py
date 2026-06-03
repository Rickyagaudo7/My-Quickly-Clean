from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime

# ==============================
# USER MODEL
# ==============================
class User(UserMixin, db.Model):
    __tablename__ = 'users'  # IMPORTANT: matches your db table

    id = db.Column(db.Integer, primary_key=True)

    # UNIQUE LOGIN FIELDS (prevents duplicates)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='customer')

    # Optional geo support (safe for future upgrade)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    zip_code = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ==============================
# REQUEST MODEL (CLEANING JOBS)
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

    price = db.Column(db.Float, nullable=False, default=0.0)

    # UPDATED STATUS PIPELINE (safe expansion)
    status = db.Column(
        db.String(30),
        default='searching'  # replaces simple pending system
    )

    # Cleaner assignment (future Uber-style flow)
    cleaner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Geo matching support (optional but future-ready)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer = db.relationship('User', foreign_keys=[customer_id], backref='requests')
    cleaner = db.relationship('User', foreign_keys=[cleaner_id], backref='assigned_jobs')


# ==============================
# NOTIFICATIONS
# ==============================
class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    message = db.Column(db.String(255), nullable=False)

status = db.Column(db.String(20), default='unread')

created_at = db.Column(db.DateTime, default=datetime.utcnow)

user = db.relationship('User', backref='notifications')