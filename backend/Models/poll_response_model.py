from datetime import datetime
import uuid
import pytz
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey
from database import Base, SessionLocal

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)


class PollResponse(Base):
    __tablename__ = "poll_responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    poll_id = Column(String, nullable=False)  # Reference to poll
    user_id = Column(String, nullable=True)                            # chatbot user identifier
    user_type = Column(String, nullable=True)                           # optional: e.g., "customer", "guest"
    response = Column(JSON, nullable=False)                             # {question_id: selected_option, ...}
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
        return db.query(PollResponse).filter_by(**kwargs).first()

    # --- Update a record ---
    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(PollResponse).filter_by(**filter_query).first()
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
        return db.query(PollResponse).all()
