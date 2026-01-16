from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from werkzeug.security import generate_password_hash
from database import Base, SessionLocal
from datetime import datetime
import pytz
from cryptography.fernet import Fernet
import os

key=b'y8aIT06DjNY5VtEUvAhIFd5EIG7DruRI14kw3XEYDX0='
cipher = Fernet(key)
IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class UserDetails(Base):
    __tablename__ = "user_details"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=True)
    email_id = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False)
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def __init__(self, email_id, role_id, password=None, name=None):
        self.email_id = email_id
        self.role_id = role_id
        self.password = generate_password_hash(password) if password else None
        self.name = name

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        db.close()
        return self.id
    
    @staticmethod
    def find_one(id):
        db = SessionLocal()
        user = db.query(UserDetails).filter_by(id=id).first()
        db.close()
        return user

    @staticmethod
    def find_by_email(email_id):
        db = SessionLocal()
        user = db.query(UserDetails).filter_by(email_id=email_id).first()
        db.close()
        return user
    
    @staticmethod
    def find_by_email_en(email_id):
        print("Finding user by email:", email_id)
        encrypted_email = cipher.encrypt(email_id.encode())
        if isinstance(encrypted_email, bytes):
            encrypted_email = encrypted_email.decode()
        print("Encrypted email for search:", encrypted_email)
        
        db = SessionLocal()
        user = db.query(UserDetails).filter_by(email_id=encrypted_email).first()
        print("User found:", user)
        db.close()
        return user

    @staticmethod
    def find_all():
        db = SessionLocal()
        users = db.query(UserDetails).all()
        db.close()
        return users
    
    @staticmethod
    def update(user_id, update_values):
        db = SessionLocal()
        user = db.query(UserDetails).filter_by(id=user_id).first()
        if user:
            for key, value in update_values.items():
                setattr(user, key, value)
            user.updated_at = datetime.now(pytz.timezone("Asia/Kolkata"))
            db.commit()
            db.refresh(user)
            return user
        return None
