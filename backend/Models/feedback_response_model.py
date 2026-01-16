from datetime import datetime
import uuid
import pytz
from sqlalchemy import Column, String, DateTime, JSON
from database import Base, SessionLocal

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class FeedbackResponse(Base):
    __tablename__ = "feedback_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    user_type = Column(String, nullable=True)  # e.g., "customer", "guest"
    ca_number = Column(String, nullable=True)   # optional
    response = Column(JSON, nullable=False)     # store {question_id: answer, ...}
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    # --- Save the record ---
    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    # --- Find a single record ---
    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(FeedbackResponse).filter_by(**kwargs).first()

    # --- Update a record ---
    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(FeedbackResponse).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            session.updated_at = current_time_ist()
            db.commit()
            db.refresh(session)
            return True
        return False
    # --- Get all records ---
    @staticmethod
    def get_all():
        db = SessionLocal()
        return db.query(FeedbackResponse).all()