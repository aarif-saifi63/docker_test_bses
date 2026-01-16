from datetime import datetime
import uuid
import pytz
from sqlalchemy import JSON, Column, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from database import Base, SessionLocal
from sqlalchemy import and_


IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)


class Poll(Base):
    __tablename__ = "polls"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)  # e.g., "Customer Satisfaction Poll"
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    questions = Column(JSONB, nullable=False)  # JSON array of questions and options
    division_list = Column(JSONB, nullable=False, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def save(self):
        db = SessionLocal()
        try:
            divisions = self.division_list or []

            # --- Rule 1: Only one default poll can be active ---
            if not divisions:  # default poll
                existing_default = db.query(Poll).filter(
                    Poll.is_active.is_(True),
                    (Poll.division_list == None) | (Poll.division_list == [])
                ).first()
                if existing_default:
                    return {
                        "status": False,
                        "message": f"Default poll '{existing_default.title}' is already active. Please deactivate it first."
                    }

            # --- Rule 2: Division-based poll ---
            else:
                active_polls = db.query(Poll).filter(Poll.is_active.is_(True)).all()
                for existing in active_polls:
                    if existing.division_list:
                        overlap = set(existing.division_list).intersection(divisions)
                        if overlap:
                            return {
                                "status": False,
                                "message": f"Active poll already exists for division(s): {', '.join(overlap)}"
                            }

            db.add(self)
            db.commit()
            db.refresh(self)
            return {"status": True, "poll_id": self.id}

        except Exception as e:
            db.rollback()
            return {"status": "fail", "message": str(e)}
        finally:
            db.close()

    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(Poll).filter_by(**kwargs).first()

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        try:
            session = db.query(Poll).filter_by(**filter_query).first()
            if not session:
                return {"status": "fail", "message": "Poll not found"}

            # Get divisions (old and new)
            new_divisions = update_query.get("division_list", session.division_list or [])

            # If activating poll, apply validation rules
            if update_query.get("is_active") is True:
                # --- Default poll rule ---
                if not new_divisions:
                    existing_default = db.query(Poll).filter(
                        Poll.is_active.is_(True),
                        Poll.id != session.id,
                        (Poll.division_list == None) | (Poll.division_list == [])
                    ).first()
                    if existing_default:
                        return {
                            "status": "fail",
                            "message": f"Default poll '{existing_default.title}' is already active. Please deactivate it first."
                        }

                # --- Division overlap rule ---
                else:
                    active_polls = db.query(Poll).filter(
                        Poll.is_active.is_(True),
                        Poll.id != session.id
                    ).all()
                    for existing in active_polls:
                        if existing.division_list:
                            overlap = set(existing.division_list).intersection(new_divisions)
                            if overlap:
                                return {
                                    "status": "fail",
                                    "message": f"Active poll already exists for division(s): {', '.join(overlap)}"
                                }

            # Update fields dynamically
            for k, v in update_query.items():
                if hasattr(session, k):
                    setattr(session, k, v)

            session.updated_at = current_time_ist()
            db.commit()
            db.refresh(session)

            return {"status": "success", "message": "Poll updated successfully", "poll_id": session.id}

        except Exception as e:
            db.rollback()
            return {"status": "fail", "message": str(e)}
        finally:
            db.close()

        
    @staticmethod
    def get_active_poll(division=None):
        db = SessionLocal()

        print(division, "===================== division in poll model")
        try:
            now = current_time_ist()
            if now.tzinfo:
                now = now.replace(tzinfo=None)

            # Step 1: Try to find an active poll for the division
            division_poll = None
            if division:
                # division_poll = db.query(Poll).filter(
                #     Poll.is_active.is_(True),
                #     Poll.start_time <= now,
                #     Poll.end_time >= now,
                #     Poll.divisions_list.any([division])  # JSON contains division
                # ).first()

                division_poll = db.query(Poll).filter(
                    Poll.is_active.is_(True),
                    Poll.start_time <= now,
                    Poll.end_time >= now,
                    Poll.division_list.contains([division])  # ✅ works for JSON columns
                ).first()

            if division_poll:
                return division_poll

            # # Step 2: Otherwise, return default poll (divisions_list empty)
            default_poll = db.query(Poll).filter(
                Poll.is_active.is_(True),
                Poll.start_time <= now,
                Poll.end_time >= now,
                (Poll.division_list == None) | (Poll.division_list == [])
            ).first()

            # default_poll = db.query(Poll).filter(
            #     Poll.is_active.is_(True),
            #     Poll.start_time <= now,
            #     Poll.end_time >= now,
            #     (Poll.division_list == None | (Poll.division_list == []))
            # ).first()

            return default_poll

        except Exception as e:
            print("Error in get_active_poll:", e)
            return None
        finally:
            db.close()
