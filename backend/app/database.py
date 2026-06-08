import logging
from datetime import datetime
import uuid
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Date, Numeric, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from backend.app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

# Helper for UUID generation that is database-agnostic (supports SQLite and PostgreSQL)
def generate_uuid():
    return str(uuid.uuid4())

# 1. Vehicles Table
class Vehicle(Base):
    __tablename__ = "vehicles"
    
    vehicle_id = Column(String(36), primary_key=True, default=generate_uuid)
    vin = Column(String(17), unique=True, nullable=False, index=True)
    make = Column(String(50), nullable=False)
    model = Column(String(50), nullable=False)
    year = Column(Integer, nullable=False)
    current_owner = Column(Integer, default=1)
    registered_date = Column(Date, nullable=False)
    registration_city = Column(String(50), nullable=False)
    insurance_company = Column(String(100), nullable=True)
    insurance_policy_number = Column(String(100), nullable=True)
    insurance_expiry_date = Column(Date, nullable=True)
    insurance_claims_count = Column(Integer, default=0)
    insurance_claims_total_amount = Column(Numeric(12, 2), default=0.0)
    insurance_no_claim_bonus = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    vahan_records = relationship("VahanRecord", back_populates="vehicle", cascade="all, delete-orphan")
    ecu_readings = relationship("EcuReading", back_populates="vehicle", cascade="all, delete-orphan")
    wear_images = relationship("WearImage", back_populates="vehicle", cascade="all, delete-orphan")
    fraud_scores = relationship("FraudScore", back_populates="vehicle", cascade="all, delete-orphan")

# 2. VAHAN Records Table (Layer 1)
class VahanRecord(Base):
    __tablename__ = "vaahan_records"
    
    record_id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.vehicle_id"), nullable=False)
    recorded_date = Column(Date, nullable=False)
    odometer_reading = Column(Integer, nullable=False)
    owner_number = Column(Integer, nullable=False)
    api_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="vahan_records")

# 3. ECU Readings Table (Layer 2)
class EcuReading(Base):
    __tablename__ = "ecu_readings"
    
    reading_id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.vehicle_id"), nullable=False)
    ecu_module = Column(String(30), nullable=False)  # ECM, TCM, ABS, AIRBAG, CLUSTER
    mileage = Column(Integer, nullable=False)
    engine_hours = Column(Numeric(10, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="ecu_readings")

# 4. Wear Images Table (Layer 4)
class WearImage(Base):
    __tablename__ = "wear_images"
    
    image_id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.vehicle_id"), nullable=False)
    component = Column(String(30), nullable=False)  # pedal, steering, seat
    image_url = Column(String(255), nullable=False)
    wear_score = Column(Numeric(5, 2), nullable=True)  # Wear score from CNN: 0-10
    wear_level = Column(String(20), nullable=True)   # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="wear_images")

# 5. Fraud Scores Table (Layer 6)
class FraudScore(Base):
    __tablename__ = "fraud_scores"
    
    score_id = Column(String(36), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(36), ForeignKey("vehicles.vehicle_id"), nullable=False)
    vahan_score = Column(Numeric(5, 2), nullable=False)
    ecu_score = Column(Numeric(5, 2), nullable=False)
    xgboost_score = Column(Numeric(5, 2), nullable=False)
    wear_score = Column(Numeric(5, 2), nullable=False)
    combined_score = Column(Numeric(5, 2), nullable=False)
    fraud_probability = Column(Numeric(5, 2), nullable=False)
    risk_level = Column(String(20), nullable=False)      # LOW, MEDIUM, HIGH, CRITICAL
    recommendation = Column(String(100), nullable=False)  # ACCEPT, REVIEW, REJECT
    llm_report = Column(String, nullable=True)
    assessed_at = Column(DateTime, default=datetime.utcnow)
    
    vehicle = relationship("Vehicle", back_populates="fraud_scores")

# Initialize Engine with SQLite fallback capability
try:
    logger.info(f"Connecting to database at {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else settings.DATABASE_URL}")
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    # Test connection
    with engine.connect() as conn:
        logger.info("Successfully connected to PostgreSQL database.")
except Exception as e:
    logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to SQLite for local development/testing.")
    fallback_db_path = "sqlite:///odoshield_fallback.db"
    engine = create_engine(fallback_db_path, connect_args={"check_same_thread": False})
    logger.info(f"Using SQLite fallback database: {fallback_db_path}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    logger.info("Initializing database schema...")
    Base.metadata.create_base_all = Base.metadata.create_all(bind=engine)
    logger.info("Database tables initialized successfully.")
