from datetime import datetime
import uuid
import pytz
from sqlalchemy import Column, String, DateTime, Text
from database import Base, SessionLocal

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class   FeedbackQuestion(Base):
    __tablename__ = "feedback_questions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(String, nullable=False)
    options = Column(Text, nullable=True)  # JSON string (["Very satisfied", "Satisfied", "Not satisfied"])
    question_type = Column(String, nullable=False)
    feedback_acceptance = Column(String, nullable=True)
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
        return db.query(FeedbackQuestion).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(FeedbackQuestion).filter_by(**filter_query).first()
        if session:
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)
            session.updated_at = current_time_ist()
            db.commit()
            db.refresh(session)
            return True