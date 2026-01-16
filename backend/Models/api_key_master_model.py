from sqlalchemy import Column, String, DateTime, JSON
from database import Base, SessionLocal
from datetime import datetime
import uuid
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class API_Key_Master(Base):
    __tablename__ = "api_key_master"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    menu_option = Column(String, nullable=True)
    api_url = Column(String, nullable=True)
    api_name = Column(String, nullable=True)
    api_headers = Column(JSON, nullable=True)  
    api_hit = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(API_Key_Master).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(API_Key_Master).filter_by(**filter_query).first()
        if session:
            if "$push" in update_query:  # emulate Mongo's $push
                if not session.api_hit:
                    session.api_hit = []
                session.api_hit = session.api_hit + [update_query["$push"]["api_hit"]]

            if "$set" in update_query:
                for k, v in update_query["$set"].items():
                    setattr(session, k, v)

            session.updated_at = current_time_ist()   # ✅ keep timezone consistent
            db.commit()
            return True
        return False
