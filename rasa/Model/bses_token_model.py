from sqlalchemy import Column, String, DateTime
from database import Base, SessionLocal
from datetime import datetime
import uuid

class BSES_Token(Base):
    __tablename__ = "bses_token"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    bses_jwt_token = Column(String, nullable=True)
    bses_jwt_token_expiry = Column(DateTime, nullable=True)
    bses_delhiv2_token = Column(String, nullable=True)
    bses_delhiv2_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def save(self):
        db = SessionLocal()
        db.add(self)
        db.commit()
        db.refresh(self)
        return self.id

    @staticmethod
    def find_one(**kwargs):
        db = SessionLocal()
        return db.query(BSES_Token).filter_by(**kwargs).first()

    @staticmethod
    def update(filter_query, update_values):
        db = SessionLocal()
        token = db.query(BSES_Token).filter_by(**filter_query).first()
        if token:
            for k, v in update_values.items():
                setattr(token, k, v)
            token.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False

    @staticmethod
    def update_one(filter_query, update_query):
        db = SessionLocal()
        session = db.query(BSES_Token).filter_by(**filter_query).first()
        if session:
            if "$push" in update_query:  # emulate Mongo's $push
                if not session.chat:
                    session.chat = []
                session.chat.append(update_query["$push"]["chat"])
            if "$set" in update_query:
                for k, v in update_query["$set"].items():
                    setattr(session, k, v)
            session.updated_at = datetime.utcnow()
            db.commit()
            return True
        return False