from sqlalchemy import Column, String, Integer, DateTime
from werkzeug.security import generate_password_hash
from database import Base, SessionLocal
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email_id = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=True)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def __init__(self, email_id="", role="admin", password=""):
        self.email_id = email_id
        self.password = generate_password_hash(password) if password else None
        self.role = role

    def save(self):
        db = SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
            return self.id

        finally:
            db.close()
    @staticmethod
    def find(**kwargs):
        db = SessionLocal()
        try:
            return db.query(Admin).filter_by(**kwargs).all()

        finally:
            db.close()
    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        try:
            return db.query(Admin).filter_by(**kwargs).first()

        finally:
            db.close()
    @staticmethod
    def update(user_id, update_values):
        db = SessionLocal()
        try:
            user = db.query(Admin).filter_by(id=user_id).first()
            if user:
                for key, value in update_values.items():
                    setattr(user, key, value)
                user.updated_at = current_time_ist()
                db.commit()
                return True
            return False

        finally:
            db.close()
    @staticmethod
    def find_by_email(email_id):
        db = SessionLocal()
        try:
            return db.query(Admin).filter_by(email_id=email_id).first()

        finally:
            db.close()
    @staticmethod
    def find_by_user_id(user_id):
        db = SessionLocal()
        try:
            return db.query(Admin).filter_by(id=user_id).first()

        finally:
            db.close()
    @staticmethod
    def delete(user_id):
        db = SessionLocal()
        try:
            user = db.query(Admin).filter_by(id=user_id).first()
            if user:
                db.delete(user)
                db.commit()
                return True
            return False

        finally:
            db.close()