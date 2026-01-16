from sqlalchemy import Column, String, DateTime, JSON
from database import Base, SessionLocal
from datetime import datetime
import uuid

from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class Session(Base):
    __tablename__ = "session_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=False)
    user_type = Column(String, default="new")
    ca_number = Column(String, nullable=True)
    tel_no = Column(String, nullable=True)
    email = Column(String, nullable=True)
    division_name = Column(String, nullable=True)
    complain_no = Column(String, nullable=True)
    complain_status = Column(String, nullable=True)
    otp = Column(String, nullable=True)
    otp_is_verified = Column(String, nullable=True)
    chat = Column(JSON, nullable=True)  # Store chat history as JSON
    source = Column(String, nullable=True)
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
        return db.query(Session).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(Session).filter_by(**filter_query).first()
        if session:
            if "$push" in update_query:  # emulate Mongo's $push
                if not session.chat:
                    session.chat = []
                # reassign so SQLAlchemy detects the change
                session.chat = session.chat + [update_query["$push"]["chat"]]

            if "$set" in update_query:
                for k, v in update_query["$set"].items():
                    setattr(session, k, v)

            session.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def get_division_by_user_id(user_id: str):
        db = SessionLocal()
        try:
            # Fetch the most recent session entry for this user_id
            session_entry = (
                db.query(Session)
                .filter_by(user_id=user_id)
                .order_by(Session.created_at.desc())  # latest record
                .first()
            )

            if session_entry:
                if session_entry.division_name:
                    return {
                        "status": "success",
                        "division_name": session_entry.division_name
                    }
                else:
                    return {
                        "status": "fail",
                        "message": f"Division not found for user_id {user_id}",
                        "division_name": None
                    }

            return {
                "status": "fail",
                "message": f"No session found for user_id {user_id}",
                "division_name": None
            }

        except Exception as e:
            return {
                "status": "fail",
                "message": str(e),
                "division_name": None
            }
        finally:
            db.close()