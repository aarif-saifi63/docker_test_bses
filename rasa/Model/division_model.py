from sqlalchemy import Column, String
from database import Base, SessionLocal
from datetime import datetime


class Divisions(Base):
    __tablename__ = "division_master"

    id = Column(String, primary_key=True)
    division_code = Column(String, nullable=False)
    division_name = Column(String, default="new")
   

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        try:
            db = SessionLocal()
            return db.query(Divisions).filter_by(**kwargs).first()
        finally:
            db.close()

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(Divisions).filter_by(**filter_query).first()
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

    