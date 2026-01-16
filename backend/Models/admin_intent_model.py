# from sqlalchemy import Column, String, Integer, DateTime
# from database import Base, SessionLocal
# from datetime import datetime
# import pytz

# IST = pytz.timezone("Asia/Kolkata")

# def current_time_ist():
#     return datetime.now(IST)

# class Intent(Base):
#     __tablename__ = "intent_v"

#     id = Column(Integer, primary_key=True, autoincrement=True)
#     intent_name = Column(String(255), nullable=False)
#     sub_menu_id = Column(String(255), nullable=True)
#     created_at = Column(DateTime, default=current_time_ist)
#     updated_at = Column(DateTime, default=current_time_ist, onupdate=current_time_ist)

#     def save(self):
#         with SessionLocal() as db:
#             db.add(self)
#             db.commit()
#             db.refresh(self)
#             return self.id

#     @staticmethod
#     def find(search=None, page=1, limit=10):
#         with SessionLocal() as db:
#             query = db.query(Intent)
#             if search:
#                 query = query.filter(Intent.intent_name.ilike(f"%{search}%"))
#             total = query.count()
#             results = query.order_by(Intent.id.desc()).offset((page - 1) * limit).limit(limit).all()
#             return results, total

#     @staticmethod
#     def find_one(**kwargs):
#         with SessionLocal() as db:
#             return db.query(Intent).filter_by(**kwargs).first()

#     @staticmethod
#     def find_by_id(intent_id):
#         with SessionLocal() as db:
#             return db.query(Intent).filter_by(id=intent_id).first()

#     @staticmethod
#     def update(intent_id, update_values):
#         with SessionLocal() as db:
#             intent = db.query(Intent).filter_by(id=intent_id).first()
#             if intent:
#                 for key, value in update_values.items():
#                     setattr(intent, key, value)
#                 intent.updated_at = current_time_ist()
#                 db.commit()
#                 return True
#             return False

#     @staticmethod
#     def delete(intent_id):
#         with SessionLocal() as db:
#             intent = db.query(Intent).filter_by(id=intent_id).first()
#             if intent:
#                 db.delete(intent)
#                 db.commit()
#                 return True
#             return False
