import logging
from psycopg2 import IntegrityError
from sqlalchemy import Boolean, Column, String, DateTime, JSON
from database import Base, SessionLocal
from datetime import datetime
import uuid
import pytz
from sqlalchemy.dialects.postgresql import JSONB

IST = pytz.timezone("Asia/Kolkata")

def current_time_ist():
    return datetime.now(IST)

class Advertisement(Base):
    __tablename__ = "ad_content"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ad_name = Column(String, unique=True, nullable=False)
    ad_image_path = Column(String, nullable=True)
    ad_pdf_path = Column(String, nullable=True)
    test = Column(String, nullable=True)
    chatbot_options = Column(JSON, nullable=True)
    divisions_list = Column(JSONB, nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    ad_type = Column(String, nullable=False)
    ad_tracker = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=current_time_ist)
    updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

    def save(self, db=None):
        db = db or SessionLocal()
        try:
            db.add(self)
            db.commit()
            db.refresh(self)
            return self.id
        finally:
            if not db:  
                db.close()

    @staticmethod
    def find_one(db=None, **kwargs):
        db = db or SessionLocal()
        try:
            return db.query(Advertisement).filter_by(**kwargs).first()
        finally:
            if not db:  
                db.close()

    @staticmethod
    def update_one(filter_query, update_query, db=None):
        db = db or SessionLocal()
        try:
            session = db.query(Advertisement).filter_by(**filter_query).first()
            if session:
                for k, v in update_query.items():
                    if hasattr(session, k):
                        setattr(session, k, v)
                session.updated_at = current_time_ist()
                db.commit()
                db.refresh(session)
                return True
            return False
        finally:
            if not db:  
                db.close()

    @staticmethod
    def get_ad_with_options(ad_name, db=None):
        """
        Fetch ad details along with chatbot options.
        """
        db = db or SessionLocal()
        try:
            ad = Advertisement.find_one(db=db, ad_name=ad_name)
            if not ad:
                return None
            return {
                "ad_name": ad.ad_name,
                "ad_image_path": ad.ad_image_path,
                "ad_pdf_path": ad.ad_pdf_path,
                "chatbot_options": ad.chatbot_options or [],
                "created_at": ad.created_at,
                "updated_at": ad.updated_at
            }
        finally:
            if not db:  
                db.close()

    # @staticmethod
    def delete(self, db=None):
        db = db or SessionLocal()
        try:
            logging.debug(f"Deleting Advertisement {self.id} with session {id(db)}")
            db.delete(self)
            db.commit()
        except IntegrityError as e:
            db.rollback()
            logging.error(f"Cannot delete Advertisement {self.id} due to dependencies: {str(e)}")
            raise Exception("Cannot delete advertisement due to related records")
        except Exception as e:
            db.rollback()
            logging.error(f"Error deleting Advertisement {self.id}: {str(e)}", exc_info=True)
            raise
        finally:
            if not db:  # Only close the session if we created it
                logging.debug(f"Closing session {id(db)} in delete")
                db.close()