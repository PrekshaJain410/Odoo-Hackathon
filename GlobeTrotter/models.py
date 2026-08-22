from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(180), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    photo = db.Column(db.String(255))
    language = db.Column(db.String(30), default="English")
    bio = db.Column(db.String(500))
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    trips = db.relationship("Trip", backref="owner", cascade="all, delete-orphan", lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(180), nullable=False)
    description = db.Column(db.Text)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    cover_photo = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=False)
    share_token = db.Column(db.String(80), unique=True, index=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    stops = db.relationship("TripStop", backref="trip", cascade="all, delete-orphan", lazy=True)
    expenses = db.relationship("Expense", backref="trip", cascade="all, delete-orphan", lazy=True)

class City(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    country = db.Column(db.String(120), nullable=False, index=True)
    region = db.Column(db.String(120))
    cost_index = db.Column(db.Float, default=50)
    popularity = db.Column(db.Integer, default=50)
    image_url = db.Column(db.String(500))
    description = db.Column(db.Text)
    activities = db.relationship("Activity", backref="city", cascade="all, delete-orphan", lazy=True)

class TripStop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False, index=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    position = db.Column(db.Integer, default=0)
    city = db.relationship("City")
    activities = db.relationship("TripActivity", backref="stop", cascade="all, delete-orphan", lazy=True)

class Activity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city_id = db.Column(db.Integer, db.ForeignKey("city.id"), nullable=False, index=True)
    name = db.Column(db.String(180), nullable=False)
    category = db.Column(db.String(80))
    description = db.Column(db.Text)
    duration_hours = db.Column(db.Float, default=2)
    estimated_cost = db.Column(db.Float, default=0)
    image_url = db.Column(db.String(500))

class TripActivity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stop_id = db.Column(db.Integer, db.ForeignKey("trip_stop.id"), nullable=False)
    activity_id = db.Column(db.Integer, db.ForeignKey("activity.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(10), default="10:00")
    notes = db.Column(db.Text)
    activity = db.relationship("Activity")

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trip_id = db.Column(db.Integer, db.ForeignKey("trip.id"), nullable=False, index=True)
    category = db.Column(db.String(50), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)