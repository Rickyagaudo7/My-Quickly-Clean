from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from dotenv import load_dotenv
import os
import logging

# ==============================
# Load Environment Variables
# ==============================
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# ==============================
# App Configuration
# ==============================
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///your_database.db')  # Default to SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# ==============================
# Logging Setup
# ==============================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==============================
# Models
# ==============================

class User(db.Model):
    """User model representing registered users."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='customer', nullable=False)  # Roles: 'customer', 'employee', 'admin'
    verified = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now(), nullable=False)

    def __repr__(self):
        return f"<User {self.username}, Role: {self.role}, Verified: {self.verified}>"

class Request(db.Model):
    """Request model representing cleaning service requests."""
    __tablename__ = 'requests'
    id = db.Column(db.Integer, primary_key=True)
    service_type = db.Column(db.String(100), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # Status: 'pending', 'approved', 'denied'
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    total_cost = db.Column(db.Float, nullable=False, default=0.0)  # Total order cost
    milestone_paid = db.Column(db.Boolean, default=False)  # Whether 50% milestone payment is done
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    # Relationships
    customer = db.relationship('User', backref='customer_requests')

    def __repr__(self):
        return f"<Request {self.id}, Service: {self.service_type}, Status: {self.status}, Milestone Paid: {self.milestone_paid}>"

class CleaningService(db.Model):
    """CleaningService model representing available cleaning options."""
    __tablename__ = 'cleaning_services'
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)  # e.g. "Regular Cleaning Services"
    name = db.Column(db.String(100), nullable=False)      # e.g. "General House Cleaning - Quick Clean"
    price = db.Column(db.Float, nullable=False)           # e.g. 80.0
    price_type = db.Column(db.String(50), nullable=True) # e.g. "Quick Clean", "Deep Clean", "per hour", "from per hour", "starting at"
    image = db.Column(db.String(255), nullable=True)      # Optional image filename

    def __repr__(self):
        return f"<CleaningService {self.category} - {self.name} (${self.price} {self.price_type or ''})>"

# ==============================
# Database Initialization and Seeding
# ==============================
def initialize_database():
    """Creates the database and tables if they don't exist and seeds cleaning services."""
    with app.app_context():
        db.create_all()
        
        if CleaningService.query.count() == 0:
            # Seed detailed cleaning services and prices
            services = [
                # 1. Regular Cleaning Services
                CleaningService(category="Regular Cleaning Services", name="General House Cleaning - Quick Clean", price=80.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="General House Cleaning - Deep Clean", price=150.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Vacuuming Carpets & Rugs - Quick Clean", price=40.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Vacuuming Carpets & Rugs - Deep Clean", price=70.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Floor Mopping and Sweeping - Quick Clean", price=30.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Floor Mopping and Sweeping - Deep Clean", price=60.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Dusting & Polishing Furniture - Quick Clean", price=35.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Dusting & Polishing Furniture - Deep Clean", price=65.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Bed Making and Linen Change - Quick Clean", price=20.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Bed Making and Linen Change - Deep Clean", price=40.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Trash Removal and Recycling - Quick Clean", price=15.0, price_type=None),
                CleaningService(category="Regular Cleaning Services", name="Trash Removal and Recycling - Deep Clean", price=30.0, price_type=None),

                # 2. Deep Cleaning & Specialized Cleaning
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Deep Cleaning (kitchen, bathrooms, floors) - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Deep Cleaning (kitchen, bathrooms, floors) - Deep Clean", price=300.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Bathroom Sanitizing (toilets, showers, sinks) - Quick Clean", price=50.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Bathroom Sanitizing (toilets, showers, sinks) - Deep Clean", price=90.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Kitchen Cleaning (appliances, counters, cabinets) - Quick Clean", price=70.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Kitchen Cleaning (appliances, counters, cabinets) - Deep Clean", price=130.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Carpet and Upholstery Steam Cleaning - Quick Clean", price=80.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Carpet and Upholstery Steam Cleaning - Deep Clean", price=150.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Refrigerator and Oven Cleaning (inside/outside) - Quick Clean", price=50.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Refrigerator and Oven Cleaning (inside/outside) - Deep Clean", price=100.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Window Cleaning (interior & exterior) - Quick Clean", price=60.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Window Cleaning (interior & exterior) - Deep Clean", price=110.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Cleaning Air Vents and Filters - Quick Clean", price=40.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Cleaning Air Vents and Filters - Deep Clean", price=80.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Wall and Baseboard Cleaning - Quick Clean", price=40.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Wall and Baseboard Cleaning - Deep Clean", price=80.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Curtain and Blind Dusting - Quick Clean", price=35.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Curtain and Blind Dusting - Deep Clean", price=70.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Ceiling Fan and Light Fixture Cleaning - Quick Clean", price=30.0, price_type=None),
                CleaningService(category="Deep Cleaning & Specialized Cleaning", name="Ceiling Fan and Light Fixture Cleaning - Deep Clean", price=60.0, price_type=None),

                # 3. Laundry & Linen Services
                CleaningService(category="Laundry & Linen Services", name="Laundry and Ironing - Quick Clean", price=50.0, price_type=None),
                CleaningService(category="Laundry & Linen Services", name="Laundry and Ironing - Deep Clean", price=90.0, price_type=None),
                CleaningService(category="Laundry & Linen Services", name="Bed Making and Linen Change - Quick Clean", price=20.0, price_type=None),
                CleaningService(category="Laundry & Linen Services", name="Bed Making and Linen Change - Deep Clean", price=40.0, price_type=None),

                # 4. Move-In / Move-Out & Event Cleaning
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Move-in / Move-out Cleaning - Quick Clean", price=200.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Move-in / Move-out Cleaning - Deep Clean", price=400.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Post-party Cleaning - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Post-party Cleaning - Deep Clean", price=300.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Cleaning for Special Events (weddings, corporate) - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Cleaning for Special Events (weddings, corporate) - Deep Clean", price=350.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Holiday / Seasonal Cleaning - Quick Clean", price=120.0, price_type=None),
                CleaningService(category="Move-In / Move-Out & Event Cleaning", name="Holiday / Seasonal Cleaning - Deep Clean", price=250.0, price_type=None),

                # 5. Organization & Decluttering
                CleaningService(category="Organization & Decluttering", name="Organizing and Decluttering", price=60.0, price_type="per hour"),
                CleaningService(category="Organization & Decluttering", name="Garage Cleaning and Organization", price=80.0, price_type="per hour"),
                CleaningService(category="Organization & Decluttering", name="Pet Area Cleaning", price=50.0, price_type=None),

                # 6. Eco-Friendly & Sanitization Services
                CleaningService(category="Eco-Friendly & Sanitization Services", name="Green / Eco-Friendly Cleaning Options", price=10.0, price_type="percent surcharge (+10%)"),
                CleaningService(category="Eco-Friendly & Sanitization Services", name="Sanitization & Disinfection Services - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Eco-Friendly & Sanitization Services", name="Sanitization & Disinfection Services - Deep Clean", price=200.0, price_type=None),

                # 7. Handyman & Home Repairs - Plumbing & Water Systems
                CleaningService(category="Handyman & Home Repairs - Plumbing & Water Systems", name="Plumbing Repairs", price=75.0, price_type="per hour (starting from)"),
                CleaningService(category="Handyman & Home Repairs - Plumbing & Water Systems", name="Water Heater Repair/Replacement - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Plumbing & Water Systems", name="Water Heater Repair/Replacement - Deep Clean", price=350.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Plumbing & Water Systems", name="Drain Cleaning and Septic Service - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Plumbing & Water Systems", name="Drain Cleaning and Septic Service - Deep Clean", price=250.0, price_type=None),

                # Electrical & HVAC
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Electrical Repairs", price=80.0, price_type="per hour (starting from)"),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="HVAC Maintenance/Repairs - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="HVAC Maintenance/Repairs - Deep Clean", price=250.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Smart Home Device Installation - Quick Clean", price=75.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Smart Home Device Installation - Deep Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Home Automation Setup - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Home Automation Setup - Deep Clean", price=300.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Home Security System Installation - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Electrical & HVAC", name="Home Security System Installation - Deep Clean", price=350.0, price_type=None),

                # Appliance & Furniture
                CleaningService(category="Handyman & Home Repairs - Appliance & Furniture", name="Appliance Repair - Quick Clean", price=80.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Appliance & Furniture", name="Appliance Repair - Deep Clean", price=200.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Appliance & Furniture", name="Furniture Assembly and Repair - Quick Clean", price=50.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Appliance & Furniture", name="Furniture Assembly and Repair - Deep Clean", price=120.0, price_type=None),

                # Carpentry & Painting
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Carpentry", price=80.0, price_type="per hour (starting from)"),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Painting and Wall Patching - Quick Clean", price=60.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Painting and Wall Patching - Deep Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Drywall Installation and Repair - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Drywall Installation and Repair - Deep Clean", price=250.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Installation of Shelves, Curtain Rods, and Blinds - Quick Clean", price=50.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Installation of Shelves, Curtain Rods, and Blinds - Deep Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Fence Painting or Staining - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Carpentry & Painting", name="Fence Painting or Staining - Deep Clean", price=200.0, price_type=None),

                # Outdoor & Garden Maintenance
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Lawn and Garden Maintenance", price=50.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Lawn and Garden Maintenance - Deep Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Pressure Washing - Quick Clean", price=120.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Pressure Washing - Deep Clean", price=250.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Gutter Cleaning and Repair - Quick Clean", price=80.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Gutter Cleaning and Repair - Deep Clean", price=160.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Roof Repairs - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Roof Repairs - Deep Clean", price=350.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Fence Installation and Repair - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Fence Installation and Repair - Deep Clean", price=400.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Deck and Patio Maintenance - Quick Clean", price=120.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Deck and Patio Maintenance - Deep Clean", price=300.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Outdoor & Garden Maintenance", name="Concrete and Masonry Work", price=150.0, price_type="per job (starting from)"),

                # Flooring Services
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Flooring Installation and Repairs - Quick Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Flooring Installation and Repairs - Deep Clean", price=400.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Tile Grout Cleaning and Repair - Quick Clean", price=80.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Tile Grout Cleaning and Repair - Deep Clean", price=180.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Carpet and Floor Repairs - Quick Clean", price=70.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Carpet and Floor Repairs - Deep Clean", price=150.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Waterproofing and Sealing Services - Quick Clean", price=100.0, price_type=None),
                CleaningService(category="Handyman & Home Repairs - Flooring Services", name="Waterproofing and Sealing Services - Deep Clean", price=250.0, price_type=None),

                # Moving & Heavy Lifting
                CleaningService(category="Handyman & Home Repairs - Moving & Heavy Lifting", name="Moving Heavy Items and Furniture", price=50.0, price_type="per hour"),
                CleaningService(category="Handyman & Home Repairs - Moving & Heavy Lifting", name="Junk Removal and Hauling", price=75.0, price_type="per load"),

                # Emergency & Specialized Repairs
                CleaningService(category="Handyman & Home Repairs - Emergency & Specialized Repairs", name="Emergency Repair Services (24/7)", price=25.0, price_type="percent surcharge (+25%)"),
                CleaningService(category="Handyman & Home Repairs - Emergency & Specialized Repairs", name="Energy Efficiency Upgrades", price=100.0, price_type="starting at"),

            ]
            db.session.bulk_save_objects(services)
            db.session.commit()
            logger.info("Initial cleaning services added.")
        else:
            logger.info("Cleaning services already present.")

if __name__ == '__main__':
    initialize_database()
    logger.info("Database initialization script completed.")
