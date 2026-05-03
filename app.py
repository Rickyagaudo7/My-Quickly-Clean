from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from flask_login import (
    LoginManager, login_user, logout_user,
    login_required, current_user, UserMixin
)
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from dotenv import load_dotenv
from datetime import datetime
from flask import session

import os, logging, stripe, uuid

# ------------------- Init -------------------
load_dotenv()

app = Flask(__name__)
csrf = CSRFProtect(app)

app.secret_key = os.getenv("SECRET_KEY", "devkey")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URI", "sqlite:///your_database.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"

# ------------------- Mail -------------------
app.config.update(
    MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp.office365.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
)

# ------------------- Stripe -------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
app.config["STRIPE_PUBLIC_KEY"] = os.getenv("STRIPE_PUBLIC_KEY")

# ------------------- Extensions -------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ------------------- Logging -------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- Models -------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default="customer")
    verified = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


class Request(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(100), nullable=False)
    photo_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    customer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    customer = db.relationship("User", foreign_keys=[customer_id], backref="requests")
    employee = db.relationship("User", foreign_keys=[employee_id])


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    message = db.Column(db.String(255))
    status = db.Column(db.String(20), default="unread")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", backref="notifications")


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ------------------- Routes -------------------
@app.route("/")
def home():
    return render_template(
        "home.html",
        stripe_public_key=app.config["STRIPE_PUBLIC_KEY"]
    )
@app.route("/chat", methods=["GET", "POST"])
@login_required
def chat():
    if request.method == "POST":
        user_message = request.json.get("message", "").strip()

        # Simple keyword-based response (expand this logic or connect to AI later)
        if "schedule" in user_message.lower():
            approved_reqs = Request.query.filter_by(
                customer_id=current_user.id,
                status="approved"
            ).order_by(Request.date).all()
            if approved_reqs:
                schedule_text = "\n".join(
                    f"- {r.service_type} on {r.date} at {r.time}" for r in approved_reqs
                )
                bot_response = f"Here is your schedule:\n{schedule_text}"
            else:
                bot_response = "You currently have no approved appointments."
        else:
            bot_response = "Thanks for your message! How can I assist you further?"

        # Save chat history in session
        chat_history = session.get("chat_history", [])
        chat_history.append({"user": user_message, "bot": bot_response})
        session["chat_history"] = chat_history

        return jsonify({"response": bot_response})

    # On GET, show chat page with current session history
    chat_history = session.get("chat_history", [])
    return render_template("chat.html", chat_history=chat_history)

