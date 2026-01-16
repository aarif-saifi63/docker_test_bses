from sqlalchemy import Boolean, Column, String, Integer, DateTime
from werkzeug.security import generate_password_hash
from database import Base, SessionLocal
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)


class Language(Base):
    __tablename__ = "language_v"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    code = Column(String, nullable=False)
    is_visible = Column(Boolean, default=True)
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find(**kwargs):
        db = SessionLocal()
        return db.query(Language).filter_by(**kwargs).all()

    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(Language).filter_by(**kwargs).first()

    @staticmethod
    def update(language_id, update_values):
        db = SessionLocal()
        language = db.query(Language).filter_by(id=language_id).first()
        if language:
            for key, value in update_values.items():
                if hasattr(language, key):
                    setattr(language, key, value)
            language.updated_at = current_time_ist()
            db.commit()
            return True
        return False

    @staticmethod
    def delete(language_id):
        db = SessionLocal()
        language = db.query(Language).filter_by(id=language_id).first()
        if language:
            db.delete(language)
            db.commit()
            return True
        return False