# ---------- Auth ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if User.query.filter_by(email=request.form["email"]).first():
            flash("Email already registered.", "danger")
            return redirect(url_for("register"))

        user = User(
            email=request.form["email"],
            username=request.form["username"],
            role=request.form.get("role", "customer")
        )
        user.set_password(request.form["password"])

        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Registered successfully!", "success")
        return redirect(url_for("home"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and user.verify_password(request.form["password"]):
            login_user(user)
            return redirect(
                url_for("employee_dashboard")
                if user.role in ["employee", "admin"]
                else url_for("customer_dashboard")
            )
        flash("Invalid credentials.", "danger")

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out.", "info")
    return redirect(url_for("home"))

# ---------- Dashboards ----------
@app.route("/employee_dashboard")
@login_required
def employee_dashboard():
    if current_user.role not in ["employee", "admin"]:
        return redirect(url_for("home"))

    bookings = Request.query.filter_by(status="pending").all()
    return render_template("employee_dashboard.html", bookings=bookings)


@app.route("/customer_dashboard")
@login_required
def customer_dashboard():
    if current_user.role != "customer":
        return redirect(url_for("home"))

    requests = (
        Request.query
        .filter_by(customer_id=current_user.id)
        .order_by(Request.created_at.desc())
        .all()
    )
    notifications = Notification.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "customer_dashboard.html",
        requests=requests,
        notifications=notifications
    )

# ---------- Notifications ----------
@app.route("/notifications/mark-read", methods=["POST"])
@login_required
def mark_notifications_read():
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    flash("Notifications cleared.", "info")
    return redirect(url_for("customer_dashboard"))

# ---------- Upload ----------
@app.route("/upload-photo", methods=["POST"])
@login_required
def upload_photo():
    file = request.files.get("file")
    if not file or file.filename == "":
        return jsonify(success=False, message="No file")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        return jsonify(success=False, message="Invalid file type")

    filename = f"{uuid.uuid4().hex}{ext}"
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

    return jsonify(success=True, filename=filename)

# ---------- Requests ----------
@app.route("/submit-cleaning-request", methods=["POST"])
@login_required
def submit_cleaning_request():
    data = request.get_json()

    for item in data.get("cart", []):
        db.session.add(Request(
            service_type=item["service"],
            photo_path=item.get("photo", ""),
            description=item.get("description", ""),
            date=item.get("date", "N/A"),
            time=item.get("time", "N/A"),
            customer_id=current_user.id
        ))

    db.session.commit()
    return jsonify(success=True)

# API endpoint to fetch user's requests in JSON
@app.route("/api/my-requests")
@login_required
def api_my_requests():
    user_requests = (
        Request.query.filter_by(customer_id=current_user.id)
        .order_by(Request.created_at.desc())
        .all()
    )
    result = []
    for r in user_requests:
        result.append({
            "id": r.id,
            "service_type": r.service_type,
            "photo_path": r.photo_path,
            "description": r.description,
            "date": r.date,
            "time": r.time,
            "status": r.status
        })
    return jsonify(requests=result)

@app.route("/approve_request/<int:request_id>", methods=["POST"])
@login_required
def approve_request(request_id):
    if current_user.role not in ["employee", "admin"]:
        return redirect(url_for("home"))

    req = Request.query.get_or_404(request_id)
    req.status = "approved"

    db.session.add(Notification(
        user_id=req.customer_id,
        message=f"Request #{req.id} approved."
    ))
    db.session.commit()

    return redirect(url_for("employee_dashboard"))

@app.route("/deny_request/<int:request_id>", methods=["POST"])
@login_required
def deny_request(request_id):
    if current_user.role not in ["employee", "admin"]:
        return redirect(url_for("home"))

    req = Request.query.get_or_404(request_id)
    req.status = "denied"
    db.session.commit()

    return redirect(url_for("employee_dashboard"))

@app.route("/delete_request/<int:request_id>", methods=["POST"])
@login_required
def delete_request(request_id):
    req = Request.query.get_or_404(request_id)
    if req.customer_id != current_user.id:
        return redirect(url_for("customer_dashboard"))

    db.session.delete(req)
    db.session.commit()
    return redirect(url_for("customer_dashboard"))

@app.route("/update-title/<int:request_id>", methods=["POST"])
@login_required
def update_request_title(request_id):
    req = Request.query.get_or_404(request_id)
    if req.customer_id != current_user.id:
        return redirect(url_for("customer_dashboard"))

    req.service_type = request.form.get("new_title", "").strip()
    db.session.commit()
    return redirect(url_for("customer_dashboard"))

@app.route("/reorder_request/<int:request_id>", methods=["POST"])
@login_required
def reorder_request(request_id):
    original = Request.query.get_or_404(request_id)
    if original.customer_id != current_user.id:
        flash("Unauthorized reorder attempt.", "danger")
        return redirect(url_for("customer_dashboard"))

    db.session.add(Request(
        service_type=original.service_type,
        photo_path=original.photo_path,
        description=original.description,
        date=original.date,
        time=original.time,
        customer_id=current_user.id
    ))
    db.session.commit()

    flash("Reorder submitted for review!", "info")
    return redirect(url_for("customer_dashboard"))

# ---------- Stripe Payment Flow ----------

@app.route("/pay-milestone", methods=["POST"])
@login_required
def pay_milestone():
    request_id = request.form.get("request_id")
    if not request_id:
        flash("Request ID missing.", "danger")
        return redirect(url_for("customer_dashboard"))

    cleaning_request = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if not cleaning_request:
        flash("Request not found or unauthorized.", "danger")
        return redirect(url_for("customer_dashboard"))

    # Example fixed amount in cents ($50.00)
    amount = 5000

    # Create PaymentIntent
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency="usd",
        automatic_payment_methods={"enabled": True}
    )

    # Redirect to payment page with request_id and store client_secret in session or query (here query for simplicity)
    return redirect(url_for("payment", request_id=request_id))


@app.route('/payment')
@login_required
def payment():
    request_id = request.args.get('request_id')
    if not request_id:
        return redirect(url_for('home'))

    cleaning_request = Request.query.filter_by(id=request_id, customer_id=current_user.id).first()
    if not cleaning_request:
        return "Request not found or unauthorized", 404

    # Example fixed amount in cents ($50.00)
    amount = 5000

    # Create PaymentIntent
    intent = stripe.PaymentIntent.create(
        amount=amount,
        currency='usd',
        automatic_payment_methods={'enabled': True}
    )

    return render_template(
        'checkout.html',
        cleaning_request=cleaning_request,
        client_secret=intent.client_secret,
        stripe_public_key=app.config['STRIPE_PUBLIC_KEY']
    )

# ------------------- Run -------------------
if __name__ == "__main__":
    app.run(debug=True)
